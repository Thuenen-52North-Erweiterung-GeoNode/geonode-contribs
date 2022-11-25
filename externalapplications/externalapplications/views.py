import os
import json
import shutil
import logging
import warnings
import traceback
from django.urls import reverse
from django.conf import settings
from django.contrib import messages
from django.shortcuts import render, get_object_or_404
from django.forms.utils import ErrorList
from django.utils.translation import ugettext as _
from django.contrib.auth.decorators import login_required
from django.template import loader
from django.views.generic.edit import CreateView, UpdateView
from django.http import HttpResponse, HttpResponseRedirect, Http404
from django.core.exceptions import PermissionDenied, ObjectDoesNotExist
from geonode.base.api.exceptions import geonode_exception_handler

from geonode.client.hooks import hookset
from geonode.utils import mkdtemp, resolve_object
from geonode.base.views import batch_modify
from geonode.people.forms import ProfileForm
from geonode.base import register_event
from geonode.base.bbox_utils import BBOXHelper
from geonode.groups.models import GroupProfile
from geonode.monitoring.models import EventType
from geonode.storage.manager import storage_manager
from geonode.resource.manager import resource_manager
from geonode.decorators import check_keyword_write_perms
from geonode.security.utils import (
    get_user_visible_groups,
    AdvancedSecurityWorkflowManager)
from geonode.base.forms import (
    CategoryForm,
    TKeywordForm,
    ThesaurusAvailableForm)
from geonode.base.models import (
    Thesaurus,
    TopicCategory)
from .forms import (
    ExternalApplicationForm,
    ExternalApplicationCreateForm )
from .models import ExternalApplication

_PERMISSION_MSG_DELETE = _("You are not permitted to delete this external application")
_PERMISSION_MSG_GENERIC = _("You do not have permissions for this external application.")
_PERMISSION_MSG_MODIFY = _("You are not permitted to modify this external application")
_PERMISSION_MSG_METADATA = _(
    "You are not permitted to modify this external application's metadata")
_PERMISSION_MSG_VIEW = _("You are not permitted to view this external application")

logger = logging.getLogger(__name__)

@login_required
def create_external_application(request):
    template = "externalapplications/create_external_application.html"
    
    if request.method == "POST":
        
        form = ExternalApplicationCreateForm(request.POST)
        if form.is_valid():
            data = form.cleaned_data
            obj = ExternalApplication.objects.create(owner=request.user,
                url=data.get("url"), title=data.get("title"), abstract=data.get("abstract"),
                resource_type = 'externalapplication')
        return HttpResponseRedirect(reverse('external_application_metadata_detail', args=(obj.pk,)))
    else:
        form = ExternalApplicationCreateForm()
        result = render(request, template, {"form": form})
        return result



def _resolve_external_application(request, appid, permission='base.change_resourcebase',
                      msg=_PERMISSION_MSG_GENERIC, **kwargs):
    '''
    Resolve the external application by the provided primary key and check the optional permission.
    '''
    return resolve_object(request, ExternalApplication, {'pk': appid},
                          permission=permission, permission_msg=msg, **kwargs)

