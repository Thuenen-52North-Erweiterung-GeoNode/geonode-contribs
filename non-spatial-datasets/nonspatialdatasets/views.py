import os
import uuid
import json

from django.conf import settings
from django.urls import reverse
from django.shortcuts import render
from django.http import HttpResponse, HttpResponseRedirect, Http404
from django.core.exceptions import PermissionDenied, ObjectDoesNotExist
from django.contrib.auth.decorators import login_required
from django.utils.translation import ugettext as _

from geonode.base import register_event
from geonode.groups.models import GroupProfile
from geonode.monitoring.models import EventType
from geonode.utils import mkdtemp, resolve_object
from geonode.resource.manager import resource_manager
from geonode.storage.manager import storage_manager

from .models import NonSpatialDataset
from .forms import NonSpatialDatasetUploadForm
from .ingestion.ingest import ingest_zipped_dataset


_PERMISSION_MSG_GENERIC = _("You do not have permissions for this non-spatial dataset.")
_PERMISSION_MSG_METADATA = _(
    "You are not permitted to modify this non-spatial dataset's metadata")

@login_required
def non_spatial_dataset_upload(request):
    template = "nonspatialdatasets/non_spatial_dataset_upload.html"
    
    if request.method == "POST":
        
        form = NonSpatialDatasetUploadForm(request.POST, request.FILES)
        if form.is_valid():
            if form.files and form.files["file"]:
                file = form.files["file"]
                tempdir = mkdtemp()
                dirname = os.path.basename(tempdir)
                filepath = storage_manager.save(f"{dirname}/{file.name}", file)
                storage_path = storage_manager.path(filepath)
                params = ingest_zipped_dataset(zip_file=storage_path)

                obj = NonSpatialDataset.objects.create(owner=request.user,
                                           column_definitions=json.dumps(
                                               params.column_definitions),
                                           postgres_url=params.postgres_url,
                                           internal_database_id=params.dataset_id,
                                           database_table=params.dataset_table,
                                           resource_type='dataset',
                                           subtype='nonspatial',
                                           name=params.dataset_name,
                                           uuid=str(uuid.uuid4()))

                obj.set_missing_info()
                resource_manager.set_permissions(None, instance=obj, permissions=None, created=True)
            
                # FIXME namespace
                return HttpResponseRedirect(reverse('non_spatial_dataset_metadata_detail', args=(obj.pk,)))

            raise Exception("missing 'file' in form data")
        raise Exception("invalid form data")
    else:
        form = NonSpatialDatasetUploadForm()
        result = render(request, template, {"form": form})
        return result


def _resolve_non_spatial_dataset(request, datasetid, permission='base.change_resourcebase',
                      msg=_PERMISSION_MSG_GENERIC, **kwargs):
    '''
    Resolve the non-spatial dataset by the provided primary key and check the optional permission.
    '''
    return resolve_object(request, NonSpatialDataset, {'pk': datasetid},
                          permission=permission, permission_msg=msg, **kwargs)

def non_spatial_dataset_metadata_detail(
        request,
        datasetid,
        template='nonspatialdatasets/non_spatial_dataset_metadata_detail.html'):
    try:
        non_spatial_dataset = _resolve_non_spatial_dataset(
            request,
            datasetid,
            'view_resourcebase',
            _PERMISSION_MSG_METADATA)
    except PermissionDenied:
        return HttpResponse(_("Not allowed"), status=403)
    except Exception:
        raise Http404(_("Not found"))
    if not non_spatial_dataset:
        raise Http404(_("Not found"))

    group = None
    if non_spatial_dataset.group:
        try:
            group = GroupProfile.objects.get(slug=non_spatial_dataset.group.name)
        except ObjectDoesNotExist:
            group = None
    site_url = settings.SITEURL.rstrip('/') if settings.SITEURL.startswith('http') else settings.SITEURL
    register_event(request, EventType.EVENT_VIEW_METADATA, non_spatial_dataset)
    return render(request, template, context={
        "resource": non_spatial_dataset,
        "group": group,
        'SITEURL': site_url
    })