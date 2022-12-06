from django.db import models
from django.conf import settings
from django.urls import reverse
from django.contrib import admin
from django.utils.functional import classproperty
from django.utils.translation import ugettext_lazy as _

from geonode.base.models import ResourceBase
from geonode.geoapps.models import GeoApp
from geonode.utils import build_absolute_uri

# Create your models here.
class ExternalApplication(GeoApp):

    url = models.URLField(max_length=2000, null=False, blank=False, help_text="Link to the external application")
    

    @property
    def embed_url(self):
        return None

    def get_detail_url(self):
        return build_absolute_uri(f"/externalapplications/{self.pk}")

    def get_absolute_url(self):
        return self.url

admin.site.register(ExternalApplication)