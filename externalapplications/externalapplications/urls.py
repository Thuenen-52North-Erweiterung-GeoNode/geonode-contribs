from django.conf.urls import url, include
from . import views

urlpatterns = [  # 'geonode.external_applications.views',
    #url(r'^(?P<appid>\d+)/link/?$',
    #    views.link, name='external_application_link'),
    url(r'^create/?$', views.create_external_application, name='external_application_create'),
    url(r'^(?P<appid>[^/]+)/metadata_detail$', views.external_application_metadata_detail,
        name='external_application_metadata_detail'),
    url(r'^(?P<appid>\d+)/metadata$',
        views.external_application_metadata, name='external_application_metadata'),
    url(r'^(?P<appid>\d+)/metadata_advanced$', views.external_application_metadata_advanced,
        name='external_application_metadata_advanced'),
    #url(r'^', include('externalapplications.api.urls')),
]
