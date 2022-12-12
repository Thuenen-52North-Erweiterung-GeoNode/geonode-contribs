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
import logging

from geonode.base.api.serializers import ResourceBaseSerializer

from ..models import NonSpatialDataset

logger = logging.getLogger(__name__)

class NonSpatialDatasetSerializer(ResourceBaseSerializer):

    def __init__(self, *args, **kwargs):
        # Instantiate the superclass normally
        super().__init__(*args, **kwargs)

    class Meta:
        model = NonSpatialDataset
        name = 'nonspatialdataset'
        view_name = 'nonspatialdatasets-list'
        fields = (
            'pk', 'uuid'#, 'name', 'subtype'
        )
