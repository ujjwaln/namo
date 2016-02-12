__author__ = 'ujjwal'

import ogr
import osr
from namo_app.helpers.pgdb_helper import PGDbHelper
from namo_app.db.models import Provider, Variable, DataFormat, DataGranule, RasterTile
from namo_app.db.spref import SPREFS
from namo_app import logger


def get_srs(srid):
    for spref in SPREFS:
        if spref.epsg == srid:
            return spref.srs

    srs = osr.SpatialReference()
    srs.ImportFromEPSG(srid)
    return srs


def upsert_datagranule(sqa, config, provider_name, variable_name, format_name, level, extent, srid, start_time, end_time,
                       grib_file_name, overwrite_existing_datagranule=False, name_suffix=None):

    dataformat = sqa.one(DataFormat, filterr={"name": format_name})
    provider = sqa.one(Provider, filterr={"name": provider_name})
    variable = sqa.one(Variable, filterr={"name": variable_name})

    existing_dg = sqa.one(DataGranule, filterr={
                "provider_id": provider.id, "variable_id": variable.id,
                "dataformat_id": dataformat.id, "start_time": start_time,
                "end_time": end_time, "level": level, "extent": extent})

    if existing_dg:
        datagranule = existing_dg
        if overwrite_existing_datagranule:
            raster_format = sqa.one(DataFormat, filterr={"name": "RASTER"})
            vector_format = sqa.one(DataFormat, filterr={"name": "VECTOR"})

            if datagranule.dataformat_id == raster_format.id:
                tiles = sqa.all(RasterTile, filterr={"datagranule_id": datagranule.id})
                for tile in tiles:
                    sqa.delete(tile)
                    logger.info("Deleted existing tile %d" % tile.id)

            if datagranule.dataformat_id == vector_format.id:
                #should probably delete table using ogr
                pgdb_helper = PGDbHelper(conn_str=config.pgsql_conn_str())
                pgdb_helper.execute("drop table if exists %s" % datagranule.table_name)

            logger.info("returning existing datagranule %s" % datagranule.name)

    else:
        granule_name = "%s_%s_%s_%d" % (provider_name, variable_name, start_time.strftime("%Y%m%d %H:%M"), level)
        table_name = "%s_%s_%s_%d" % (provider_name, variable_name, start_time.strftime("%Y%m%d%H%M"), level)
        if name_suffix:
            granule_name = "%s_%s" % (granule_name, name_suffix)
            table_name = "%s_%s" % (table_name, name_suffix)

        datagranule = DataGranule(provider_id=provider.id, variable_id=variable.id, start_time=start_time,
                end_time=end_time, level=level, extent=extent, name=granule_name, srid=srid,
                table_name=table_name, file_name=grib_file_name, dataformat_id=dataformat.id)

        if variable:
            datagranule.variable = variable

        sqa.insert(datagranule)

    return datagranule


def insert_raster(sqa, config, datagranule, ras, srid_in, srid_out, block_size, mask=None):
    raster_format = sqa.one(DataFormat, filterr={"name": "RASTER"})
    vector_format = sqa.one(DataFormat, filterr={"name": "VECTOR"})

    if (srid_in != srid_out) and datagranule.dataformat_id == raster_format.id:
        raise Exception("Cannot reproject raster tiles, ensure srid_in and srid_out are same")

    if datagranule.dataformat_id == raster_format.id:
        tile_count = 0
        mask_wkt = None

        if not mask is None:
            mask_wkt = sqa.AsEWKT(mask.geom, srid_in)

        for tile in ras.tile_generator(block_size=block_size):
            tile_wkt = tile["raster_wkt"]
            extent = tile["extent_wkt"]
            rt = RasterTile(datagranule=datagranule, rast=tile_wkt)
            rt.extent = extent

            if mask_wkt:
                if sqa.Intersects(extent, mask_wkt):
                    sqa.insert(rt)
                    tile_count += 1
            else:
                sqa.insert(rt)
                tile_count += 1

            if tile_count and tile_count % 100 == 0:
                logger.info("Inserted %d tiles" % tile_count)

        logger.info("Inserted %d tiles" % tile_count)
        return tile_count

    elif datagranule.dataformat_id == vector_format.id:
        batch_size = 1000
        ogrds = ogr.Open(config.ogr_connection_string())
        srs_in = get_srs(srid_in)

        if srid_in != srid_out:
            srs_out = get_srs(srid_out)
            transform = osr.CoordinateTransformation(srs_in, srs_out)
            layer = ogrds.CreateLayer(str(datagranule.table_name), srs_out, ogr.wkbPolygon, ['OVERWRITE=YES'])
        else:
            transform = None
            layer = ogrds.CreateLayer(str(datagranule.table_name), srs_in, ogr.wkbPolygon, ['OVERWRITE=YES'])

        logger.info("Created layer %s" % str(datagranule.table_name))
        value_field = ogr.FieldDefn(str(datagranule.variable.name), ogr.OFTReal)
        layer.CreateField(value_field)

        layerDefn = layer.GetLayerDefn()
        layer.StartTransaction()
        count = 0

        #create mask to filter ingest geometries
        mask_geom = None
        if not mask is None:
            mask_wkt = sqa.AsWKT(mask.geom, srid_in)
            mask_geom = ogr.CreateGeometryFromWkt(mask_wkt)

        for items in ras.vector_generator(block_size=block_size):
            for item in items:
                poly, value = item[0], item[1]
                if not mask_geom is None:
                    if not mask_geom.Intersects(poly):
                        continue

                feature = ogr.Feature(layerDefn)
                if transform:
                    try:
                        poly.Transform(transform)
                        feature.SetGeometry(poly)
                    except:
                        logger.error("Reprojection failed")
                else:
                    feature.SetGeometry(poly)

                feature.SetField(str(datagranule.variable.name), value)
                layer.CreateFeature(feature)
                count += 1

                if count % batch_size == 0:
                    logger.info("inserted features - %d" % count)
                    layer.CommitTransaction()

        if count % batch_size != 0:
            logger.info("inserted features - %d" % count)
            layer.CommitTransaction()

        return count

    else:
        raise Exception("Format should be one of raster or vector")

