#########################################################################
#
# Copyright (C) 2017 OSGeo
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
import taggit

from django import forms
from django.core.exceptions import ValidationError
from django.utils.translation import ugettext as _
from .models import ExternalApplication

logger = logging.getLogger(__name__)


class ExternalApplicationCreateForm(forms.Form):
    title = forms.CharField(
        label=_("Title"),
        max_length=2000,
        widget=forms.TextInput(
            attrs={
                'size': '65',
                'class': 'inputText',
                'required': '',
            }
        )
    )
    abstract = forms.CharField(
        label=_("Abstract"),
        max_length=2000,
        widget=forms.TextInput(
            attrs={
                'size': '65',
                'class': 'inputText',
                'required': '',
            }
        )
    )
    url = forms.CharField(
        label=_("External Application URL"),
        max_length=2000,
        widget=forms.TextInput(
            attrs={
                'size': '65',
                'class': 'inputText',
                'required': '',
                'type': 'url',

            }
        )
    )
        

class ExternalApplicationForm(forms.ModelForm):
    title = forms.CharField(
        label=_("Title"),
        max_length=2000,
        widget=forms.TextInput(
            attrs={
                'size': '65',
                'class': 'inputText',
                'required': '',
            }
        )
    )
    abstract = forms.CharField(
        label=_("Abstract"),
        max_length=2000,
        widget=forms.TextInput(
            attrs={
                'size': '65',
                'class': 'inputText',
                'required': '',
            }
        )
    )
    url = forms.CharField(
        label=_("External Application URL"),
        max_length=2000,
        widget=forms.TextInput(
            attrs={
                'size': '65',
                'class': 'inputText',
                'required': '',
                'type': 'url',

            }
        )
    )
    keywords = taggit.forms.TagField(required=False)

    class Meta:
        model = ExternalApplication
        fields = (
            'title',
            'abstract',
            'url',
            'keywords',
        )
