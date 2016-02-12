__author__ = 'ujjwal'
import traceback
from namo_app.db.access import PGDbAccess
from namo_app import logger
from psycopg2 import ProgrammingError


class PGDbHelper(object):
    """
    AdminDBHelper contains utility functions for creating the database, deleting existing
    database etc using pyscopg2 driver directly (as opposed to SQLAlchemy dependent modules)
    """
    def __init__(self, conn_str, echo=False):
        self.conn_string = conn_str
        self.echo = echo

    def execute(self, sql_string, values=None):
        try:
            with PGDbAccess(self.conn_string, self.echo) as pga:
                if values is None:
                    pga.cur.execute(sql_string)
                    pga.conn.commit()
                elif isinstance(values, list):
                    pga.cur.executemany(sql_string, values)
                    pga.conn.commit()
                else:
                    pga.cur.execute(sql_string, values)
                    pga.conn.commit()

                try:
                    results = pga.cur.fetchall()
                except ProgrammingError, ex:
                    results = []

                return results

        except Exception, ex:
            logger.debug("Error while executing %s" % sql_string)
            logger.debug(traceback.print_exc())
            raise ex

