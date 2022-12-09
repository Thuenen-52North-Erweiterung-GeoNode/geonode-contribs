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
import os
import uuid
import json
import logging

from dynamic_rest.viewsets import DynamicModelViewSet
from dynamic_rest.filters import DynamicFilterBackend, DynamicSortingFilter

from rest_framework.decorators import action
from rest_framework.exceptions import APIException
from rest_framework.permissions import IsAuthenticatedOrReadOnly
from rest_framework.authentication import SessionAuthentication, BasicAuthentication
from oauth2_provider.contrib.rest_framework import OAuth2Authentication

from django.http import HttpResponse, JsonResponse
from django.contrib.auth import get_user_model
from django.core.exceptions import ObjectDoesNotExist
from django.core.files.storage import FileSystemStorage

from geonode.base.api.filters import DynamicSearchFilter, ExtentFilter
from geonode.base.api.pagination import GeoNodeApiPagination
from geonode.base.api.permissions import UserHasPerms

from .utils import extract_int_parameter, extract_string_parameter, parse_filters, parse_sorting
from .serializers import NonSpatialDatasetSerializer
from .permissions import NonSpatialDatasetPermissionsFilter
from ..models import NonSpatialDataset
from ..database.database import query_dataset
from ..coding.csv_encoder import encode_as_csv
from ..ingestion.ingest import ingest_zipped_dataset, register_dataset

logger = logging.getLogger(__name__)


class NonSpatialDatasetViewSet(DynamicModelViewSet):
    """
    API endpoint that allows non-spatial datasets to be viewed or edited.
    """
    http_method_names = ['get', 'post', 'delete']
    authentication_classes = [SessionAuthentication,
                              BasicAuthentication, OAuth2Authentication]
    permission_classes = [IsAuthenticatedOrReadOnly, UserHasPerms]
    filter_backends = [
        DynamicFilterBackend, DynamicSortingFilter, DynamicSearchFilter,
        ExtentFilter, NonSpatialDatasetPermissionsFilter
    ]
    queryset = NonSpatialDataset.objects.all().order_by('-last_updated')
    serializer_class = NonSpatialDatasetSerializer
    pagination_class = GeoNodeApiPagination

    def create(self, request, *args, **kwargs):
        try:
            return ingest_dataset(request)
        except Exception as e:
            raise APIException(e)

    @action(detail=True, methods=['get'])
    def data(self, request, pk=None):
        return get_dataset_data(request, pk)

    @action(detail=True, methods=['get'])
    def export(self, request, pk=None):
        return export_dataset_data(request, pk)


def ingest_dataset(request):
    ct = request.META.get('CONTENT_TYPE')

    if (ct and ct == "application/json"):
        data = request.data
        if not data:
            raise Exception("No POST body provided")
        params = register_dataset(data)
    else:
        payload_file = request.FILES['file']
        fs = FileSystemStorage()
        filename = fs.save(payload_file.name, payload_file)

        params = ingest_zipped_dataset(f"{fs.location}/{filename}")

    # TODO make the view with login_required
    admin_name = os.getenv("ADMIN_USERNAME", "admin")
    User = get_user_model()
    admin_user = User.objects.get(username=admin_name)

    obj = NonSpatialDataset.objects.create(owner=admin_user,
                                           column_definitions=json.dumps(
                                               params.column_definitions),
                                           postgres_url=params.postgres_url,
                                           internal_database_id=params.dataset_id,
                                           database_table=params.dataset_table,
                                           resource_type='dataset',
                                           subtype='nonspatial',
                                           name=params.dataset_name,
                                           uuid=str(uuid.uuid4()))

    return JsonResponse({"id": obj.id})


def get_dataset_data(request, dataset_id):
    try:
        nsd_obj = NonSpatialDataset.objects.get(id=dataset_id)
    except ObjectDoesNotExist:
        return JsonResponse({
            'status_code': 404,
            'error': 'The resource was not found'
        })

    params = request.GET
    size = extract_int_parameter(params, "size", 50)
    start = extract_int_parameter(params, "start", 0)

    f = parse_filters(params)
    s = parse_sorting(params)

    try:
        result = query_dataset(dataset_id=nsd_obj.internal_database_id, filters=f, start=start, size=size,
                               sort=s, connection_string=nsd_obj.postgres_url, database_table=nsd_obj.database_table)
    except Exception as e:
        return JsonResponse({
            'status_code': 500,
            'error': 'Internal Server Error: %s' % e
        })

    return JsonResponse(result, safe=False)


def export_dataset_data(request, dataset_id):
    try:
        nsd_obj = NonSpatialDataset.objects.get(id=dataset_id)
    except ObjectDoesNotExist:
        return JsonResponse({
            'status_code': 404,
            'error': 'The resource was not found'
        })

    params = request.GET
    f = extract_string_parameter(params, "format", "csv")

    if (f not in ["json", "csv"]):
        return JsonResponse({
            'status_code': 400,
            'error': f'Unsupported format: {f}'
        })

    size = 1000
    start = 0
    full_data = []
    try:
        result = query_dataset(dataset_id=nsd_obj.internal_database_id, start=start, size=size,
                               connection_string=nsd_obj.postgres_url, database_table=nsd_obj.database_table)
        while (len(result) > 0):
            full_data.extend(result)
            start += size
            result = query_dataset(dataset_id=nsd_obj.internal_database_id, start=start, size=size,
                                   connection_string=nsd_obj.postgres_url, database_table=nsd_obj.database_table)

    except Exception as e:
        return JsonResponse({
            'status_code': 500,
            'error': 'Internal Server Error: %s' % e
        })

    if (f == "json"):
        return JsonResponse(full_data, safe=False)
    elif (f == "csv"):
        return encode_csv(full_data)


def encode_csv(full_data):
    content = encode_as_csv(full_data)

    response = HttpResponse(content, content_type='text/csv')
    response['Content-Length'] = len(content)

    return response
