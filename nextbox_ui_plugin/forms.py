from django import forms
from utilities.forms import (
    BootstrapMixin, DynamicModelMultipleChoiceField,
)
from .models import SavedTopology
from dcim.models import Device, Site, Region
from django.conf import settings
from packaging import version

NETBOX_CURRENT_VERSION = version.parse(settings.VERSION)

if NETBOX_CURRENT_VERSION >= version.parse("2.11.0"):
    from dcim.models import Location
else:
    from dcim.models import RackGroup as Location


class TopologyFilterForm(BootstrapMixin, forms.Form):

    model = Device

    device_id = DynamicModelMultipleChoiceField(
        queryset=Device.objects.all(),
        to_field_name='id',
        required=False,
        null_option='None',
    )
    location_id = DynamicModelMultipleChoiceField(
        queryset=Location.objects.all(),
        required=False,
        to_field_name='id',
        null_option='None',
    )
    site_id = DynamicModelMultipleChoiceField(
        queryset=Site.objects.all(),
        required=False,
        to_field_name='id',
        null_option='None',
    )
    region_id = DynamicModelMultipleChoiceField(
        queryset=Region.objects.all(),
        required=False,
        to_field_name='id',
        null_option='None',
    )


class LoadSavedTopologyFilterForm(BootstrapMixin, forms.Form):

    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user', None)
        super(LoadSavedTopologyFilterForm, self).__init__(*args, **kwargs)
        self.fields['saved_topology_id'].queryset = SavedTopology.objects.filter(created_by=user)

    model = SavedTopology

    saved_topology_id = forms.ModelChoiceField(
        queryset=None,
        to_field_name='id',
        required=True
    )
