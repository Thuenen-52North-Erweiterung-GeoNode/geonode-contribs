import os
import logging
import json
import csv

from ..database.database import create_catalog_table, create_dataset_table, insert_data_rows, insert_catalog_entry, query_dataset

logger = logging.getLogger(__name__)

# load tabular data resource
with open('../test_data/data.csv.json') as f:
    defs = json.load(f)

# extract the actual column field definitions
columns = defs["schema"]["fields"]

# set up primary keys
for pk in defs["schema"]["primaryKey"]:
    for c in columns:
        if c["name"] == pk:
            c["primaryKey"] = True
            break

# request a target database table 
target_table = create_dataset_table("BZE_LW_HORIZON", columns)

# store the dataset table name in our meta/catalog table
dataset_id = insert_catalog_entry(target_table, columns)

# load actual data
data = []
with open('../test_data/data.csv', newline='') as csvfile:
    if ("dialect" in defs):
        if ("delimiter" in defs["dialect"]):
            delimiter = defs["dialect"]["delimiter"]
        else:
            delimiter = ";"
        if ("quotechar" in defs["dialect"]):
            quotechar = defs["dialect"]["quotechar"]
        else:
            quotechar = '"'
    else:
        delimiter = ";"
        quotechar = '"'
        
    reader = csv.reader(csvfile, delimiter=delimiter, quotechar=quotechar)
    
    header_row = True
    for row in reader:
        if header_row:
            header_row = False
            pass
        else:
            data.append(row)

# insert all data into the dataset table
insert_data_rows(target_table, columns, data)

# query first two rows
data = query_dataset(dataset_id, size=2)
print(data)