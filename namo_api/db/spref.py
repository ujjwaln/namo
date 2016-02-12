__author__ = 'ujjwal'

import osr
SRID_WGS84 = 4326
SRID_MODIS = 96842
SRID_RAP = 750914
SRID_ALBERS = 750915
SRID_HRAP = 750916
SRID_GFS = 750917
SRID_LIS = 750918


class SpatialReference(object):
    def __init__(self, esri_sr_text, force_epsg=-1):
        srs = osr.SpatialReference()
        srs.ImportFromESRI([esri_sr_text])

        self.wkt = srs.ExportToWkt()
        self.proj4 = srs.ExportToProj4()

        srs.AutoIdentifyEPSG()
        self.epsg = srs.GetAuthorityCode(None)
        if self.epsg is None:
            self.epsg = force_epsg

        auth_name = 'sr-org'
        auth_srid = 6842
        self.sql_insert_statement = """
            INSERT into spatial_ref_sys(srid, auth_name, auth_srid, proj4text, srtext)
            values (%d, '%s', %d, '%s', '%s');
        """ % (self.epsg, auth_name, auth_srid, self.proj4, self.wkt)

        self.srs = srs

__sr_text_modis_sinusoidal = \
        'PROJCS["Sinusoidal",'+\
            'GEOGCS["GCS_Undefined",'+\
                'DATUM["Undefined",SPHEROID["User_Defined_Spheroid",6371007.181,0.0]],'+\
                'PRIMEM["Greenwich",0.0],'+\
                'UNIT["Degree",0.0174532925199433]'+\
            '],'+\
            'PROJECTION["Sinusoidal"],'+\
            'PARAMETER["False_Easting",0.0],'+\
            'PARAMETER["False_Northing",0.0],'+\
            'PARAMETER["Central_Meridian",0.0],'+\
            'UNIT["Meter",1.0]'+\
        ']'

__sr_text_rap_grid =\
    'PROJCS["unnamed",'+\
        'GEOGCS["Coordinate System imported from GRIB file",'+\
            'DATUM["unknown", SPHEROID["Sphere",6371229,0]],'+\
            'PRIMEM["Greenwich",0],'+\
            'UNIT["degree",0.0174532925199433]'+\
        '],'+\
        'PROJECTION["Lambert_Conformal_Conic_2SP"],'+\
        'PARAMETER["standard_parallel_1",25],'+\
        'PARAMETER["standard_parallel_2",25],'+\
        'PARAMETER["latitude_of_origin",25],'+\
        'PARAMETER["central_meridian",265],'+\
        'PARAMETER["false_easting",0],'+\
        'PARAMETER["false_northing",0]'+\
    ']'

__sr_text_albers = \
    'PROJCS["NAD_1983_Albers",'+\
    'GEOGCS["NAD83",'+\
        'DATUM["North_American_Datum_1983",'+\
            'SPHEROID["GRS 1980",6378137,298.257222101,'+\
                'AUTHORITY["EPSG","7019"]],'+\
            'TOWGS84[0,0,0,0,0,0,0],'+\
            'AUTHORITY["EPSG","6269"]],'+\
        'PRIMEM["Greenwich",0,'+\
            'AUTHORITY["EPSG","8901"]],'+\
        'UNIT["degree",0.0174532925199433,'+\
            'AUTHORITY["EPSG","9108"]],'+\
        'AUTHORITY["EPSG","4269"]],'+\
    'PROJECTION["Albers_Conic_Equal_Area"],'+\
    'PARAMETER["standard_parallel_1",29.5],'+\
    'PARAMETER["standard_parallel_2",45.5],'+\
    'PARAMETER["latitude_of_center",23],'+\
    'PARAMETER["longitude_of_center",-96],'+\
    'PARAMETER["false_easting",0],'+\
    'PARAMETER["false_northing",0],'+\
    'UNIT["meters",1]]'

__sr_text_hrap_polar = \
    'PROJCS["User_Defined_Stereographic_North_Pole",'+\
    'GEOGCS["GCS_User_Defined",'+\
        'DATUM["D_User_Defined",'+\
            'SPHEROID["User_Defined_Spheroid",6371200.0,0.0]],'+\
        'PRIMEM["Greenwich",0.0],'+\
        'UNIT["Degree",0.0174532925199433]],'+\
    'PROJECTION["Stereographic_North_Pole"],'+\
    'PARAMETER["False_Easting",0.0],'+\
    'PARAMETER["False_Northing",0.0],'+\
    'PARAMETER["Central_Meridian",-105.0],'+\
    'PARAMETER["Standard_Parallel_1",60.0],'+\
    'UNIT["Meter",1.0]]'

__sr_text_gfs = \
    'GEOGCS["Coordinate System imported from GRIB file",'+\
    'DATUM["unknown",'+\
    '    SPHEROID["Sphere",6371229,0]],'+\
    'PRIMEM["Greenwich",0],'+\
    'UNIT["degree",0.0174532925199433]]'

__sr_text_lis = \
    'GEOGCS["Coordinate System imported from GRIB file",'+\
    'DATUM["unknown",'+\
    '    SPHEROID["Sphere",6371200,0]],'+\
    'PRIMEM["Greenwich",0],'+\
    'UNIT["degree",0.0174532925199433]]'

MODIS_SpatialReference = SpatialReference(__sr_text_modis_sinusoidal, SRID_MODIS)
RAP_Spatial_Reference = SpatialReference(__sr_text_rap_grid, SRID_RAP)
ALBERS_Spatial_Reference = SpatialReference(__sr_text_albers, SRID_ALBERS)
HRAP_Spatial_Reference = SpatialReference(__sr_text_hrap_polar, SRID_HRAP)
GFS_Spatial_Reference = SpatialReference(__sr_text_gfs, SRID_GFS)
LIS_Spatial_Reference = SpatialReference(__sr_text_lis, SRID_LIS)

SPREFS = [
    MODIS_SpatialReference,
    RAP_Spatial_Reference,
    ALBERS_Spatial_Reference,
    HRAP_Spatial_Reference,
    GFS_Spatial_Reference,
    LIS_Spatial_Reference
]


def srs_from_esri_prj(prj_file):
    prj_file = open(prj_file, 'r')
    prj_txt = prj_file.read()

    sr = osr.SpatialReference()
    sr.ImportFromESRI([prj_txt])

    #print sr.ExportToProj4()
    print sr.AutoIdentifyEPSG()
    return sr
