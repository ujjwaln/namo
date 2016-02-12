__author__ = 'ujjwal'
from namo_app.raster.raster_writer import upsert_datagranule, insert_raster
from namo_app.raster.helpers.gdal_file_helper import GdalFileHelper
from namo_app.raster.models.gdal_raster import GDALRaster
from namo_app.utils import get_ingest_files
from namo_app.db.access import SqaAccess
from namo_app.db.models import Mask
from namo_app.ingest import config
from datetime import datetime


settings = {
    "provider": {
        "name": "GTOPO30"
    },
    "srid": {
        "in": 4326,
        "out": 4326
    },
    "data": {
        "sds": None,
        "bands": [{
            "name": "ELEV",
            "number": 1
        }],
        "variables": None
    },
    "metadata_map": {
        "level": "GRIB_SHORT_NAME",
        "start_time": "GRIB_REF_TIME"
    },
    "level": {

    },
    "level_data_source": None,
    "time_metadata_field_names": {
        "start_time": "RANGEBEGINNINGDATE",
        "end_time": "RANGEENDINGDATE",
        "format": "%Y-%m-%d"
    },
    "time_interval_seconds": 3600,
    "format": "RASTER"
}


def ingest(filenames):
    for filename in filenames:
        for band in settings["data"]["bands"]:
            ras = GDALRaster(filename, settings["srid_in"])
            ras.set_band_num(band["number"])
            ras.nodata_value = -9999
            variable_name = band["name"]
            level = 0
            start_time = datetime(year=2010, month=1, day=1)
            end_time = datetime(year=2020, month=1, day=1)
            with SqaAccess(conn_str=config.sqa_connection_string()) as sqa:
                i = 0
                mask = sqa.one(Mask, filterr={"name": "alabama"})
                dg = upsert_datagranule(sqa, config, provider_name=settings["provider_name"],
                    variable_name=variable_name, format_name=settings["format"], level=level,
                    extent=ras.extent_ewkt(), srid=settings["srid_in"], start_time=start_time,
                    end_time=end_time, grib_file_name=filename, overwrite_existing_datagranule=True,
                    name_suffix="ext_%d" % i)

                if dg:
                    block_size = 50, 50
                    insert_raster(sqa, config=config, datagranule=dg, ras=ras, settings=settings,
                          block_size=block_size, mask=mask)

if __name__ == "__main__":
    import glob
    pattern = r"/home/ujjwal/essic/data/gtopo/wcs_al.nc"
    files = glob.glob(pattern)

    ingest(files)