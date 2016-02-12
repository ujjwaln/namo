__author__ = 'ujjwal'

import numpy
from namo_app.raster.raster_writer import upsert_datagranule, insert_raster
from namo_app.raster.helpers.gdal_file_helper import GdalFileHelper
from namo_app.raster.models.gdal_raster import GDALRaster
from namo_app.utils import get_ingest_files
from namo_app.db.access import SqaAccess
from namo_app.db.models import Mask
from namo_app.ingest import config, get_env
from datetime import datetime, timedelta
from multiprocessing import Pool


settings = {
    "provider": {
        "name": "MRMS"
    },
    "srid": {
        "in": 4326,
        "out": 4326
    },
    "sds": None,
    "bands": {
        "numbers": [{
            "name": "REFL",
            "number": 14
        }],
        "variables": None,
        "meta": {
            "level": None,
            "start_time": {
                "field_name": "NC_GLOBAL#Time",
                "format": "UTC"
            },
            "end_time": None
        }
    },
    "time_interval_seconds": 720,
    "format": "RASTER"
}


def ingest(filename):

    with GdalFileHelper(filename) as gfh:
        #modis hdf file consists of subdatasets
        band_info = gfh.get_band_info(meta=settings["bands"]["meta"], band_num=0)
        nc_vars = gfh.get_nc_vars(["Ht"])
        heights = nc_vars["Ht"]

    for band_num in settings["bands"]["numbers"]:
        ras = GDALRaster(filename, settings["srid"]["in"])
        ras.set_band_num(band_num["number"])
        variable_name = band_num["name"]
        ras.nodata_value = -9999
        level = int(numpy.asscalar(heights[band_num["number"]]))
        start_time = band_info["start_time"]
        end_time = start_time + timedelta(seconds=settings["time_interval_seconds"])

        with SqaAccess(conn_str=config.sqa_connection_string()) as sqa:
            i = 0
            mask = sqa.one(Mask, filterr={"name": "alabama"})
            dg = upsert_datagranule(sqa, config, provider_name=settings["provider"]["name"],
                variable_name=variable_name, format_name=settings["format"], level=level,
                extent=ras.extent_ewkt(), srid=settings["srid"]["in"], start_time=start_time,
                end_time=end_time, grib_file_name=filename, overwrite_existing_datagranule=True,
                name_suffix="ext_%d" % i)

            if dg:
                block_size = 50, 50
                #sqa, config, datagranule, ras, srid_in, srid_out, block_size, mask=None
                insert_raster(sqa, config=config, datagranule=dg, ras=ras, srid_in=settings["srid"]["in"],
                              srid_out=settings["srid"]["out"], block_size=block_size, mask=mask)

if __name__ == "__main__":
    if get_env() == 'production':
        mrms_files1 = get_ingest_files(r"mrms/MREFL", "20140722-*.netcdf.gz")
        mrms_files2 = get_ingest_files(r"mrms/MREFL", "20140723-*.netcdf.gz")
        mrms_files3 = get_ingest_files(r"mrms/MREFL", "20140724-*.netcdf.gz")
        mrms_files = mrms_files1 + mrms_files2 + mrms_files3
    else:
        mrms_files = get_ingest_files(r"mrms", "201407*.netcdf.gz")

    parallel = config.parallel
    if parallel:
        n_proc = config.nprocs
        pool_size = min(n_proc, len(mrms_files))
        p = Pool(pool_size)
        p.map(ingest, mrms_files)
    else:
        for file in mrms_files:
            ingest(file)
