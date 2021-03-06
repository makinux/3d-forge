# -*- coding: utf-8 -*-

import os
from forge.terrain import TerrainTile
from forge.terrain.topology import TerrainTopology
from forge.lib.shapefile_utils import ShpToGDALFeatures
from forge.lib.global_geodetic import GlobalGeodetic


basename = '228_91_10'
directory = '.tmp'
extension = '.terrain'

curDir = os.getcwd()
filePathSource = '%s/forge/data/dem/%s.shp' % (curDir, basename)
filePathTarget = '%s/%s%s' % (directory, basename, extension)

shapefile = ShpToGDALFeatures(shpFilePath=filePathSource)
features = shapefile.__read__()

terrainTopo = TerrainTopology(features=features)
terrainTopo.fromGDALFeatures("DN")
terrainFormat = TerrainTile()

geodetic = GlobalGeodetic(True)
zxy = basename.split('_')
bounds = geodetic.TileBounds(float(zxy[1]), float(zxy[2]), float(zxy[0]))

terrainFormat.fromTerrainTopology(terrainTopo, bounds)
terrainFormat.toFile(filePathTarget)

# Display SwissCoordinates
terrainFormat.computeVerticesCoordinates(epsg=21781)
print terrainFormat
