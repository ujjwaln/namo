__author__ = 'ujjwal'
from flask import Flask, send_from_directory, render_template
from flask.json import JSONEncoder
import flask.ext.sqlalchemy
import flask.ext.restless
import geoalchemy2 #this import introduces geometry types in sqlalchemy
from sqlalchemy.types import Float
from sqlalchemy.engine import reflection
from sqlalchemy import create_engine, type_coerce
from namo_app.config import Config, get_env
from namo_app import logger
from geoalchemy2.functions import GenericFunction
from geoalchemy2.types import CompositeType
from namo_app.web.service import crossdomain
from namo_app.db.models import Mask, RasterTile, DataGranule, DataFormat


"""
    Flask application for creating REST API, using Flask-Restless
    /layers end point returns the names of all tables that are saved in postgresql
    /api/rastertile/datagranule_id returns rasters dumped into geosjon polygons
    note /api endpoint returns datagranule via flask_restless
"""

class GeomvalType(CompositeType):
    typemap = {'geom': geoalchemy2.Geometry('POLYGON'), 'val': Float}


class ST_DumpAsPolygons(GenericFunction):
    name = 'ST_DumpAsPolygons'
    type = geoalchemy2.Geometry


class ST_PixelAsPolygons(GenericFunction):
    name = 'ST_PixelAsPolygons'
    type = geoalchemy2.Geometry


class GeoJSONEncoder(JSONEncoder):
    def default(self, o):
        if isinstance(o, unicode):
            return str(o)

        if isinstance(o, list):
            return [GeoJSONEncoder.default(self, item) for item in o]

        if isinstance(o, dict):
            resp = {}
            for key in o.keys():
                val = GeoJSONEncoder.default(self, o[key])
                resp[key] = val
            return resp

        if isinstance(o, geoalchemy2.WKBElement):
            str_data = db.session.scalar(geoalchemy2.functions.ST_AsGeoJSON(o))
            return flask.json.loads(str_data)

        if isinstance(o, geoalchemy2.RasterElement):
            try:
                gv = type_coerce(ST_DumpAsPolygons(o), GeomvalType()).label("gvs")
                q1 = db.session.query(gv)
                q2 = db.session.query(geoalchemy2.func.ST_AsGeoJSON(geoalchemy2.func.ST_Transform(q1.subquery().c.gvs.geom, 3857)))
                geoms = q2.all()

                q3 = db.session.query(q1.subquery().c.gvs.val)
                vals = q3.all()

                i = 0
                dat = []
                for geom in geoms:
                    val, poly = vals[i][0], flask.json.loads(geom[0])
                    dat.append((poly, val))
                    i += 1

                #js = flask.json.dumps(dat, cls=GeoJSONEncoder)
                return dat
            except Exception:
                pass

        if isinstance(o, RasterTile):
            resp = {}
            for key in o.__dict__:
                if key.startswith('_') or key.startswith('__'):
                    continue
                resp[key] = GeoJSONEncoder.default(self, o.__dict__[key])
            return flask.json.dumps(resp, cls=JSONEncoder)

        return flask.json.dumps(o, cls=JSONEncoder)


geojson_encoder = GeoJSONEncoder()


def post_get_many(result=None, search_params=None, **kw):
    if isinstance(result["objects"], list):
        json_list = geojson_encoder.default(result["objects"])
        result["objects"] = json_list

    return result


def post_get_single(result=None, search_params=None, **kw):
    json_result =geojson_encoder.default(result)
    return json_result


#add cross domain headers
def add_cors_headers(response):
    response.headers['Access-Control-Allow-Origin'] = '*'
    response.headers['Access-Control-Allow-Credentials'] = 'true'
    return response


config = Config(env=get_env())

app = Flask(__name__)
app.after_request(add_cors_headers)

app.config['DEBUG'] = config.debug
app.config['SQLALCHEMY_DATABASE_URI'] = config.sqa_connection_string()
app.json_encoder = GeoJSONEncoder

db = flask.ext.sqlalchemy.SQLAlchemy(app)
engine = create_engine(config.sqa_connection_string())
insp = reflection.Inspector.from_engine(engine)

#discover table names in public schema using flask restless inspector
table_names = insp.get_table_names()


manager = flask.ext.restless.APIManager(app, flask_sqlalchemy_db=db)


if 'spatial_ref_sys' in table_names:
    table_names.remove('spatial_ref_sys')
    table_names.remove('rastertile')


for table_name in table_names:
    columns = insp.get_columns(table_name)
    pkey = insp.get_pk_constraint(table_name)
    attrs = {}

    for col in columns:
        if 'type' in col:
            if col["name"] in pkey["constrained_columns"]:
                attrs[col["name"]] = db.Column(col["type"], primary_key=True)
            else:
                attrs[col["name"]] = db.Column(col["type"])

    attrs["__tablename__"] = table_name

    table_class = type(str(table_name), (db.Model,), attrs)

    #need GET_MANY post processor as flask jsonify doesn't handle list serialization
    manager.create_api(table_class, methods=['GET'], results_per_page=None,
                       postprocessors={'GET_MANY': [post_get_many], 'GET_SINGLE': [post_get_single]})

    #manager.create_api(table_class, methods=['GET'], results_per_page=None)
    logger.info("Activted endpoint: api/%s" % table_name)


@app.route("/")
def index():
    return send_from_directory("static", "index.html")


@app.route("/layers/")
@crossdomain(origin="*", methods=["GET", "OPTIONS"])
def layers():
    return flask.json.dumps({"layers": table_names}, cls=GeoJSONEncoder)


@app.route("/api/rastertile/<datagranule_id>")
@crossdomain(origin="*", methods=["GET", "OPTIONS"])
def rastertile(datagranule_id):
    from namo_app.db.access import SqaAccess
    from namo_app.config import Config, get_env
    from namo_app.db.models import init_mapper, Mask, RasterTile, DataGranule, DataFormat
    from flask import request

    #q	{"filters":[{"name":"datagranule_id","op":"==","val":"3"}]}
    config = Config(env=get_env())
    init_mapper(config.sqa_connection_string())

    mask = request.args.get('mask', None)
    with SqaAccess(conn_str=config.sqa_connection_string()) as sqa:
        tileObjs = sqa.all(RasterTile, filterr={'datagranule_id': datagranule_id})
        response = flask.json.dumps({"tiles": tileObjs})

    return response

app.run()
