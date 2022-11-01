import django_filters
from dcim.models import Device, Site, Region
from django.conf import settings
from packaging import version
from dcim.models import Location



class TopologyFilterSet(django_filters.FilterSet):

    device_id = django_filters.ModelMultipleChoiceFilter(
        queryset=Device.objects.all(),
        to_field_name='id',
        field_name='id',
        label='Device (ID)',
    )
    location_id = django_filters.ModelMultipleChoiceFilter(
        queryset=Location.objects.all(),
        label='Location (ID)',
    )
    site_id = django_filters.ModelMultipleChoiceFilter(
        queryset=Site.objects.all(),
        label='Site (ID)',
    )
    region_id = django_filters.ModelMultipleChoiceFilter(
        queryset=Region.objects.all(),
        field_name='site__region',
        label='Region (ID)',
    )

    class Meta:
        model = Device
        fields = ['id', 'name', ]
