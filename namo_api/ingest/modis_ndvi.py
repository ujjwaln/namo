__author__ = 'ujjwal'
from namo_app.raster.raster_writer import upsert_datagranule, insert_raster
from namo_app.raster.helpers.gdal_file_helper import GdalFileHelper
from namo_app.raster.models.gdal_raster import GDALRaster
from namo_app.utils import get_ingest_files
from namo_app.db.access import SqaAccess
from namo_app.db.models import Mask
from namo_app.ingest import config


settings = {
    "provider": {
        "name": "MODIS"
    },
    "srid": {
        "in": 96842,
        "out": 96842
    },
    "sds": {
        "NDVI": "250m 16 days NDVI",
    },
    "bands": {
        "numbers": None,
        "variables": None,
        "meta": {
            "level": {
                "field_name": "GRIB_SHORT_NAME"
            },
            "start_time": {
                "field_name": "RANGEBEGINNINGDATE",
                "format": "%Y-%m-%d"
            },
            "end_time": {
                "field_name": "RANGEENDINGDATE",
                "format": "%Y-%m-%d"
            }
        },
    },
    "time_interval_seconds": 3600,
    "format": "RASTER"
}


def ingest(filenames):
    for filename in filenames:
        for variable_name in settings["sds"]:
            with GdalFileHelper(filename) as gfh:

                #modis hdf file consists of subdatasets
                dsn = gfh.get_sds(settings["sds"][variable_name])
                band_info = gfh.get_band_info(meta=settings["bands"]["meta"], band_num=0)

                ras = GDALRaster(dsn, settings["srid"]["in"])
                with SqaAccess(conn_str=config.sqa_connection_string()) as sqa:
                    mask = sqa.one(Mask, filterr={"name": "india"})
                    #mask = sqa.one(Mask, filterr={"name": "bareilly"})

                    dg = upsert_datagranule(sqa, config, provider_name=settings["provider"]["name"],
                        variable_name=variable_name, format_name=settings["format"], level=band_info["level"],
                        extent=ras.extent_ewkt(), srid=settings["srid"]["in"], start_time=band_info["start_time"],
                        end_time=band_info["end_time"], grib_file_name=filename, overwrite_existing_datagranule=True)

                    if dg:
                        block_size = 50, 50
                        insert_raster(sqa, config=config, datagranule=dg, ras=ras, srid_in=settings["srid"]["in"],
                                      srid_out=settings["srid"]["out"], block_size=block_size, mask=mask)

if __name__ == "__main__":
    #files = get_ingest_files(r'modis/mod13q1_ndvi/', 'MOD13Q1.*.hdf')
    import glob
    #pattern = r"/home/ujjwal/projects/India_GIS/data/hail/modis/*.hdf"
    pattern = r"/home/ujjwal/projects/India_GIS/data/*.hdf"
    files = glob.glob(pattern)

    ingest(files)
