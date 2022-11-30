from django.db import models
from django.conf import settings
from geonode.geoapps.models import GeoApp

# Create your models here.
class ExternalApplication(GeoApp):

    url = models.URLField(max_length=2000, null=False, blank=False, help_text="Link to the external application")

    @property
    def embed_url(self):
        return ""

    def get_detail_url(self):
        site_url = settings.SITEURL.rstrip('/') if settings.SITEURL.startswith('http') else settings.SITEURL
        return f"{site_url}/external-applications/{self.pk}"

    def get_absolute_url(self):
        return self.url
