#########################################################################
#
# Copyright (C) 2020 OSGeo
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program. If not, see <http://www.gnu.org/licenses/>.
#
#########################################################################
from geonode.api.urls import router
from django.conf.urls import url, include

from geonode.urls import urlpatterns as geonode_urlpatterns

from . import views

router.register(r'nonspatialdatasets', views.NonSpatialDatasetViewSet, 'nonspatialdatasets')

geonode_urlpatterns += [
    url(r'^api/v2/', include(router.urls))
]

urlpatterns = [ 
    #url(r'^api/v2/', include(router.urls)),

    # path('<int:dataset_id>/data', views.get_dataset_data, name='get_dataset_data'),
    # path('<int:dataset_id>/export', views.export_dataset_data, name='export_dataset_data')
]
