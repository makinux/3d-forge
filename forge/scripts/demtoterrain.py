# -*- coding: utf-8 -*-

import os
from forge.terrain import TerrainTile
from forge.terrain.topology import TerrainTopology
from forge.lib.demfile_utils import DemToGDALFeatures
from forge.lib.global_geodetic import GlobalGeodetic

basename = '15_58391_23482'
directory = '.tmp'
extension = '.terrain'

curDir = os.getcwd()
filePathSource = '%s/forge/data/dem/%s.tif' % (curDir, basename)
filePathTarget = '%s/%s%s' % (directory, basename, extension)

demfile = DemToGDALFeatures(demFilePath=filePathSource)
points = demfile.__read__()

terrainTopo = TerrainTopology(points=points)
terrainTopo.fromGDALPoints()
terrainFormat = TerrainTile()

geodetic = GlobalGeodetic(True)
zxy = basename.split('_')
bounds = geodetic.TileBounds(float(zxy[1]), float(zxy[2]), float(zxy[0]))

terrainFormat.fromTerrainTopology(terrainTopo)
#print terrainFormat
#raise Exception
terrainFormat.toFile(filePathTarget)

# Display SwissCoordinates
#terrainFormat.computeVerticesCoordinates(epsg=4326)
#print terrainFormat
