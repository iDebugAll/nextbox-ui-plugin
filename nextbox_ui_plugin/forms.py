from django import forms
from django.utils.translation import gettext_lazy as _

from dcim.choices import *
from dcim.constants import *
from dcim.models import *
from extras.forms import LocalConfigContextFilterForm
from netbox.forms import NetBoxModelFilterSetForm
from tenancy.forms import ContactModelFilterForm, TenancyFilterForm
from utilities.forms import BOOLEAN_WITH_BLANK_CHOICES
from utilities.forms.fields import DynamicModelMultipleChoiceField, TagFilterField
from utilities.forms.rendering import FieldSet
from virtualization.models import Cluster, ClusterGroup

class TopologyFilterForm(
    LocalConfigContextFilterForm,
    TenancyFilterForm,
    ContactModelFilterForm,
    NetBoxModelFilterSetForm
):
    model = Device
    fieldsets = (
        FieldSet('q', 'filter_id', 'device_id', 'tag'),
        FieldSet('region_id', 'site_group_id', 'site_id', 'location_id', 'rack_id', name=_('Location')),
        FieldSet('status', 'role_id', name=_('Operation')),
        FieldSet('manufacturer_id', 'device_type_id', 'platform_id', name=_('Hardware')),
        FieldSet('tenant_group_id', 'tenant_id', name=_('Tenant')),
        FieldSet(
            'console_ports', 'console_server_ports', 'power_ports', 'power_outlets', 'interfaces', 'pass_through_ports',
            name=_('Components')
        ),
        FieldSet('cluster_group_id', 'cluster_id', name=_('Cluster')),
        FieldSet(
            'has_primary_ip', 'has_oob_ip', 'virtual_chassis_member', 'has_virtual_device_context',
            name=_('Miscellaneous')
        ),
        FieldSet('exclude_device_id', 'exclude_site', 'exclude_site_group', 'exclude_location', 'exclude_role', name=_('Exclude')),
        FieldSet('display_unconnected', 'display_passive', name=_('Topology Presentation Preferences')),
    )
    selector_fields = ('filter_id', 'q', 'region_id', 'site_group_id', 'site_id', 'location_id', 'rack_id')
    device_id = DynamicModelMultipleChoiceField(
        queryset=Device.objects.all(),
        to_field_name='id',
        required=False,
        null_option='None',
        label=_('Device')
    )
    region_id = DynamicModelMultipleChoiceField(
        queryset=Region.objects.all(),
        required=False,
        label=_('Region')
    )
    site_group_id = DynamicModelMultipleChoiceField(
        queryset=SiteGroup.objects.all(),
        required=False,
        label=_('Site group')
    )
    site_id = DynamicModelMultipleChoiceField(
        queryset=Site.objects.all(),
        required=False,
        query_params={
            'region_id': '$region_id',
            'group_id': '$site_group_id',
        },
        label=_('Site')
    )
    location_id = DynamicModelMultipleChoiceField(
        queryset=Location.objects.all(),
        required=False,
        null_option='None',
        query_params={
            'site_id': '$site_id'
        },
        label=_('Location')
    )
    rack_id = DynamicModelMultipleChoiceField(
        queryset=Rack.objects.all(),
        required=False,
        null_option='None',
        query_params={
            'site_id': '$site_id',
            'location_id': '$location_id',
        },
        label=_('Rack')
    )
    role_id = DynamicModelMultipleChoiceField(
        queryset=DeviceRole.objects.all(),
        required=False,
        label=_('Role')
    )
    manufacturer_id = DynamicModelMultipleChoiceField(
        queryset=Manufacturer.objects.all(),
        required=False,
        label=_('Manufacturer')
    )
    device_type_id = DynamicModelMultipleChoiceField(
        queryset=DeviceType.objects.all(),
        required=False,
        query_params={
            'manufacturer_id': '$manufacturer_id'
        },
        label=_('Model')
    )
    platform_id = DynamicModelMultipleChoiceField(
        queryset=Platform.objects.all(),
        required=False,
        null_option='None',
        label=_('Platform')
    )
    status = forms.MultipleChoiceField(
        label=_('Status'),
        choices=DeviceStatusChoices,
        required=False
    )
    has_primary_ip = forms.NullBooleanField(
        required=False,
        label=_('Has a primary IP'),
        widget=forms.Select(
            choices=BOOLEAN_WITH_BLANK_CHOICES
        )
    )
    has_oob_ip = forms.NullBooleanField(
        required=False,
        label=_('Has an OOB IP'),
        widget=forms.Select(
            choices=BOOLEAN_WITH_BLANK_CHOICES
        )
    )
    virtual_chassis_member = forms.NullBooleanField(
        required=False,
        label=_('Virtual chassis member'),
        widget=forms.Select(
            choices=BOOLEAN_WITH_BLANK_CHOICES
        )
    )
    console_ports = forms.NullBooleanField(
        required=False,
        label=_('Has console ports'),
        widget=forms.Select(
            choices=BOOLEAN_WITH_BLANK_CHOICES
        )
    )
    console_server_ports = forms.NullBooleanField(
        required=False,
        label=_('Has console server ports'),
        widget=forms.Select(
            choices=BOOLEAN_WITH_BLANK_CHOICES
        )
    )
    power_ports = forms.NullBooleanField(
        required=False,
        label=_('Has power ports'),
        widget=forms.Select(
            choices=BOOLEAN_WITH_BLANK_CHOICES
        )
    )
    power_outlets = forms.NullBooleanField(
        required=False,
        label=_('Has power outlets'),
        widget=forms.Select(
            choices=BOOLEAN_WITH_BLANK_CHOICES
        )
    )
    interfaces = forms.NullBooleanField(
        required=False,
        label=_('Has interfaces'),
        widget=forms.Select(
            choices=BOOLEAN_WITH_BLANK_CHOICES
        )
    )
    pass_through_ports = forms.NullBooleanField(
        required=False,
        label=_('Has pass-through ports'),
        widget=forms.Select(
            choices=BOOLEAN_WITH_BLANK_CHOICES
        )
    )
    has_virtual_device_context = forms.NullBooleanField(
        required=False,
        label=_('Has virtual device contexts'),
        widget=forms.Select(
            choices=BOOLEAN_WITH_BLANK_CHOICES
        )
    )
    cluster_id = DynamicModelMultipleChoiceField(
        queryset=Cluster.objects.all(),
        required=False,
        label=_('Cluster')
    )
    cluster_group_id = DynamicModelMultipleChoiceField(
        queryset=ClusterGroup.objects.all(),
        required=False,
        label=_('Cluster group')
    )
    tag = TagFilterField(model)
    # Exclude fields
    exclude_device_id = DynamicModelMultipleChoiceField(
        to_field_name='id',
        queryset=Device.objects.all(),
        required=False,
        label=_('Exclude Device')
    )
    exclude_site = DynamicModelMultipleChoiceField(
        queryset=Site.objects.all(),
        required=False,
        label=_('Exclude Site')
    )
    exclude_site_group = DynamicModelMultipleChoiceField(
        queryset=SiteGroup.objects.all(),
        required=False,
        label=_('Exclude Site Group')
    )
    exclude_location = DynamicModelMultipleChoiceField(
        queryset=Location.objects.all(),
        required=False,
        label=_('Exclude Location')
    )
    exclude_role = DynamicModelMultipleChoiceField(
        queryset=DeviceRole.objects.all(),
        required=False,
        label=_('Exclude Role')
    )
    # Plugin-specific fields
    display_unconnected = forms.NullBooleanField(
        required=False,
        label=_('Display Unconnected Devices'),
        widget=forms.Select(
            choices=BOOLEAN_WITH_BLANK_CHOICES
        )
    )
    display_passive = forms.NullBooleanField(
        required=False,
        label=_('Display Passive Devices'),
        widget=forms.Select(
            choices=BOOLEAN_WITH_BLANK_CHOICES
        )
    )
