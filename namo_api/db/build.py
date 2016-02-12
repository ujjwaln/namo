__author__ = 'ujjwal'

from namo_app import logger
from namo_app.config import Config, get_env
from namo_app.helpers.pgdb_helper import PGDbHelper
from namo_app.db.access import SqaAccess
from namo_app.db.spref import SPREFS


def check_db_exists(conn, dbname):
    sql = "SELECT 1 FROM pg_database WHERE datname = '%s'" % dbname
    results = conn.execute(sql)
    if len(results) > 0:
        return True
    return False


def insert_masks(config):
    from namo_app.db.ref_data import MASKINFOS
    from namo_app.helpers.shp_helper import ShapeFileHelper
    from namo_app.db.models import Mask

    with SqaAccess(conn_str=config.sqa_connection_string()) as sqa:
        for mask_info in MASKINFOS:

            if mask_info[0] == "shapefile":
                shp_helper = ShapeFileHelper(mask_info[2])
                for geom in shp_helper.wkt_geoms(4326):
                    ewkt_geom = geom
                    break

                mask = Mask(name=mask_info[1], geom=ewkt_geom)
                sqa.insert(mask)

            if mask_info[0] == "bbox":
                mask_name = mask_info[1]
                x_min = mask_info[2][0]
                y_max = mask_info[2][1]
                x_max = mask_info[2][2]
                y_min = mask_info[2][3]
                srid = mask_info[3]

                poly = "SRID=%d;POLYGON (( %f %f, %f %f, %f %f, %f %f, %f %f ))" % \
                       (srid, x_max, y_min, x_max, y_max, x_min, y_max, x_min, y_min, x_max, y_min)
                mask = Mask(name=mask_name, geom=poly)
                sqa.insert(mask)


def insert_refdata(config):
    ci_db_helper = PGDbHelper(config.pgsql_conn_str())
    logger.info("Insert special coordinate systems %s" % config.dbname)
    for spref in SPREFS:
        ci_db_helper.execute(spref.sql_insert_statement)

    #insert custom functions for calculating du/dx, dv/dx
    logger.info("Inserting special plp/sql procedures %s" % config.dbname)
    insert_plpsql_functions(ci_db_helper)

    from namo_app.db.models import init_mapper
    init_mapper(sqa_conn_str=config.sqa_connection_string())

    logger.info("Inserting ref data on %s" % config.dbname)

    from namo_app.db.ref_data import PROVIDERS, VARIABLES, FORMATS

    with SqaAccess(conn_str=config.sqa_connection_string()) as sqa:
        logger.info("Inserting variables")
        sqa.insert(VARIABLES)

        logger.info("Inserting formats")
        sqa.insert(FORMATS)

        logger.info("Inserting providers")
        sqa.insert(PROVIDERS)


def create_new_geodb(config):
    admin_db_helper = PGDbHelper(conn_str=config.pgsql_postgres_conn_str())

    if check_db_exists(admin_db_helper, config.dbname):
        logger.info("Deleting existing db %s" % config.dbname)
        admin_db_helper.execute("DROP DATABASE %s" % config.dbname)

    if not check_db_exists(admin_db_helper, config.dbname):
        logger.info("Creating new db %s" % config.dbname)
        admin_db_helper.execute("CREATE DATABASE %s" % config.dbname)

    #connect to new db
    ci_db_helper = PGDbHelper(config.pgsql_conn_str())
    logger.info("Enabling geodatabase on %s" % config.dbname)
    ci_db_helper.execute("CREATE EXTENSION POSTGIS;")


def insert_plpsql_functions(conn):
        sql = """
CREATE OR REPLACE FUNCTION st_xderivative4ma(IN matrix double precision[], IN nodatamode text, VARIADIC args text[])
      RETURNS double precision AS
    $BODY$
	DECLARE
	    width double precision;
	    left_x double precision;
	    right_x double precision;
	    xderivative double precision;
        _matrix double precision[][];
	BEGIN
        _matrix := matrix;
	    width := args[1]::double precision;
	    if array_upper(matrix, 1) = 3 then
		left_x := _matrix[1][2];
		right_x := _matrix[3][2];
		    if (left_x is NULL) or (right_x is NULL) THEN
			xderivative := NULL;
		    else
			xderivative := (right_x - left_x) / (2 * width);
			end if;
	    else
		xderivative = NULL;
	    end if;

	    return xderivative;
	END;
	$BODY$
      LANGUAGE plpgsql IMMUTABLE;
    --  COST 100;
    --ALTER FUNCTION st_xderivative4ma(double precision[], text, text[])
    --  OWNER TO postgres;

CREATE OR REPLACE FUNCTION st_yderivative4ma(IN matrix double precision[], IN nodatamode text, VARIADIC args text[])
  RETURNS double precision AS
$BODY$
    DECLARE
        height double precision;
        upper_y double precision;
        lower_y double precision;
        yderivative double precision;
        _matrix double precision[][];
    BEGIN
        height := args[1]::double precision;
        _matrix := matrix;
        if array_upper(matrix, 2) = 3 then
	    upper_y := matrix[2][3];
	    lower_y := matrix[2][1];
            if (upper_y is NULL) or (lower_y is NULL) THEN
	        yderivative := NULL;
            else
	        yderivative := (upper_y - lower_y) / (2 * height);
            end if;
	else
	    yderivative = NULL;
        end if;

        return yderivative;
    END;
    $BODY$
  LANGUAGE plpgsql IMMUTABLE;
--  COST 100;
--ALTER FUNCTION st_yderivative4ma(double precision[], text, text[])
--  OWNER TO postgres;


CREATE OR REPLACE FUNCTION st_shannonentropy(IN items anyarray, IN nodatamode text, VARIADIC args text[])
	RETURNS double precision
        --RETURNS text
as
$BODY$
	DECLARE
	    tmp text;
            qry text;
            r record;
            H double precision;
            p double precision;
            count integer;
            --output text;
	BEGIN
            --output := '';
            H := 0;
            p := 0;
	    count := array_upper(items, 1);
            tmp := quote_literal('{' || array_to_string(items, ',') || '}');
	    qry := 'select unnest((' || tmp || '::text)::text[]) as val, count(*) num group by val order by val';
            for r in execute qry loop
	        p := cast(r.num as double precision) / count;
                H := H + p * log(2.0, cast(p as numeric));
                --output := output || r.val || '-' || r.num || ':' || cast(p as text) || '--';
            end loop;
            return -1 * H;
	    --return output;
	END;
	$BODY$
  LANGUAGE plpgsql IMMUTABLE;
--  COST 100;
--ALTER FUNCTION st_shannonentropy(anyarray, text, text[])
--  OWNER TO postgres;

        """
        conn.execute(sql)


if __name__ == '__main__':
    config = Config(env=get_env())
    create_new_geodb(config)

    insert_refdata(config)
    insert_masks(config)