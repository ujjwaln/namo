__author__ = 'ujjwal'
import numpy

from namo_app.raster.models.raster_base import RasterBase
from namo_app.raster.helpers.conversion_helper import gdal2numpy


class ArrayRaster(RasterBase):

    """
        Represents a numpy or array raster.
        Inherits from RasterBase and implements get_data
        also implements set_data_with_xy which creates grid/raster from list of x,y data points
    """

    def __init__(self, data_array, size, ul, scale, skew, srid, gdal_datatype, nodata_value):
        self.data = data_array
        self.dsname = "ARRAY"
        super(ArrayRaster, self).__init__(size, ul, scale, skew, srid, gdal_datatype, nodata_value)

    def get_data(self, xoff, yoff, valid_block_size, block_size):
        pixels = numpy.copy(self.data[xoff: xoff+valid_block_size[0], yoff: yoff+valid_block_size[1]], order='F')

        if block_size[0] > valid_block_size[0] or block_size[1] > valid_block_size[1]:
            buffer = numpy.zeros((block_size[0], block_size[1]), gdal2numpy(self.gdal_datatype))
            buffer.fill(self.nodata_value)
            buffer[0:valid_block_size[0], 0: valid_block_size[1]] = pixels[:, :].transpose()
        else:
            buffer = pixels.transpose()

        return buffer

    def set_data_with_xy(self, x, y, data):
        xbins = [self.ul[0] + j * self.scale[0] for j in range(0, self.size[0]+1)]
        ybins = [self.ul[1] + j * self.scale[1] for j in range(0, self.size[1]+1)]

        n_x = numpy.digitize(x, xbins)
        n_y = numpy.digitize(y, ybins)

        ndt = gdal2numpy(self.gdal_datatype)
        self.data = numpy.zeros((len(xbins), len(ybins)), ndt)
        self.data.fill(self.nodata_value)

        assert len(x) == len(y)
        assert len(x) <= len(data)

        for i in range(0, len(x)):
            bin_num_x = n_x[i] - 1
            bin_num_y = n_y[i] - 1

            if (bin_num_x > 0) and (bin_num_x < self.size[0]) and (bin_num_y > 0) and (bin_num_y < self.size[1]):
                self.data[bin_num_x, bin_num_y] = data[i]
