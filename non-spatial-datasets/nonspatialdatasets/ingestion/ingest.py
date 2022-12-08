from django.conf import settings
from django.core.files.storage import FileSystemStorage
import mimetypes
import zipfile
import uuid
import os
import shutil
import json
import csv
from urllib.parse import urlencode, urlparse, urlunparse, parse_qs

from ..database.database import create_dataset_table, insert_data_rows, insert_catalog_entry, query_dataset
from ..database.db_models import NonSpatialDatasetParameters

def ingest_zipped_dataset(zip_file):
    mt = mimetypes.guess_type(zip_file)
    
    # only zip files supported at the moment
    if mt and mt[0] == "application/zip":
        with zipfile.ZipFile(zip_file, "r") as zip_ref:
            fs = FileSystemStorage()
            extract_path = os.path.join(fs.location, str(uuid.uuid4()))
            
            try:
                zip_ref.extractall(extract_path)
                csv_file, json_file = verify_archive_contents(extract_path)
                
                tdr = load_tabular_data_resource(json_file)
                
                dataset_title, dataset_name, dataset_abstract = extract_basic_metadata(tdr)
                
                columns, dialect = resolve_dataset_definitions(tdr)
                
                dataset_id, dataset_table = ingest_csv_file(dataset_title, csv_file, columns, dialect)
                return NonSpatialDatasetParameters(dataset_id, dataset_title, dataset_name, dataset_abstract, columns, dataset_table)
            finally:
                # cleanup after ingestion
                shutil.rmtree(extract_path, ignore_errors=True)
                
        # cleanup after ingestion
        os.remove(zip_file)
        
    else:
        raise Exception("Unsupported file type")
    
    
def validate_connection_url_and_extract_table(path_url):
    if (path_url.scheme != "postgres"):
        raise Exception("Invalid scheme provided in connection URL")
    
    if (not path_url.hostname):
        raise Exception("Invalid host provided in connection URL")
    
    if (not path_url.username):
        raise Exception("No username provided in connection URL")
    
    if (not path_url.password):
        raise Exception("No password provided in connection URL")
    
    if (not path_url.query or len(path_url.query) == 0):
        raise Exception("No database table provided as a query parameter")
    else:
        qs = parse_qs(path_url.query)
        if "table" in qs and len(qs["table"][0]) > 0:
            return qs["table"][0]
        else:
            raise Exception("Invalid database table provided as a query parameter")
    
def register_dataset(tabular_data_resource):
    if "path" not in tabular_data_resource or len(tabular_data_resource["path"]) < len("postgres://___"):
        raise Exception("No or invalid 'path' attribute defined in the Tabular Data Resource definition.")

    path_url = urlparse(tabular_data_resource["path"])
    target_table = validate_connection_url_and_extract_table(path_url)

    dataset_title, dataset_name, dataset_abstract = extract_basic_metadata(tabular_data_resource)
                
    columns, dialect = resolve_dataset_definitions(tabular_data_resource)
    
    # store the dataset table name in our meta/catalog table
    dataset_id = insert_catalog_entry(target_table, columns)
    
    # remove the custom 'table' as it is not valid for a postgres connection URL
    query = parse_qs(path_url.query, keep_blank_values=True)
    query.pop('table', None)
    path_url = path_url._replace(query=urlencode(query, True))
    
    return NonSpatialDatasetParameters(dataset_id, dataset_title, dataset_name, dataset_abstract, columns, target_table, urlunparse(path_url))
    
def verify_archive_contents(content_dir):
    csv_file = None
    json_file = None
    for f in os.listdir(content_dir):
        filename = os.fsdecode(f)
        if filename.endswith(".csv"):
            csv_file = filename
        elif filename.endswith(".json"):
            json_file = filename
        else:
            continue
        
    if not csv_file:
        raise Exception("No CSV file provided")
    if not json_file:
        raise Exception("No JSON file for describing the CSV structure provided")
    
    return os.path.join(content_dir, csv_file), os.path.join(content_dir, json_file)

def load_tabular_data_resource(json_file):
    with open(json_file) as f:
        tdr = json.load(f)
        
    if "name" not in tdr or "title" not in tdr or "schema" not in tdr:
        raise Exception("Unexpected Tabular Data Resource JSON description")
        
    return tdr

def extract_basic_metadata(tdr):
    name = tdr["name"]
    title = tdr["title"]
    
    if "description" in tdr:
        description = tdr["description"]
    
    return name, title, description

def resolve_dataset_definitions(tdr):
    # extract the actual column field definitions
    columns = tdr["schema"]["fields"]

    # set up primary keys
    for pk in tdr["schema"]["primaryKey"]:
        for c in columns:
            if c["name"] == pk:
                c["primaryKey"] = True
                break

    dialect = None
    if ("dialect" in tdr):
        dialect = tdr["dialect"]

    return columns, dialect

def ingest_csv_file(dataset_title, csv_file, columns, dialect):
    # request a target database table 
    target_table = create_dataset_table(dataset_title, columns)

    # store the dataset table name in our meta/catalog table
    dataset_id = insert_catalog_entry(target_table, columns)

    # load actual data
    data = []
    with open(csv_file, newline='') as cf:
        if (dialect):
            if ("delimiter" in dialect):
                delimiter = dialect["delimiter"]
            else:
                delimiter = ";"
            if ("quotechar" in dialect):
                quotechar = dialect["quotechar"]
            else:
                quotechar = '"'
        else:
            delimiter = ";"
            quotechar = '"'
            
        reader = csv.reader(cf, delimiter=delimiter, quotechar=quotechar)
        
        header_row = True
        for row in reader:
            if header_row:
                header_row = False
                pass
            else:
                data.append(row)

    # insert all data into the dataset table
    insert_data_rows(target_table, columns, data)

    return dataset_id, target_table