__author__ = 'ujjwal'
from namo_app.raster.raster_writer import upsert_datagranule, insert_raster
from namo_app.raster.helpers.gdal_file_helper import GdalFileHelper
from namo_app.raster.models.gdal_raster import GDALRaster
from namo_app.raster.models.array_raster import ArrayRaster
from namo_app.raster.helpers.conversion_helper import numpy2gdal
from namo_app.db.access import SqaAccess
from namo_app.ingest import config
from namo_app.utils import get_ingest_files
from namo_app.db.models import Mask
from datetime import timedelta


settings = {
    "provider": {
        "name": "GFS"
    },
    "srid": {
        "in": 4326,
        "out": 4326
    },
    "sds": None,
    "bands": {
        "numbers": None,
        "variables": {
            "TEMP": {
                "GRIB_ELEMENT": "TMP",
                "GRIB_SHORT_NAME": "0-SFC"
            }
        },
        "meta": {
            "level": {
                "field_name": "GRIB_SHORT_NAME"
            },
            "start_time": {
                "field_name": "GRIB_VALID_TIME",
                "format": "UTC"
            },
            "end_time": None
        },
    },
    "time_interval_seconds": 3600,
    "format": "VECTOR"
}


def ingest_gfs_files():
    filenames = get_ingest_files("GFS", "*.f000")
    for filename in filenames:
        for variable_name in settings["bands"]["variables"]:
            with GdalFileHelper(filename) as gfh:
                band_num = gfh.find_band_num(filterr=settings["bands"]["variables"][variable_name])
                band_info = gfh.get_band_info(meta=settings["bands"]["meta"], band_num=band_num)

            if band_num > 0:
                ras = GDALRaster(filename, settings["srid"]["in"])
                ras.set_band_num(band_num)

                data = ras.get_data(0, 0, ras.size, ras.size)
                gdal_dtype = numpy2gdal(data.dtype.type)

                size_x = ras.size[0] / 2
                size_y = ras.size[1]-1

                data1 = data[0:size_y, 0:size_x]
                array_ras1 = ArrayRaster(data_array=data1, size=(size_x, size_y), ul=(0, 90), scale=ras.scale,
                                         skew=(0, 0), srid=4326, gdal_datatype=gdal_dtype, nodata_value=-999)

                data2 = data[0:size_y, size_x: ras.size[0]]
                array_ras2 = ArrayRaster(data_array=data2, size=(size_x, size_y), ul=(-180, 90), scale=ras.scale,
                                         skew=(0, 0), srid=4326, gdal_datatype=gdal_dtype, nodata_value=-999)

                with SqaAccess(conn_str=config.sqa_connection_string()) as sqa:

                    india_mask = sqa.one(Mask, filterr={"name": "india"})
                    i = 0
                    for arr_ras in [array_ras1, array_ras2]:
                        if not band_info["end_time"]:
                            band_info["end_time"] = band_info["start_time"] + timedelta(seconds=settings["time_interval_seconds"])

                        dg = upsert_datagranule(sqa, config, provider_name=settings["provider"]["name"],
                                                variable_name=variable_name, format_name=settings["format"],
                                                level=band_info["level"], extent=arr_ras.extent_ewkt(),
                                                srid=settings["srid"]["in"], start_time=band_info["start_time"],
                                                end_time=band_info["end_time"], grib_file_name=filename,
                                                overwrite_existing_datagranule=True, name_suffix="ext_%d" % i)
                        i += 1
                        if dg:
                            if settings["format"] == "RASTER":
                                block_size = 30, 30
                            else:
                                block_size = ras.size

                            insert_raster(sqa, config=config, datagranule=dg, ras=arr_ras,
                                          srid_in=settings["srid"]["in"], srid_out=settings["srid"]["out"],
                                          block_size=block_size, mask=india_mask)

if __name__ == "__main__":
    ingest_gfs_files()
