# -*- coding: utf-8 -*-

import os
import datetime
import time
import subprocess
import multiprocessing
import sys
import ConfigParser
import sqlalchemy
import signal
from geoalchemy2 import WKTElement
from sqlalchemy.orm import scoped_session, sessionmaker
from sqlalchemy.exc import ProgrammingError
from sqlalchemy.pool import NullPool
from contextlib import contextmanager
from forge.lib.logs import getLogger
from forge.lib.shapefile_utils import ShpToGDALFeatures
from forge.lib.helpers import BulkInsert, timestamp
from forge.models.tables import Base, models


config = ConfigParser.RawConfigParser()
config.read('database.cfg')
logger = getLogger(config, __name__, suffix='db_%s' % timestamp())


# Create pickable object
class PopulateFeaturesArguments:

    def __init__(self, engineURL, modelIndex, shpFile):
        self.engineURL = engineURL
        self.modelIndex = modelIndex
        self.shpFile = shpFile


def populateFeatures(args):
    pid = os.getpid()
    session = None
    try:
        engine = sqlalchemy.create_engine(args.engineURL)
        session = scoped_session(sessionmaker(bind=engine))
        model = models[args.modelIndex]
        shpFile = args.shpFile

        if not os.path.exists(shpFile):
            logger.error('[%s]: Shapefile %s does not exists' % (pid, shpFile))
            sys.exit(1)

        count = 1
        shp = ShpToGDALFeatures(shpFile)
        logger.info('[%s]: Processing %s' % (pid, shpFile))
        bulk = BulkInsert(model, session, withAutoCommit=1000)
        for feature in shp.getFeatures():
            polygon = feature.GetGeometryRef()
            # TODO Use WKBelement directly instead
            bulk.add(dict(
                the_geom=WKTElement(polygon.ExportToWkt(), 4326)
            ))
            count += 1
        bulk.commit()
        logger.info('[%s]: Commit %s features for %s.' % (pid, count, shpFile))
    except Exception as e:
        logger.error(e)
        raise Exception(e)
    finally:
        if session is not None:
            session.close_all()
            engine.dispose()

    return count


