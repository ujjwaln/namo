__author__ = 'ujjwal'

import psycopg2.extensions
from psycopg2 import connect
from psycopg2.extras import DictCursor
from sqlalchemy.orm import sessionmaker
from sqlalchemy import create_engine
from sqlalchemy.orm.exc import NoResultFound, MultipleResultsFound
from namo_app import logger
import sys, traceback


import geoalchemy2 as ga2


class LoggingCursor(psycopg2.extensions.cursor):
    def execute(self, sql, args=None):
        logger.info(self.mogrify(sql, args))
        try:
            psycopg2.extensions.cursor.execute(self, sql, args)
        except Exception, exc:
            logger.error("%s: %s" % (exc.__class__.__name__, exc))
            raise


class PGDbAccess(object):
    conn = None

    def __init__(self, conn_str, echo):
        self.conn_string = conn_str
        self.echo = echo
        if self.conn is None:
            self.conn = connect(conn_str)
            self.conn.autocommit = True

    def __enter__(self):
        if self.echo:
            self.cur = self.conn.cursor(cursor_factory=LoggingCursor)
        else:
            self.cur = self.conn.cursor(cursor_factory=DictCursor)
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.cur.close()
        self.conn.close()


class SqaAccess(object):
    def __init__(self, conn_str):
        self._engine = create_engine(conn_str)
        #Base.metadata.create_all(self._engine)

    def __enter__(self):
        Session = sessionmaker(bind=self._engine)
        self._session = Session()
        return self

    def __exit__(self, exception_type, exception_value, traceback):
        if exception_value:
            logger.error("Errors were encountered, rolling back session")
            self._session.rollback()
        else:
            self._session.commit()

        self._session.close()

        logger.info("Closed db session")

    def all(self, entity_type, filterr):
        return self._session.query(entity_type).filter_by(**filterr).all()

    def one(self, entity_type, filterr):
        query = self._session.query(entity_type).filter_by(**filterr)
        try:
            entity = query.one()
        except NoResultFound:
            logger.warn("No results found for %s %s" % (entity_type, filterr))
            entity = None
        except MultipleResultsFound:
            logger.error("MultipleResultsFound")
            entity = query.first()
        except Exception:
            logger.error(sys.exc_info())
            entity = None
        return entity

    def byId(self, entity_type, id):
        filterr = {"id": id}
        return self._session.query(entity_type).filter_by(**filterr).all()

    def insert(self, entity):
        if isinstance(entity, list):
            self._session.add_all(entity)
        else:
            self._session.add(entity)
        self._session.flush()

    def delete(self, entity):
        self._session.delete(entity)
        self._session.flush()

    def AsEWKT(self, wkbelem, srid):
        return self._session.scalar(ga2.functions.ST_AsEWKT(ga2.functions.ST_Transform(wkbelem, srid)))

    def AsWKT(self, wkbelem, srid):
        return self._session.scalar(ga2.functions.ST_AsText(ga2.functions.ST_Transform(wkbelem, srid)))

    def Project(self, wkbelem, srid):
        return self._session.scalar(ga2.functions.ST_Transform(wkbelem, srid))

    def Intersects(self, geom1, geom2):
        return self._session.scalar(ga2.functions.ST_Intersects(geom1, geom2))

    def RT_Intersects(self, rastertile, geom):
        if isinstance(rastertile, str):
            envelope = self._session.scalar(ga2.functions.ST_Envelope(rastertile+"::raster"))
        elif isinstance(rastertile, ga2.elements.RasterElement):
            envelope = self._session.scalar(ga2.functions.ST_Envelope(rastertile))
        else:
            raise Exception("rastertile should be string raster or RasterElement")

        isect = self._session.scalar(ga2.functions.ST_Intersects(envelope, geom))
        return isect
