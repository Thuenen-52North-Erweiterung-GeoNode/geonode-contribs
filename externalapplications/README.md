# External Applications

The External Applications app is a contrib module for GeoNode.
The app is compatible with GeoNode v4 and GeoNode MapStore Client v4.

The app adds a model `ExternalApplication` which extends from `GeoApp`.
It integrates as any other resource type so that GeoNode can index, search, and filter an external application like Datasets, Maps, or Dashboards.

## Installation and Configuration

To activate the external application app, add the following to the `settings.py`:

```py
INSTALLED_APPS += ( 'externalapplications', )
EXTERNAL_APPLICATION_MENU_FILTER_AUTOCREATE = os.getenv('EXTERNAL_APPLICATION_MENU_FILTER_AUTOCREATE ', False)
```

Make sure to add it _after_ the `geonode_mapstore_client` app as it makes client configuration adjustments via the mapstore templates.

Create database migrations and apply them via:

```sh
python manage.py makemigrations
python manage.py migrate
```

### Add a Filter Menu

The app adds the resource type `externalapplication` on which you can apply filter on (either by API or mapstore-client search).

If you want the app to create a quick filter menu entry automatically, set `EXTERNAL_APPLICATION_MENU_FILTER_AUTOCREATE=True`.

In case you want to manually add such entry use the GeoNode admin. 
First create a `Menu` _External Application_ which you put under placeholder `TOPBAR_MENU_LEFT`. 
After that, create a `MenuItem` to create a `MenuItem` _External Application_ and select the `Menu` you created.
To filter all external applications add the URL `/catalogue/#/search/?f=externalapplication`.
