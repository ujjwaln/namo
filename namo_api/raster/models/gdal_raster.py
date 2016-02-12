__author__ = 'ujjwal'
import numpy
from osgeo import gdal
from osgeo.gdalconst import GA_ReadOnly
from namo_app.raster.models.raster_base import RasterBase
from namo_app.raster.helpers.conversion_helper import gdal2numpy
from namo_app.utils import check_zip


class GDALRaster (RasterBase):

    """
        Represents a GDAL readable raster dataset.
        Inherits from RasterBase and implements get_data
    """

    def __init__(self, dataset_name, srid, bottom_up_data=False):
        dataset_name = check_zip(dataset_name)
        ds = gdal.Open(dataset_name, GA_ReadOnly)
        if ds is None:
            raise Exception("Could not open dataset %s" % dataset_name)

        self.dsname = dataset_name
        self.ds = ds
        self.RasterCount = ds.RasterCount

        gt = ds.GetGeoTransform()
        size = (ds.RasterXSize, ds.RasterYSize)
        ul = (gt[0], gt[3])
        scale = (gt[1], gt[5])
        skew = (gt[2], gt[4])
        projection = ds.GetProjectionRef()

        #set band 1 as default
        self.raster_band = self.ds.GetRasterBand(1)
        gdal_datatype = self.raster_band.DataType
        nodata_value = self.raster_band.GetNoDataValue()
        super(GDALRaster, self).__init__(size=size, ul=ul, scale=scale, skew=skew, srid=srid,
                                         gdal_datatype=gdal_datatype, nodata_value=nodata_value,
                                         nodata_range=None, bottom_up=bottom_up_data)

    def set_band_num(self, band_num):
        self.raster_band = self.ds.GetRasterBand(band_num)
        self.gdal_datatype = self.raster_band.DataType
        self.nodata_value = self.raster_band.GetNoDataValue()

    def get_data(self, xoff, yoff, valid_block_size, target_block_size):
        pixels = self.raster_band.ReadAsArray(xoff, yoff, valid_block_size[0],
            valid_block_size[1], target_block_size[0], target_block_size[1])

        data = numpy.zeros((target_block_size[1], target_block_size[0]), gdal2numpy(self.gdal_datatype))
        if target_block_size[0] > valid_block_size[0] or target_block_size[1] > valid_block_size[1]:
            data.fill(self.nodata_value)

        if self.bottom_up:
            for row_num in xrange(0, pixels.shape[0]):
                data[row_num, :] = pixels[pixels.shape[0] - row_num - 1, :]
        else:
            data = pixels

        return data

    def get_attribute(self, attribute_name):
        metadata = self.ds.GetMetadata()
        return metadata.get(attribute_name, None)
