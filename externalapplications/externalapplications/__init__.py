import os
from django.apps import AppConfig
from django.conf.urls import include, url
from django.db.models import Max

import logging
logger = logging.getLogger(__name__)

def run_setup_hooks(*args, **kwargs):
    from django.conf import settings
    from geonode.urls import urlpatterns
    from geonode.base.models import Menu, MenuItem, MenuPlaceholder

    LOCAL_ROOT = os.path.abspath(os.path.dirname(__file__))
    settings.MAPSTORE_TRANSLATIONS_PATH += ("/static/mapstore/ea-translations",)
    settings.TEMPLATES[0]["DIRS"].insert(0, os.path.join(LOCAL_ROOT, "templates"))
    title = "External Applications"
    
    menu_filter_create = getattr(settings, "EXTERNAL_APPLICATION_MENU_FILTER_AUTOCREATE", False)
    if menu_filter_create:
        if not Menu.objects.filter(title=title).exists():
            ph = MenuPlaceholder.objects.filter(name="TOPBAR_MENU_LEFT").first()
            if (not ph):
                logger.info(f"MenuPlaceholder not yet created. Skipping")
                return

            max_order = Menu.objects.filter(placeholder=ph).aggregate(Max("order"))["order__max"]
            order = 0 if max_order is None else max_order + 1
            menu = Menu.objects.create(title=title, placeholder=ph, order=order)
            MenuItem.objects.create(title=title, menu=menu, order=1, blank_target=False,
                                    url="/catalogue/#/search/?f=externalapplication")

    urlpatterns += [url(r'^external-applications/', include('externalapplications.urls'))]


class ExternalapplicationsConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'externalapplications'
    type = 'GEONODE_APP'
    default_model = 'ExternalApplication'

    def ready(self):
        super().ready()
        run_setup_hooks()


default_app_config = 'externalapplications.ExternalapplicationsConfig'