@login_required
@check_keyword_write_perms
def external_application_metadata(
        request,
        appid,
        template='external_applications/external_application_metadata.html',
        ajax=True):
    external_application = None
    try:
        external_application = _resolve_external_application(
            request,
            appid,
            'base.change_resourcebase_metadata',
            _PERMISSION_MSG_METADATA)
    except PermissionDenied:
        return HttpResponse(_("Not allowed"), status=403)
    except Exception:
        raise Http404(_("Not found"))
    if not external_application:
        raise Http404(_("Not found"))

    # Add metadata_author or poc if missing
    external_application.add_missing_metadata_author_or_poc()
    poc = external_application.poc
    metadata_author = external_application.metadata_author
    topic_category = external_application.category
    current_keywords = [keyword.name for keyword in external_application.keywords.all()]

    if request.method == "POST":
        external_application_form = ExternalApplicationForm(
            request.POST,
            instance=external_application,
            prefix="resource",
            user=request.user)
        category_form = CategoryForm(request.POST, prefix="category_choice_field", initial=int(
            request.POST["category_choice_field"]) if "category_choice_field" in request.POST and
            request.POST["category_choice_field"] else None)

        if hasattr(settings, 'THESAURUS'):
            tkeywords_form = TKeywordForm(request.POST)
        else:
            tkeywords_form = ThesaurusAvailableForm(request.POST, prefix='tkeywords')

    else:
        external_application_form = ExternalApplicationForm(instance=external_application, prefix="resource", user=request.user)
        external_application_form.disable_keywords_widget_for_non_superuser(request.user)
        category_form = CategoryForm(
            prefix="category_choice_field",
            initial=topic_category.id if topic_category else None)

        # Keywords from THESAURUS management
        ea_tkeywords = external_application.tkeywords.all()
        if hasattr(settings, 'THESAURUS') and settings.THESAURUS:
            warnings.warn('The settings for Thesaurus has been moved to Model, \
            this feature will be removed in next releases', DeprecationWarning)
            tkeywords_list = ''
            lang = 'en'  # TODO: use user's language
            if ea_tkeywords and len(ea_tkeywords) > 0:
                tkeywords_ids = ea_tkeywords.values_list('id', flat=True)
                if hasattr(settings, 'THESAURUS') and settings.THESAURUS:
                    el = settings.THESAURUS
                    thesaurus_name = el['name']
                    try:
                        t = Thesaurus.objects.get(identifier=thesaurus_name)
                        for tk in t.thesaurus.filter(pk__in=tkeywords_ids):
                            tkl = tk.keyword.filter(lang=lang)
                            if len(tkl) > 0:
                                tkl_ids = ",".join(
                                    map(str, tkl.values_list('id', flat=True)))
                                tkeywords_list += f",{tkl_ids}" if len(
                                    tkeywords_list) > 0 else tkl_ids
                    except Exception:
                        tb = traceback.format_exc()
                        logger.error(tb)

            tkeywords_form = TKeywordForm(instance=external_application)
        else:
            tkeywords_form = ThesaurusAvailableForm(prefix='tkeywords')
            #  set initial values for thesaurus form
            for tid in tkeywords_form.fields:
                values = []
                values = [keyword.id for keyword in ea_tkeywords if int(tid) == keyword.thesaurus.id]
                tkeywords_form.fields[tid].initial = values

    if request.method == "POST" and external_application_form.is_valid(
    ) and category_form.is_valid() and tkeywords_form.is_valid():
        new_poc = external_application_form.cleaned_data['poc']
        new_author = external_application_form.cleaned_data['metadata_author']
        new_keywords = current_keywords if request.keyword_readonly else external_application_form.cleaned_data['keywords']
        new_regions = external_application_form.cleaned_data['regions']

        new_category = None
        if category_form and 'category_choice_field' in category_form.cleaned_data and \
                category_form.cleaned_data['category_choice_field']:
            new_category = TopicCategory.objects.get(
                id=int(category_form.cleaned_data['category_choice_field']))

        if new_poc is None:
            if poc is None:
                poc_form = ProfileForm(
                    request.POST,
                    prefix="poc",
                    instance=poc)
            else:
                poc_form = ProfileForm(request.POST, prefix="poc")
            if poc_form.is_valid():
                if len(poc_form.cleaned_data['profile']) == 0:
                    # FIXME use form.add_error in django > 1.7
                    errors = poc_form._errors.setdefault(
                        'profile', ErrorList())
                    errors.append(
                        _('You must set a point of contact for this resource'))
            if poc_form.has_changed and poc_form.is_valid():
                new_poc = poc_form.save()

        if new_author is None:
            if metadata_author is None:
                author_form = ProfileForm(request.POST, prefix="author",
                                          instance=metadata_author)
            else:
                author_form = ProfileForm(request.POST, prefix="author")
            if author_form.is_valid():
                if len(author_form.cleaned_data['profile']) == 0:
                    # FIXME use form.add_error in django > 1.7
                    errors = author_form._errors.setdefault(
                        'profile', ErrorList())
                    errors.append(
                        _('You must set an author for this resource'))
            if author_form.has_changed and author_form.is_valid():
                new_author = author_form.save()

        external_application = external_application_form.instance
        resource_manager.update(
            external_application.uuid,
            instance=external_application,
            keywords=new_keywords,
            regions=new_regions,
            vals=dict(
                poc=new_poc or external_application.poc,
                metadata_author=new_author or external_application.metadata_author,
                category=new_category
            ),
            notify=True,
            extra_metadata=json.loads(external_application_form.cleaned_data['extra_metadata'])
        )

        resource_manager.set_thumbnail(external_application.uuid, instance=external_application, overwrite=False)
        external_application_form.save_many2many()

        register_event(request, EventType.EVENT_CHANGE_METADATA, external_application)
        url = hookset.external_application_detail_url(external_application)
        if not ajax:
            return HttpResponseRedirect(url)
        message = external_application.id

        try:
            # Keywords from THESAURUS management
            # Rewritten to work with updated autocomplete
            if not tkeywords_form.is_valid():
                return HttpResponse(json.dumps({'message': "Invalid thesaurus keywords"}, status_code=400))

            thesaurus_setting = getattr(settings, 'THESAURUS', None)
            if thesaurus_setting:
                tkeywords_data = tkeywords_form.cleaned_data['tkeywords']
                tkeywords_data = tkeywords_data.filter(
                    thesaurus__identifier=thesaurus_setting['name']
                )
                external_application.tkeywords.set(tkeywords_data)
            elif Thesaurus.objects.all().exists():
                fields = tkeywords_form.cleaned_data
                external_application.tkeywords.set(tkeywords_form.cleanx(fields))

        except Exception:
            tb = traceback.format_exc()
            logger.error(tb)

        vals = {}
        if 'group' in external_application_form.changed_data:
            vals['group'] = external_application_form.cleaned_data.get('group')
        if any([x in external_application_form.changed_data for x in ['is_approved', 'is_published']]):
            vals['is_approved'] = external_application_form.cleaned_data.get('is_approved', external_application.is_approved)
            vals['is_published'] = external_application_form.cleaned_data.get('is_published', external_application.is_published)
        resource_manager.update(
            external_application.uuid,
            instance=external_application,
            notify=True,
            vals=vals,
            extra_metadata=json.loads(external_application_form.cleaned_data['extra_metadata'])
        )
        return HttpResponse(json.dumps({'message': message}))
    elif request.method == "POST" and (not external_application_form.is_valid(
    ) or not category_form.is_valid() or not tkeywords_form.is_valid()):
        errors_list = {**external_application_form.errors.as_data(), **category_form.errors.as_data(), **tkeywords_form.errors.as_data()}
        logger.error(f"GeoApp Metadata form is not valid: {errors_list}")
        out = {
            'success': False,
            "errors": [f"{x}: {y[0].messages[0]}" for x, y in errors_list.items()]
        }
        return HttpResponse(
            json.dumps(out),
            content_type='application/json',
            status=400)
    # - POST Request Ends here -

    # Request.GET
    if poc is not None:
        external_application_form.fields['poc'].initial = poc.id
        poc_form = ProfileForm(prefix="poc")
        poc_form.hidden = True

    if metadata_author is not None:
        external_application_form.fields['metadata_author'].initial = metadata_author.id
        author_form = ProfileForm(prefix="author")
        author_form.hidden = True

    metadata_author_groups = get_user_visible_groups(request.user)

    if not AdvancedSecurityWorkflowManager.is_allowed_to_publish(request.user, external_application):
        external_application_form.fields['is_published'].widget.attrs.update({'disabled': 'true'})
    if not AdvancedSecurityWorkflowManager.is_allowed_to_approve(request.user, external_application):
        external_application_form.fields['is_approved'].widget.attrs.update({'disabled': 'true'})

    register_event(request, EventType.EVENT_VIEW_METADATA, external_application)
    return render(request, template, context={
        "resource": external_application,
        "external_application": external_application,
        "external_application_form": external_application_form,
        "poc_form": poc_form,
        "author_form": author_form,
        "category_form": category_form,
        "tkeywords_form": tkeywords_form,
        "metadata_author_groups": metadata_author_groups,
        "TOPICCATEGORY_MANDATORY": getattr(settings, 'TOPICCATEGORY_MANDATORY', False),
        "GROUP_MANDATORY_RESOURCES": getattr(settings, 'GROUP_MANDATORY_RESOURCES', False),
        "UI_MANDATORY_FIELDS": list(
            set(getattr(settings, 'UI_DEFAULT_MANDATORY_FIELDS', []))
            |
            set(getattr(settings, 'UI_REQUIRED_FIELDS', []))
        )
    })


@login_required
def external_application_metadata_advanced(request, appid):
    return external_application_metadata(
        request,
        appid,
        template='externalapplications/external_application_metadata_advanced.html')



def external_application_metadata_detail(
        request,
        appid,
        template='externalapplications/external_application_metadata_detail.html'):
    try:
        external_application = _resolve_external_application(
            request,
            appid,
            'view_resourcebase',
            _PERMISSION_MSG_METADATA)
    except PermissionDenied:
        return HttpResponse(_("Not allowed"), status=403)
    except Exception:
        raise Http404(_("Not found"))
    if not external_application:
        raise Http404(_("Not found"))

    group = None
    if external_application.group:
        try:
            group = GroupProfile.objects.get(slug=external_application.group.name)
        except ObjectDoesNotExist:
            group = None
    site_url = settings.SITEURL.rstrip('/') if settings.SITEURL.startswith('http') else settings.SITEURL
    register_event(request, EventType.EVENT_VIEW_METADATA, external_application)
    return render(request, template, context={
        "resource": external_application,
        "group": group,
        'SITEURL': site_url
    })
