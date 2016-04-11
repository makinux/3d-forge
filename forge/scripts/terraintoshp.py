# -*- coding: utf-8 -*-

from forge.terrain import TerrainTile
from forge.lib.global_geodetic import GlobalGeodetic

basename = '15_58391_23482'
directory = '.tmp'
extension = '.shp'

# Read terrain file
filePathSource = '%s/%s.terrain' % (directory, basename)
filePathTarget = '%s/%s%s' % (directory, basename, extension)
ter = TerrainTile()

geodetic = GlobalGeodetic(True)
zxy = basename.split('_')
bounds = geodetic.TileBounds(float(zxy[1]), float(zxy[2]), float(zxy[0]))

print bounds
ter.fromFile(filePathSource, bounds[0], bounds[2], bounds[1], bounds[3])
ter.toShapefile(filePathTarget)

# In order to display swiss coordinates
#ter.computeVerticesCoordinates(epsg=4326)
#print ter
