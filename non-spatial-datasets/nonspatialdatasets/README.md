# Non-Spatial Datasets

The Non-Spatial Datasets app makes possible to upload datasets which do not have any spatial data included.
The app adds a new subtype for datasets (`nonspatial`).

Data without spatial information (e.g. attribute data) can be uploaded as CSV files.

## Installation

To activate the external application app, add the following to the `settings.py`:

```py
INSTALLED_APPS += ( 'nonspatialdatasets', )
```

Make sure to add it _after_ the `geonode_mapstore_client` app as it makes client configuration adjustments via the mapstore templates.

Create database migrations and apply them via:

```sh
python manage.py makemigrations
python manage.py migrate
```

## Concept for Data Structure

Non-spatial, or attribute data is tabular like. 
The app accepts any CSV file which is described by [a table schema file](https://specs.frictionlessdata.io/table-schema/).
Before upload, make sure you have two files available in a zip file:

```sh
zipinfo -1 data.zip 
data.csv
data.csv.json
```

`data.csv` contains the data, `data.csv.json` contains the schema.

The successfully uploaded data is stored in a new table in the geodatabase.
The name of the new table is taken from the `name` field of the schema file.

## How to Upload Non-Spatial Datasets

You can upload non-spatial CSV files either via UI or API.

In the UI choosing `nonspatial` from the `Add Resource` menu and upload the zip file containing both data and schema.

Ingesting non-spatial data via the API, just execute

```
curl -X POST 'http://localhost/api/v2/nonspatialdatasets' -F file=@/path/to/data.zip
```

Make sure you choose [a proper way to authenticate](https://developer.mozilla.org/en-US/docs/Web/HTTP/Authentication).

## Removing Non-Spatial Datasets App

Before uninstalling the Non-Spatial Datasets app you will have to remove the data first.
This includes:

- Remove all data from the geonode database
- Delete all uploaded data from the geodatabase

Before we delete the non-spatial data from the geonode database, we have to know all table names containing the uploaded non-spatial datasets.
Open the Django shell and execute the following python tasks:

```py
python manage.py shell
from nonspatialdatasets.models import NonSpatialDataset

# List all table names in the geodatabase including non-spatial data 
# If the postgres_url is None, the data has been stored in the default geodatabase
for d in NonSpatialDataset.objects.all(): print(d.postgres_url, d.database_table)
# None bze_lw_horizon_3 
# ...

# Delete all instances from the geonode database
for d in NonSpatialDataset.objects.all(): d.delete()
```

In case you want to delete the uploaded data from the geodatabase, drop the table names from the listed geodatabase.
If the `postgres_url` is `None` the tables have to be dropped from the default geodatabase.

After removing the non-spatial data, you can revert all migrations of the app.
This can be done by executing the managemant command:

```sh
python manage.py migrate nonspatialdatasets zero
```

Once the database is cleaned up, the app can be removed by deleting it from the `INSTALLED_APPS` in the `settings.py`.
