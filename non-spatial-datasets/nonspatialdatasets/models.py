from django.db import models
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
    
    def get_absolute_url(self):
        return f"/nonspatial/{self.pk}"

    @property
    def embed_url(self):
        try:
            if self.service_typename:
                return reverse('dataset_embed', kwargs={'layername': self.service_typename})
        except Exception as e:
            logger.exception(e)
            return None