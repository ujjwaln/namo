__author__ = 'ujjwal'
from namo_app.config import Config, get_env
from namo_app.db.models import init_mapper


config = Config(env=get_env())
init_mapper(sqa_conn_str=config.sqa_connection_string())

