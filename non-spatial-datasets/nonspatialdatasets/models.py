from django.db import models
from django.urls import reverse

from geonode.utils import build_absolute_uri
from geonode.layers.models import Dataset
import logging

logger = logging.getLogger(__name__)

class NonSpatialDataset(Dataset):
    
    postgres_url = models.URLField(
        'Postgres URL',
        null=True,
        blank=True,
        help_text='The Postgres connection string as a URL (optional). If empty, the API will lookup the default GeoNode database')
    
    internal_database_id = models.IntegerField('Internal Database ID', null=True, blank=True)
    
    database_table = models.CharField('Database Table', max_length=255, null=True, blank=True)
    database_user = models.CharField('Database User', max_length=255, null=True, blank=True)
    database_password = models.CharField('Database Password', max_length=255, null=True, blank=True)
    
    column_definitions = models.TextField('Column Definitions', blank=False)
    
    def has_thumbnail(self):
        return False

    def get_thumbnail_url(self):
        return None

    def get_detail_url(self):
        url = f"/nonspatial/{self.pk}"
        return build_absolute_uri(url)

    def get_absolute_url(self):
        url = f"/api/v2/nonspatialdatasets/{self.pk}"
        return build_absolute_uri(url)

    