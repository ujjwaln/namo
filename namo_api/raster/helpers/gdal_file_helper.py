__author__ = 'ujjwal'
from osgeo import gdal
from osgeo.gdalconst import GA_ReadOnly
from datetime import datetime, timedelta
import re
from namo_app.utils import check_zip
from namo_app.helpers.nc_file_helper import nc_get_1d_vars_as_list

# Utility methods for GDAL compatible raster datasets

def _parseTime(strTime, fmt="UTC"):
    if fmt == "UTC":
        dtime_utc_str = (strTime.split())[0]
        return datetime.utcfromtimestamp(float(dtime_utc_str))
    else:
        dtime_utc_str = strTime.strip()
        return datetime.strptime(dtime_utc_str, fmt)


def _parseLevel(strLevel):
    try:
        level_str = re.split('-|\[\]', strLevel)[0]
        level = int(level_str)
    except Exception:
        level = 0

    return level


class GdalFileHelper(object):
    def __init__(self, file_name):
        self.file_name = check_zip(file_name)

    def __enter__(self):
        self.ds = gdal.Open(self.file_name, GA_ReadOnly)
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.ds = None

    def find_band_num(self, filterr):
        num_bands = self.ds.RasterCount
        i = 1
        while i <= num_bands:
            band = self.ds.GetRasterBand(i)
            meta = band.GetMetadata()
            keys_found = 0
            for key in filterr:
                if key in meta:
                    if meta[key] == filterr[key]:
                        keys_found += 1

            if keys_found == len(filterr):
                return i

            i += 1

        raise Exception("Could not find band number")

    def get_sds(self, wildcard=None):
        subdatasets = self.ds.GetSubDatasets()
        if wildcard is None:
            return subdatasets[0][0]

        for subdataset in subdatasets:
            if wildcard in subdataset[0] or wildcard in subdataset[1]:
                return subdataset[0]

        raise Exception("Could not find sds")

    def get_metadata(self, band_num=0, vars=[]):
        if band_num:
            band = self.ds.GetRasterBand(band_num)
            meta = band.GetMetadata()
        else:
            meta = self.ds.GetMetadata()
        results = {}
        for varname in vars:
            for item_key in meta:
                if str(item_key).lower() == varname.lower():
                    results[varname] = meta[item_key]

            if not varname in results:
                results[varname] = None
        return results

    def get_description(self, band_num):
        band = self.ds.GetRasterBand(band_num)
        return band.GetDescription()

    def get_band_info(self, meta, band_num):
        _vars = []

        if meta["start_time"] and meta["start_time"]["field_name"]:
            _vars.append(meta["start_time"]["field_name"])
        if meta["end_time"] and meta["end_time"]["field_name"]:
            _vars.append(meta["end_time"]["field_name"])
        if meta["level"] and meta["level"]["field_name"]:
            _vars.append(meta["level"]["field_name"])

        metadata = self.get_metadata(band_num=band_num, vars=_vars)
        if meta["start_time"]["field_name"] and meta["start_time"]["field_name"] in metadata:
            start_time = _parseTime(metadata[meta["start_time"]["field_name"]], meta["start_time"]["format"])
        else:
            start_time = datetime.now()

        if meta["end_time"] and meta["end_time"]["field_name"] and meta["end_time"]["field_name"] in metadata:
            end_time = _parseTime(metadata[meta["end_time"]["field_name"]], meta["end_time"]["format"])
        else:
            end_time = None

        if meta["level"] and meta["level"]["field_name"] and meta["level"]["field_name"] in metadata:
            ldata = metadata[meta["level"]["field_name"]]
            level = _parseLevel(ldata)
        else:
            level = 0

        return {
            "level": level,
            "end_time": end_time,
            "start_time": start_time
        }

    def get_nc_vars(self, var_names):
        vars = nc_get_1d_vars_as_list(self.file_name, var_names)
        return vars