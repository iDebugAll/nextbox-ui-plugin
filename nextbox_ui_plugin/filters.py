import django_filters
from django.utils.translation import gettext as _

from extras.filtersets import LocalConfigContextFilterSet
from ipam.filtersets import PrimaryIPFilterSet
from ipam.models import IPAddress
from netbox.filtersets import NetBoxModelFilterSet
from tenancy.filtersets import TenancyFilterSet, ContactModelFilterSet
from tenancy.models import *
from utilities.filters import MultiValueCharFilter, TreeNodeMultipleChoiceFilter
from virtualization.models import Cluster, ClusterGroup
from dcim.choices import *
from dcim.constants import *
from dcim.models import *


class TopologyFilterSet(
    NetBoxModelFilterSet,
    TenancyFilterSet,
    ContactModelFilterSet,
    LocalConfigContextFilterSet,
    PrimaryIPFilterSet,
):
    device_id = django_filters.ModelMultipleChoiceFilter(
        queryset=Device.objects.all(),
        to_field_name='id',
        field_name='id',
        label='Device (ID)',
    )
    manufacturer_id = django_filters.ModelMultipleChoiceFilter(
        field_name='device_type__manufacturer',
        queryset=Manufacturer.objects.all(),
        label=_('Manufacturer (ID)'),
    )
    manufacturer = django_filters.ModelMultipleChoiceFilter(
        field_name='device_type__manufacturer__slug',
        queryset=Manufacturer.objects.all(),
        to_field_name='slug',
        label=_('Manufacturer (slug)'),
    )
    device_type = django_filters.ModelMultipleChoiceFilter(
        field_name='device_type__slug',
        queryset=DeviceType.objects.all(),
        to_field_name='slug',
        label=_('Device type (slug)'),
    )
    device_type_id = django_filters.ModelMultipleChoiceFilter(
        queryset=DeviceType.objects.all(),
        label=_('Device type (ID)'),
    )
    role_id = django_filters.ModelMultipleChoiceFilter(
        field_name='role_id',
        queryset=DeviceRole.objects.all(),
        label=_('Role (ID)'),
    )
    role = django_filters.ModelMultipleChoiceFilter(
        field_name='role__slug',
        queryset=DeviceRole.objects.all(),
        to_field_name='slug',
        label=_('Role (slug)'),
    )
    parent_device_id = django_filters.ModelMultipleChoiceFilter(
        field_name='parent_bay__device',
        queryset=Device.objects.all(),
        label=_('Parent Device (ID)'),
    )
    platform_id = django_filters.ModelMultipleChoiceFilter(
        queryset=Platform.objects.all(),
        label=_('Platform (ID)'),
    )
    platform = django_filters.ModelMultipleChoiceFilter(
        field_name='platform__slug',
        queryset=Platform.objects.all(),
        to_field_name='slug',
        label=_('Platform (slug)'),
    )
    region_id = TreeNodeMultipleChoiceFilter(
        queryset=Region.objects.all(),
        field_name='site__region',
        lookup_expr='in',
        label=_('Region (ID)'),
    )
    region = TreeNodeMultipleChoiceFilter(
        queryset=Region.objects.all(),
        field_name='site__region',
        lookup_expr='in',
        to_field_name='slug',
        label=_('Region (slug)'),
    )
    site_group_id = TreeNodeMultipleChoiceFilter(
        queryset=SiteGroup.objects.all(),
        field_name='site__group',
        lookup_expr='in',
        label=_('Site group (ID)'),
    )
    site_group = TreeNodeMultipleChoiceFilter(
        queryset=SiteGroup.objects.all(),
        field_name='site__group',
        lookup_expr='in',
        to_field_name='slug',
        label=_('Site group (slug)'),
    )
    site_id = django_filters.ModelMultipleChoiceFilter(
        queryset=Site.objects.all(),
        label=_('Site (ID)'),
    )
    site = django_filters.ModelMultipleChoiceFilter(
        field_name='site__slug',
        queryset=Site.objects.all(),
        to_field_name='slug',
        label=_('Site name (slug)'),
    )
    location_id = TreeNodeMultipleChoiceFilter(
        queryset=Location.objects.all(),
        field_name='location',
        lookup_expr='in',
        label=_('Location (ID)'),
    )
    rack_id = django_filters.ModelMultipleChoiceFilter(
        field_name='rack',
        queryset=Rack.objects.all(),
        label=_('Rack (ID)'),
    )
    parent_bay_id = django_filters.ModelMultipleChoiceFilter(
        field_name='parent_bay',
        queryset=DeviceBay.objects.all(),
        label=_('Parent bay (ID)'),
    )
    cluster_id = django_filters.ModelMultipleChoiceFilter(
        queryset=Cluster.objects.all(),
        label=_('VM cluster (ID)'),
    )
    cluster_group = django_filters.ModelMultipleChoiceFilter(
        field_name='cluster__group__slug',
        queryset=ClusterGroup.objects.all(),
        to_field_name='slug',
        label=_('Cluster group (slug)'),
    )
    cluster_group_id = django_filters.ModelMultipleChoiceFilter(
        field_name='cluster__group',
        queryset=ClusterGroup.objects.all(),
        label=_('Cluster group (ID)'),
    )
    model = django_filters.ModelMultipleChoiceFilter(
        field_name='device_type__slug',
        queryset=DeviceType.objects.all(),
        to_field_name='slug',
        label=_('Device model (slug)'),
    )
    name = MultiValueCharFilter(
        lookup_expr='iexact'
    )
    status = django_filters.MultipleChoiceFilter(
        choices=DeviceStatusChoices,
        null_value=None
    )
    has_primary_ip = django_filters.BooleanFilter(
        method='_has_primary_ip',
        label=_('Has a primary IP'),
    )
    has_oob_ip = django_filters.BooleanFilter(
        method='_has_oob_ip',
        label=_('Has an out-of-band IP'),
    )
    virtual_chassis_id = django_filters.ModelMultipleChoiceFilter(
        field_name='virtual_chassis',
        queryset=VirtualChassis.objects.all(),
        label=_('Virtual chassis (ID)'),
    )
    virtual_chassis_member = django_filters.BooleanFilter(
        method='_virtual_chassis_member',
        label=_('Is a virtual chassis member')
    )
    console_ports = django_filters.BooleanFilter(
        method='_console_ports',
        label=_('Has console ports'),
    )
    console_server_ports = django_filters.BooleanFilter(
        method='_console_server_ports',
        label=_('Has console server ports'),
    )
    power_ports = django_filters.BooleanFilter(
        method='_power_ports',
        label=_('Has power ports'),
    )
    power_outlets = django_filters.BooleanFilter(
        method='_power_outlets',
        label=_('Has power outlets'),
    )
    interfaces = django_filters.BooleanFilter(
        method='_interfaces',
        label=_('Has interfaces'),
    )
    pass_through_ports = django_filters.BooleanFilter(
        method='_pass_through_ports',
        label=_('Has pass-through ports'),
    )
    module_bays = django_filters.BooleanFilter(
        method='_module_bays',
        label=_('Has module bays'),
    )
    device_bays = django_filters.BooleanFilter(
        method='_device_bays',
        label=_('Has device bays'),
    )
    oob_ip_id = django_filters.ModelMultipleChoiceFilter(
        field_name='oob_ip',
        queryset=IPAddress.objects.all(),
        label=_('OOB IP (ID)'),
    )
    has_virtual_device_context = django_filters.BooleanFilter(
        method='_has_virtual_device_context',
        label=_('Has virtual device context'),
    )
    exclude_device_id = django_filters.ModelMultipleChoiceFilter(
        field_name='id',
        to_field_name='id',
        queryset=Device.objects.all(),
        label=_('Exclude Device'),
        method='filter_exclude_device_id'
    )
    exclude_site = django_filters.ModelMultipleChoiceFilter(
        field_name='site',
        queryset=Site.objects.all(),
        label=_('Exclude Site'),
        method='filter_exclude_site'
    )
    exclude_site_group = django_filters.ModelMultipleChoiceFilter(
        field_name='site__group',
        queryset=SiteGroup.objects.all(),
        label=_('Exclude Site Group'),
        method='filter_exclude_site_group'
    )
    exclude_location = django_filters.ModelMultipleChoiceFilter(
        field_name='location',
        queryset=Location.objects.all(),
        label=_('Exclude Location'),
        method='filter_exclude_location'
    )
    exclude_role = django_filters.ModelMultipleChoiceFilter(
        field_name='role',
        queryset=DeviceRole.objects.all(),
        label=_('Exclude Role'),
        method='filter_exclude_role'
    )

    class Meta:
        model = Device
        fields = (
            'id', 'asset_tag', 'face', 'position', 'latitude', 'longitude', 'airflow', 'vc_position', 'vc_priority',
            'description',
        )

    def search(self, queryset, name, value):
        if not value.strip():
            return queryset
        return queryset.filter(
            Q(name__icontains=value) |
            Q(serial__icontains=value.strip()) |
            Q(inventoryitems__serial__icontains=value.strip()) |
            Q(asset_tag__icontains=value.strip()) |
            Q(description__icontains=value.strip()) |
            Q(comments__icontains=value) |
            Q(primary_ip4__address__startswith=value) |
            Q(primary_ip6__address__startswith=value)
        ).distinct()

    def _has_primary_ip(self, queryset, name, value):
        params = Q(primary_ip4__isnull=False) | Q(primary_ip6__isnull=False)
        if value:
            return queryset.filter(params)
        return queryset.exclude(params)

    def _has_oob_ip(self, queryset, name, value):
        params = Q(oob_ip__isnull=False)
        if value:
            return queryset.filter(params)
        return queryset.exclude(params)

    def _virtual_chassis_member(self, queryset, name, value):
        return queryset.exclude(virtual_chassis__isnull=value)

    def _console_ports(self, queryset, name, value):
        return queryset.exclude(consoleports__isnull=value)

    def _console_server_ports(self, queryset, name, value):
        return queryset.exclude(consoleserverports__isnull=value)

    def _power_ports(self, queryset, name, value):
        return queryset.exclude(powerports__isnull=value)

    def _power_outlets(self, queryset, name, value):
        return queryset.exclude(poweroutlets__isnull=value)

    def _interfaces(self, queryset, name, value):
        return queryset.exclude(interfaces__isnull=value)

    def _pass_through_ports(self, queryset, name, value):
        return queryset.exclude(
            frontports__isnull=value,
            rearports__isnull=value
        )

    def _module_bays(self, queryset, name, value):
        return queryset.exclude(modulebays__isnull=value)

    def _device_bays(self, queryset, name, value):
        return queryset.exclude(devicebays__isnull=value)

    def _has_virtual_device_context(self, queryset, name, value):
        params = Q(vdcs__isnull=False)
        if value:
            return queryset.filter(params).distinct()
        return queryset.exclude(params)
    
    def filter_exclude_site(self, queryset, name, value):
        """
        Exclude devices belonging to the selected sites.
        """
        return queryset.exclude(site__in=value)
    
    def filter_exclude_device_id(self, queryset, name, value):
        """
        Exclude devices with selected IDs.
        """
        device_ids = [device.id for device in value]
        return queryset.exclude(id__in=device_ids)

    def filter_exclude_site_group(self, queryset, name, value):
        """
        Exclude devices belonging to the selected site groups.
        """
        return queryset.exclude(site__group__in=value)
    
    def filter_exclude_location(self, queryset, name, value):
        """
        Exclude devices belonging to the selected locations.
        """
        return queryset.exclude(location__in=value)
    
    def filter_exclude_role(self, queryset, name, value):
        """
        Exclude devices that have any of the selected roles.
        """
        return queryset.exclude(role__in=value)
