# -*- coding: utf-8 -*-

import re
from osgeo import gdal

class DemToGDALFeatures(object):

    def __init__(self, demFilePath=None):
        if demFilePath is None:
            raise Exception('No demfile path provided')
        if re.search(r'(\.tif)$', demFilePath) is None:
            raise TypeError(
                'Only demfiles are supported. Provided path %s' % demFilePath
            )
        self.demFilePath = demFilePath
        self.drvName = 'GTiff'
        self.ds = gdal.Open(self.demFilePath)
        self.X = self.ds.RasterXSize
        self.Y = self.ds.RasterYSize
        self.drv = gdal.GetDriverByName(self.drvName)

    # Returns a list of GDAL Features
    def __read__(self):
        gt = self.ds.GetGeoTransform()
        band = self.ds.GetRasterBand(1)
        block_sizes = band.GetBlockSize()
        x_block_size = block_sizes[0]
        y_block_size = block_sizes[1]
        bandArray = band.ReadAsArray()
        Origin = (gt[0], gt[3])
        xPitch, yPitch = gt[1], gt[5]
        xsize = band.XSize
        ysize = band.YSize
        data=[]
        vertice=[]
        i=0
        for y in range(ysize):
            for x in range(xsize):
                if y==ysize-1 or x==xsize-1:
                    continue
                minLon = Origin[0] + xPitch * (x)
                maxLon = Origin[0] + xPitch * (x + 1)
                minLat = Origin[1] + yPitch * (y)
                maxLat = Origin[1] + yPitch * (y + 1)
                minminAlt = bandArray[y][x]
                minmaxAlt = bandArray[y+1][x]
                maxminAlt = bandArray[y][x+1]
                maxmaxAlt = bandArray[y+1][x+1]
                #first vertice
                vertice.append([minLon,minLat,minminAlt])
                vertice.append([minLon,maxLat,minmaxAlt])
                vertice.append([maxLon,minLat,maxminAlt])
                data.append(vertice)
                vertice=[]
                #second vertice
                vertice.append([maxLon,minLat,maxminAlt])
                vertice.append([minLon,maxLat,minmaxAlt])
                vertice.append([maxLon,maxLat,maxmaxAlt])
                data.append(vertice)
                vertice=[]
        return data

    # Returns a list of GDAL Features
    def readPoint(self):
        gt = self.ds.GetGeoTransform()
        band = self.ds.GetRasterBand(1)
        block_sizes = band.GetBlockSize()
        x_block_size = block_sizes[0]
        y_block_size = block_sizes[1]
        bandArray = band.ReadAsArray()
        Origin = (gt[0], gt[3])
        xPitch, yPitch = gt[1], gt[5]
        xsize = band.XSize
        ysize = band.YSize
        data=[]
        vertice=[]
        i=0
        for y in range(ysize):
            for x in range(xsize):
                minLon = Origin[0] + xPitch * (x)
                minLat = Origin[1] + yPitch * (y)
                minminAlt = bandArray[y][x]
                #first vertice
                data.append([minLon,minLat,minminAlt])
        return data
    
    def world2Pixel(self, gt, x, y):
        ulX = gt[0]
        ulY = gt[3]
        xDist = gt[1]
        yDist = gt[5]
        rtnX = gt[2]
        rtnY = gt[4]
        pixel = int((x - ulX) / xDist)
        line = int((ulY - y) / xDist)
        return (pixel, line)


    def getFeatures(self):
        dataSource = self._getDatasource()
        layer = dataSource.GetLayer()
        for feature in layer:
            yield feature
