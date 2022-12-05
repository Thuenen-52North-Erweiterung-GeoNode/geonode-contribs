from django.db import models
from django.conf import settings
from django.urls import reverse
from django.contrib import admin
from django.utils.functional import classproperty
from django.utils.translation import ugettext_lazy as _

from geonode.geoapps.models import GeoApp
from geonode.groups.conf import settings as groups_settings
from geonode.security.permissions import (
    VIEW_PERMISSIONS,
    OWNER_PERMISSIONS,
)
from geonode.utils import build_absolute_uri

# Create your models here.
class ExternalApplication(GeoApp):

    url = models.URLField(max_length=2000, null=False, blank=False, help_text="Link to the external application")
    
    @classproperty
    def allowed_permissions(cls):
        return {
            "anonymous": VIEW_PERMISSIONS,
            "default": OWNER_PERMISSIONS,
            groups_settings.REGISTERED_MEMBERS_GROUP_NAME: OWNER_PERMISSIONS
        }

    @classproperty
    def compact_permission_labels(cls):
        return {
            "none": _("None"),
            "view": _("View Metadata"),
            "download": _("View"),
            "edit": _("Edit"),
            "manage": _("Manage"),
            "owner": _("Owner")
        }

    @property
    def embed_url(self):
        return None

    def get_detail_url(self):
        return build_absolute_uri(reverse("external_application_metadata", args=(self.pk,)))

    def get_absolute_url(self):
        return self.url


admin.site.register(ExternalApplication)