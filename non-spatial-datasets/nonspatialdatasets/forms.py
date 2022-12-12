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


from django import forms
from django.utils.translation import ugettext as _
from .models import NonSpatialDataset


class NonSpatialDatasetUploadForm(forms.Form):
    
    file = forms.FileField(
        label=_("Non-Spatial Dataset URL"),
        max_length=2000,
        widget=forms.FileInput(
            attrs={
                'size': '65',
                'class': 'inputText',
                'required': '',
                'type': 'file',

            }
        )
    )
        

class NonSpatialDatasetForm(forms.ModelForm):
    file = forms.FileField(
        label=_("Title"),
        max_length=2000,
        widget=forms.FileInput(
            attrs={
                'size': '65',
                'class': 'inputText',
                'required': '',
            }
        )
    )

    class Meta:
        model = NonSpatialDataset
        fields = (
            'file',
        )
