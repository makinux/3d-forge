# -*- coding: utf-8 -*-

import os
from forge.terrain import TerrainTile
from forge.terrain.topology import TerrainTopology
from forge.lib.demfile_utils import DemToGDALFeatures
from forge.lib.global_geodetic import GlobalGeodetic

basename = '15_58391_23482'
directory = '.tmp'
extension = '.xyz'

curDir = os.getcwd()
filePathSource = '%s/forge/data/dem/%s.tif' % (curDir, basename)
filePathTarget = '%s/%s%s' % (directory, basename, extension)

demfile = DemToGDALFeatures(demFilePath=filePathSource)
points = demfile.readPoint()

with open(filePathTarget, 'w') as f:
    for i in xrange(0, len(points) - 1):
        lon=points[i][0]
        lat=points[i][1]
        alt=points[i][2]
        f.write(lon+","+lat+","+alt+"\n")
    f.close()

# Display SwissCoordinates
#terrainFormat.computeVerticesCoordinates(epsg=4326)
#print terrainFormat
