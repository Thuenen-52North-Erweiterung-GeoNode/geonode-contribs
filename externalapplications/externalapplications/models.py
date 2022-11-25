from django.db import models
from django.urls import reverse
from geonode.geoapps.models import GeoApp

# Create your models here.
class ExternalApplication(GeoApp):

    url = models.URLField(max_length=2000, null=False, blank=False, help_text="Link to the external application")

    def get_absolute_url(self):
        return self.url
