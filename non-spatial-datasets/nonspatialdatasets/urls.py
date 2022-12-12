from django.conf.urls import url, include

from . import views

urlpatterns = [
    url(r'^upload/?$', views.non_spatial_dataset_upload, name='non_spatial_dataset_upload'),
    url(r'^(?P<datasetid>[^/]+)/metadata_detail$', views.non_spatial_dataset_metadata_detail, 
        name="non_spatial_dataset_metadata_detail"),
    url(r'^', include('nonspatialdatasets.api.urls')),
]