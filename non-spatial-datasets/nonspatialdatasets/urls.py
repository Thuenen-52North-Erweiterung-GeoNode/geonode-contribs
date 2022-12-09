from django.urls import path
from django.conf.urls import url, include

urlpatterns = [
    url(r'^', include('nonspatialdatasets.api.urls')),
]