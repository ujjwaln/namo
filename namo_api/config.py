__author__ = 'ujjwal'
import socket
from datetime import datetime


def get_env():
    hostname = socket.gethostname()
    if 'cedarkey' in hostname:
        return 'production'
    else:
        return 'development'


class Config(object):

    _instance = None

    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            cls._instance = super(Config, cls).__new__(cls, *args, **kwargs)

        return cls._instance

    def __init__(self, env='development', dbname=None):
        env = str(env).lower()

        if env == 'development':
            if dbname is None:
                dbname = "ci_dev"

            username = "postgres"
            password = "postgres"
            servername = "localhost"
            port = 5432
            datadir = r'/home/ujjwal/essic/data'
            adminusername = 'postgres'
            adminpassword = 'postgres'
            logsql = False
            parallel = True
            nprocs = 3
            debug = True
            start_date = datetime(year=2014, month=7, day=22, hour=5, minute=0, second=0)
            end_date = datetime(year=2014, month=7, day=22, hour=6, minute=0, second=0)

        if env == 'production':
            if dbname is None:
                dbname = "namo_prod"

            username = "unarayan"
            password = "crvcrv11"
            servername = "localhost"
            port = 5432
            datadir = r'/nas/rhome/unarayan/data'
            adminusername = 'unarayan'
            adminpassword = 'crvcrv11'
            logsql = False
            parallel = True
            nprocs = 6
            debug = False

            start_date = datetime(year=2014, month=7, day=23, hour=4, minute=0, second=0)
            end_date = datetime(year=2014, month=7, day=25, hour=0, minute=0, second=0)


        self.dbname = dbname
        self.username = username
        self.adminusername = adminusername
        self.adminpassword = adminpassword
        self.password = password
        self.servername = servername
        self.port = port
        self.datadir = datadir
        self.logsql = logsql
        self.parallel = parallel
        self.nprocs = nprocs
        self.start_date = start_date
        self.end_date = end_date
        self.debug = debug

    def sqa_connection_string(self):
        return 'postgresql://%s:%s@%s:%d/%s' % (self.username, self.password, self.servername, self.port, self.dbname)

    def ogr_connection_string(self):
        return "PG:dbname='%s' user='%s' password='%s'" % (self.dbname, self.username, self.password)

    def pgsql_conn_str(self):
        return "host=%s dbname=%s user=%s password=%s" % (self.servername, self.dbname, self.username, self.password)

    def pgsql_postgres_conn_str(self):
        return "host=%s dbname=%s user=%s password=%s" % ("localhost", "postgres", self.adminusername, self.adminpassword)
