from sqlalchemy import Column, Integer, String, DateTime, Float, ForeignKey, UniqueConstraint, Index, \
    MetaData, Table, create_engine
from geoalchemy2 import Geometry, Raster
from sqlalchemy.orm import relationship, mapper, clear_mappers


class DataFormat(object):
    def __init__(self, name):
        self.name = name


class Variable(object):
    def __init__(self, name, unit, description):
        self.name = name
        self.unit = unit
        self.description = description


class Provider(object):
    def __init__(self, name):
        self.name = name


class DataGranule(object):
    def __init__(self, provider_id, variable_id, start_time, end_time, level, extent, name, srid, table_name, file_name,
                 dataformat_id):
        self.provider_id = provider_id
        self.provider = None

        self.variable_id = variable_id
        self.variable = None

        self.start_time = start_time
        self.end_time = end_time
        self.level = level
        self.extent = extent
        self.name = name
        self.srid = srid
        self.table_name = table_name
        self.file_name = file_name

        self.dataformat_id = dataformat_id
        self.dataformat = None

        self.raster_band_num = -1 #not mapped, useful internally
        self.exists_in_db = False


class RasterTile(object):
    def __init__(self, rast, datagranule):
        self.rast = rast
        self.datagranule_id = None
        self.datagranule = datagranule
        self.extent = None


class Mask(object):
    def __init__(self, name, geom):
        self.name = name
        self.geom = geom


metadata = MetaData()

dataformat = Table('dataformat', metadata,
                   Column('id', Integer, primary_key=True),
                   Column('name', String(256), nullable=False))
mapper(DataFormat, dataformat)

variable = Table('variable', metadata,
                 Column('id', Integer, primary_key=True),
                 Column('name', String(256), nullable=False),
                 Column('unit', String(256), nullable=True),
                 Column('description', String(256), nullable=True))
mapper(Variable, variable)

provider = Table('provider', metadata,
                 Column('id', Integer, primary_key=True),
                 Column('name', String(256), nullable=False))
mapper(Provider, provider)

datagranule = Table('datagranule', metadata,
    Column('id', Integer, primary_key=True),
    Column('start_time', DateTime, nullable=False),
    Column('end_time', DateTime, nullable=False),
    Column('level', Float, nullable=False),
    Column('extent', Geometry, nullable=True),
    Column('name', String, nullable=False),
    Column('srid', Integer, nullable=False),
    Column('table_name', String, nullable=False),
    Column('file_name', String, nullable=False),
    Column('variable_id', Integer, ForeignKey('variable.id'), nullable=False),
    Column('provider_id', Integer, ForeignKey('provider.id'), nullable=False),
    Column('dataformat_id', Integer, ForeignKey('dataformat.id'), nullable=False),
    UniqueConstraint('start_time', 'end_time', 'level', 'variable_id', 'provider_id',
                     'level', 'extent', 'dataformat_id', name='datagranule_unique_idx'))

mapper(DataGranule, datagranule, properties={'variable': relationship(Variable),
                                             'provider': relationship(Provider),
                                             'dataformat': relationship(DataFormat)})

rastertile = Table('rastertile', metadata,
                   Column('id', Integer, primary_key=True),
                   Column('rast', Raster, nullable=True),
                   Column('datagranule_id', Integer, ForeignKey('datagranule.id'), nullable=False))

mapper(RasterTile, rastertile, properties={'datagranule': relationship(DataGranule)})


mask = Table('mask', metadata,
             Column('name', String, nullable=False, primary_key=True),
             Column('geom', Geometry(geometry_type="GEOMETRY", srid=4326), nullable=False))

mapper(Mask, mask)


def init_mapper(sqa_conn_str):
    engine = create_engine(sqa_conn_str)
    metadata.create_all(engine)