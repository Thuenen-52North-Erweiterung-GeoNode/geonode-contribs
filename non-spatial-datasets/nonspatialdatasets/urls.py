from django.urls import path
from django.conf.urls import url, include

from . import views

urlpatterns = [
    path('', views.index, name='index'),
    path('<int:dataset_id>', views.get_dataset_definition, name='get_dataset_data_definition'),
    path('<int:dataset_id>/data', views.get_dataset_data, name='get_dataset_data'),
    path('<int:dataset_id>/export', views.export_dataset_data, name='export_dataset_data')
]