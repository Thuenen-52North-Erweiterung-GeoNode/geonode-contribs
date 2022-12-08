import psycopg2
import os
import logging
import json

logger = logging.getLogger(__name__)

POSTGRES_USER = os.environ.get('GEONODE_GEODATABASE', 'postgres')
POSTGRES_PASSWORD = os.environ.get('GEONODE_GEODATABASE_PASSWORD', 'postgres')
DATABASE_HOST = os.environ.get('DATABASE_HOST', 'postgres')
DATABASE_PORT = os.environ.get('DATABASE_PORT', 'postgres')
DATABASE_NAME = os.environ.get('GEONODE_GEODATABASE', 'postgres')
                                   

CATALOG_DB_NAME = "non_spatial_datasets"

MAX_STRING_FIELD_LENGTH = 256

def execute_statement(stmt, result_count=0, connection_string=None):
    conn = None
    result = None
    try:
        if connection_string:
            # a custom DB connection string is defined
            conn = psycopg2.connect(connection_string)
        else:
            # use the default database
            conn = psycopg2.connect(dbname=DATABASE_NAME, user=POSTGRES_USER, host=DATABASE_HOST, port=DATABASE_PORT, password=POSTGRES_PASSWORD)
        cur = conn.cursor()
        
        logger.debug("[NON SPATIAL] SQL Query: %s", stmt)
        cur.execute(stmt)
        
        if (result_count > 1):
            result = cur.fetchall()
        elif (result_count > 0):
            result = cur.fetchone()
        
        conn.commit()
    except Exception as e:
        logger.error(
            "Error executing statement: %s",
            str(e))
        logger.exception(e)
        raise e
    finally:
        try:
            if conn:
                conn.close()
        except Exception as e:
            logger.error("Error closing PostGIS conn %s:%s", CATALOG_DB_NAME, str(e)) 
    
    return result

def table_exists(table_name):
    stmt = f"""SELECT EXISTS(
        SELECT * 
        FROM information_schema.tables 
        WHERE 
        table_schema = 'public' AND 
        table_name = '{table_name}'
        );"""
    result = execute_statement(stmt, 1)
    
    if (result[0]):
        return True
    else:
        return False
            
def create_catalog_table():
    stmt = f"""CREATE TABLE IF NOT EXISTS {CATALOG_DB_NAME} (
        dataset_id serial PRIMARY KEY,
        table_name VARCHAR (50) UNIQUE NOT NULL,
        column_definitions TEXT NOT NULL,
        created TIMESTAMP DEFAULT NOW()
        );"""
    execute_statement(stmt)
    
def insert_catalog_entry(target_table, column_defs):
    column_defs_json = json.dumps(column_defs)
    stmt = f"INSERT INTO {CATALOG_DB_NAME}(table_name, column_definitions) VALUES ('{target_table}', '{column_defs_json}');"
    
    execute_statement(stmt)
    result = execute_statement(f"SELECT dataset_id FROM {CATALOG_DB_NAME} WHERE table_name = '{target_table}'", 1)
    return result[0]
            
def resolve_dataset_table(id):
    stmt = f"SELECT table_name from {CATALOG_DB_NAME} WHERE dataset_id = {id};"
    table = execute_statement(stmt, 1)
    return table[0]

def sanitize(s):
    result = s.lower()
    result = result.replace(" ", "_").replace(":", "_")
    return result

def resolve_unique_table_name(dataset_title):
    candidate = sanitize(dataset_title)
    
    current_candidate = candidate
    i = 0
    while (table_exists(current_candidate)):
        current_candidate = f"{candidate}_{i}"
        i += 1
        
    return current_candidate

def resolve_sql_type(type):
    if (type == "integer"):
        return "INT"
    elif (type == "number"):
        return "NUMERIC"
    elif (type == "string"):
        return f"VARCHAR({MAX_STRING_FIELD_LENGTH})"
    
    raise Exception(f"Unsupported type: {type}")

def create_column_defs_sql(column_defs):
    sql_defs = []
    pk_names = []
    for cd in column_defs:
        name = sanitize(cd["name"])
        sql_defs.append(f'{name} {resolve_sql_type(cd["type"])}')
        if ("primaryKey" in cd and cd["primaryKey"] == True):
            pk_names.append(name)
    
    # primary key(s)
    pk = f"PRIMARY KEY({', '.join(pk_names)})"

    # sql syntax        
    cols = ", ".join(sql_defs)
    
    return f"{cols}, {pk}"

def create_dataset_table(dataset_title, column_defs):
    target_table = resolve_unique_table_name(dataset_title)
    
    column_defs_sql = create_column_defs_sql(column_defs)
    
    stmt = f"CREATE TABLE IF NOT EXISTS {target_table} ({column_defs_sql});"
    table = execute_statement(stmt)
    return target_table

def insert_data_rows(target_table, column_defs, data_rows):
    for r in data_rows:
        preprocessed_vals = []
        i = 0
        for v in r:
            try:
                if (column_defs[i]["type"] in ["integer", "number"]):
                    preprocessed_vals.append(str(v))
                else:
                    preprocessed_vals.append(f"'{v}'")
            except Exception as e:
                logger.exception(e)
            i += 1
        
        stmt = f"INSERT INTO {target_table} VALUES ({', '.join(preprocessed_vals)});"
        execute_statement(stmt)

def get_column_definitions(dataset_id):
    stmt = f"SELECT column_definitions from {CATALOG_DB_NAME} WHERE dataset_id = {dataset_id}"
        
    data = execute_statement(stmt, 1)
    column_defs = json.loads(data[0])
    return column_defs

def find_column_definition(column_defs, key):
    el = [x for x in column_defs if x["name"] == key]
    if el:
        return el[0]
    
    return None

def construct_sql_filter(filter_def, column_defs):
    defs = []
    for key, value in filter_def.items():
        key_def = find_column_definition(column_defs, key)
        if (key_def):
            sanitized_key = sanitize(key)
            if (key_def["type"] in ["integer", "number"]):
                defs.append(f"{sanitized_key} = {value}")
            else:
                defs.append(f"{sanitized_key} = '{value}'")
    
    if (len(defs) > 0):
        return " AND ".join(defs)
    
    return None
    
def query_dataset(dataset_id, start=0, size=50, filters=None, sort=None, connection_string=None, database_table=None):
    # load column defs
    column_defs = get_column_definitions(dataset_id)
    
    # order by
    order = ""
    if (sort):
        asc_desc = "ASC"
        if (not sort["ascending"]):
            asc_desc = "DESC"
        order = f'ORDER BY {sort["sort"]} {asc_desc}'
        
        
    # where clause
    where = ""
    if (filters):
        sql_defs = construct_sql_filter(filters, column_defs)
        if (sql_defs):
            where = f" WHERE {sql_defs} "
    
    # contruct the query
    if (not database_table):
        target_table = resolve_dataset_table(dataset_id)
    else:
        target_table = database_table
    
    stmt = f"SELECT * from {target_table} {where} {order} LIMIT {size} OFFSET {start};"
    
    # construct a nice array of dicts
    result = []
    data = execute_statement(stmt, size, connection_string)
    
    for d in data:
        i = 0
        entry = {}
        for v in d:
            entry[column_defs[i]["name"]] = v
            i += 1
        result.append(entry)
    
    return result