class DB:

    class Server:

        def __init__(self, config):
            self.host = config.get('Server', 'host')
            self.port = config.getint('Server', 'port')

    class Admin:

        def __init__(self, config):
            self.user = config.get('Admin', 'user')
            self.password = config.get('Admin', 'password')

    class Database:

        def __init__(self, config):
            self.name = config.get('Database', 'name')
            self.user = config.get('Database', 'user')
            self.password = config.get('Database', 'password')

    def __init__(self, configFile):
        config = ConfigParser.RawConfigParser()
        config.read(configFile)

        self.serverConf = DB.Server(config)
        self.adminConf = DB.Admin(config)
        self.databaseConf = DB.Database(config)

        self.superEngine = sqlalchemy.create_engine(
            'postgresql+psycopg2://%(user)s:%(password)s@%(host)s:%(port)d/%(database)s' % dict(
                user=self.adminConf.user,
                password=self.adminConf.password,
                host=self.serverConf.host,
                port=self.serverConf.port,
                database='postgres'
            )
        )

        self.adminEngine = sqlalchemy.create_engine(
            'postgresql+psycopg2://%(user)s:%(password)s@%(host)s:%(port)d/%(database)s' % dict(
                user=self.adminConf.user,
                password=self.adminConf.password,
                host=self.serverConf.host,
                port=self.serverConf.port,
                database=self.databaseConf.name
            )
        )
        self.userEngine = sqlalchemy.create_engine(
            'postgresql+psycopg2://%(user)s:%(password)s@%(host)s:%(port)d/%(database)s' % dict(
                user=self.databaseConf.user,
                password=self.databaseConf.password,
                host=self.serverConf.host,
                port=self.serverConf.port,
                database=self.databaseConf.name,
                poolclass=NullPool
            )
        )

    @contextmanager
    def superConnection(self):
        conn = self.superEngine.connect()
        isolation = conn.connection.connection.isolation_level
        conn.connection.connection.set_isolation_level(0)
        yield conn
        conn.connection.connection.set_isolation_level(isolation)
        conn.close()

    @contextmanager
    def adminConnection(self):
        conn = self.adminEngine.connect()
        isolation = conn.connection.connection.isolation_level
        conn.connection.connection.set_isolation_level(0)
        yield conn
        conn.connection.connection.set_isolation_level(isolation)
        conn.close()

    @contextmanager
    def userConnection(self):
        conn = self.userEngine.connect()
        yield conn
        conn.close()

    def createUser(self):
        logger.info('Action: createUser()')
        with self.superConnection() as conn:
            try:
                conn.execute(
                    "CREATE ROLE %(role)s WITH NOSUPERUSER INHERIT LOGIN ENCRYPTED PASSWORD '%(password)s'" % dict(
                        role=self.databaseConf.user,
                        password=self.databaseConf.password
                    )
                )
            except ProgrammingError as e:
                logger.error('Could not create user %(role)s: %(err)s' % dict(
                    role=self.databaseConf.user,
                    err=str(e)
                ))

    def createDatabase(self):
        logger.info('Action: createDatabase()')
        with self.superConnection() as conn:
            try:
                conn.execute(
                    "CREATE DATABASE %(name)s WITH OWNER %(role)s ENCODING 'UTF8' TEMPLATE template_postgis" % dict(
                        name=self.databaseConf.name,
                        role=self.databaseConf.user
                    )
                )
            except ProgrammingError as e:
                logger.error('Could not create database %(name)s with owner %(role)s: %(err)s' % dict(
                    name=self.databaseConf.name,
                    role=self.databaseConf.user,
                    err=str(e)
                ))

        with self.adminConnection() as conn:
            try:
                conn.execute("""
                    ALTER SCHEMA public OWNER TO %(role)s;
                    ALTER TABLE public.spatial_ref_sys OWNER TO %(role)s;
                    ALTER TABLE public.geometry_columns OWNER TO %(role)s
                """ % dict(
                    role=self.databaseConf.user
                )
                )
            except ProgrammingError as e:
                logger.error('Could not create database %(name)s with owner %(role)s: %(err)s' % dict(
                    name=self.databaseConf.name,
                    role=self.databaseConf.user,
                    err=str(e)
                ))

    def setupDatabase(self):
        logger.info('Action: setupDatabase()')
        try:
            Base.metadata.create_all(self.userEngine)
        except ProgrammingError as e:
            logger.warning('Could not setup database on %(name)s: %(err)s' % dict(
                name=self.databaseConf.name,
                err=str(e)
            ))

    def setupFunctions(self):
        logger.info('Action: setupFunctions()')

        os.environ['PGPASSWORD'] = self.databaseConf.password
        baseDir = 'forge/sql/'

        for fileName in os.listdir('forge/sql/'):
            if fileName != 'legacy.sql':
                command = 'psql -U %(user)s -d %(dbname)s -a -f %(baseDir)s%(fileName)s' % dict(
                    user=self.databaseConf.user,
                    dbname=self.databaseConf.name,
                    baseDir=baseDir,
                    fileName=fileName
                )
                try:
                    subprocess.call(command, shell=True)
                except Exception as e:
                    logger.error('Could not add custom functions %s to the database: %(err)s' % dict(
                        fileName=fileName,
                        err=str(e)
                    ))
            else:
                with self.adminConnection() as conn:
                    pgVersion = conn.execute("Select postgis_version();").fetchone()[0]
                    if pgVersion.startswith("2."):
                        logger.info('Action: setupFunctions()->legacy.sql')
                        os.environ['PGPASSWORD'] = self.adminConf.password
                        command = 'psql --quiet -h %(host)s -U %(user)s -d %(dbname)s -f %(baseDir)s%(fileName)s' % dict(
                            host=self.serverConf.host,
                            user=self.adminConf.user,
                            dbname=self.databaseConf.name,
                            baseDir=baseDir,
                            fileName=fileName
                        )
                        try:
                            subprocess.call(command, shell=True)
                        except Exception as e:
                            logger.error('Could not install postgis 2.1 legacy functions to the database: %(err)s' % dict(
                                err=str(e)
                            ))

        del os.environ['PGPASSWORD']

    def populateTables(self):
        logger.info('Action: populateTables()')
        tstart = time.time()
        featuresArgs = []
        for i in range(0, len(models)):
            model = models[i]
            for shp in model.__shapefiles__:
                featuresArgs.append(PopulateFeaturesArguments(
                    self.userEngine.url,
                    i,
                    shp
                ))

        def initWorker():
            signal.signal(signal.SIGINT, signal.SIG_IGN)

        pool = multiprocessing.Pool(multiprocessing.cpu_count(), initWorker)
        async = pool.map_async(populateFeatures, iterable=featuresArgs)

        try:
            while not async.ready():
                time.sleep(3)
        except KeyboardInterrupt:
            logger.info('Keyboard interupt recieved, terminating workers...')
            pool.terminate()
            pool.join()
        except Exception as e:
            logger.error('An error occured while populating the tables with shapefiles: %s' % e)
            logger.error('Terminating workers...')
            pool.terminate()
            pool.join()
            raise Exception(e)
        else:
            logger.info('All jobs have been completed.')
            logger.info('Closing processes...')
            pool.close()
            pool.join()
            tend = time.time()
            logger.info('All tables have been created. It took %s' % str(datetime.timedelta(seconds=tend - tstart)))

    def dropDatabase(self):
        logger.info('Action: dropDatabase()')
        with self.superConnection() as conn:
            try:
                conn.execute(
                    "DROP DATABASE %(name)s" % dict(
                        name=self.databaseConf.name
                    )
                )
            except ProgrammingError as e:
                logger.error('Could not drop database %(name)s: %(err)s' % dict(
                    name=self.databaseConf.name,
                    err=str(e)
                ))

    def dropUser(self):
        logger.info('Action: dropUser()')
        with self.superConnection() as conn:
            try:
                conn.execute(
                    "DROP ROLE %(role)s" % dict(
                        role=self.databaseConf.user
                    )
                )
            except ProgrammingError as e:
                logger.error('Could not drop user %(role)s: %(err)s' % dict(
                    role=self.databaseConf.user,
                    err=str(e)
                ))

    def create(self):
        logger.info('Action: create()')
        self.createUser()
        self.createDatabase()
        self.setupDatabase()
        self.setupFunctions()

    def importshp(self):
        self.populateTables()

    def destroy(self):
        logger.info('Action: destroy()')
        self.dropDatabase()
        self.dropUser()
