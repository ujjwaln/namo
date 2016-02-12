### namo

namo project consists of namo_api and www folders.
featureserver is not being user now, it is a python implementation for creating WFS services

namo_api has python implementation for ingesting some weather and satellite datasets. in particular, see
1. ingest/gfs.py :Ingests Global Forecast Model weather predictions
2. ingest/gtopo.py: ingests GTOPO30 digital elevation model
3. ingest/modis_ndvi.py: ingests MODIS NDVI data
4. ingest/mrms: ingests nexrad radar reflectivity data

all four ingestors above work by creating ArrayRaster or GDALRaster objects which are then passed along to raster_writer
which writes them to the db. see raster/models/array_raster.py and raster/models/gdal_raster.py, raster/raster_writer.py

the web/service/service.py runs the API endpoint which client application requests data from. service.py is using
the flask_restless package which creates RESTful api given a database.


www folder has a simple angularjs that draws a map and overlays raster datasets (GFS, MODIS etc) as polygons.
uses and angularized version of the OpenLayers library for mapping

