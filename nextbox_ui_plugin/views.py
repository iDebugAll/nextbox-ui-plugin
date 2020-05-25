#!./venv/bin/python

from django.shortcuts import render
from django.views.generic import View
from dcim.models import Cable, Device, Interface
from django.contrib.auth.mixins import PermissionRequiredMixin
from django.conf import settings
import json


# Default NeXt UI icons
SUPPORTED_ICONS = {
    'switch',
    'router',
    'firewall',
    'wlc',
    'unknown',
    'server',
    'phone',
    'nexus5000',
    'ipphone',
    'host',
    'camera',
    'accesspoint',
    'groups',
    'groupm',
    'groupl',
    'cloud',
    'unlinked',
    'hostgroup',
    'wirelesshost',
}

# Topology layers would be sorted
# in the same descending order
# as in the tuple below.
# It is expected that Device Role
# slugs in Netbox exactly match
# values listed below.
# Update mapping to whatever you use.
DEFAULT_LAYERS_SORT_ORDER = (
    'undefined',
    'outside',
    'border',
    'edge',
    'edge-switch',
    'edge-router',
    'core',
    'core-router',
    'core-switch',
    'distribution',
    'distribution-router',
    'distribution-switch',
    'leaf',
    'spine',
    'access',
    'access-switch',
)


interface_full_name_map = {
    'Eth': 'Ethernet',
    'Fa': 'FastEthernet',
    'Gi': 'GigabitEthernet',
    'Te': 'TenGigabitEthernet',
}


DEFAULT_ICON_MODEL_MAP = {
    'CSR1000V': 'router',
    'Nexus': 'switch',
    'IOSXRv': 'router',
    'IOSv': 'switch',
    '2901': 'router',
    '2911': 'router',
    '2921': 'router',
    '2951': 'router',
    '4321': 'router',
    '4331': 'router',
    '4351': 'router',
    '4421': 'router',
    '4431': 'router',
    '4451': 'router',
    '2960': 'switch',
    '3750': 'switch',
    '3850': 'switch',
    'ASA': 'firewall',
}


PLUGIN_SETTINGS = settings.PLUGINS_CONFIG.get("nextbox_ui_plugin", dict())

MANUAL_LAYERS_SORT_ORDER = PLUGIN_SETTINGS.get("layers_sort_order", "")
LAYERS_SORT_ORDER = MANUAL_LAYERS_SORT_ORDER or DEFAULT_LAYERS_SORT_ORDER

MANUAL_ICON_MODEL_MAP = PLUGIN_SETTINGS.get("icon_model_map", "")
ICON_MODEL_MAP = MANUAL_ICON_MODEL_MAP or DEFAULT_ICON_MODEL_MAP

HIDE_UNCONNECTED = PLUGIN_SETTINGS.get("hide_unconnected", False)


def if_shortname(ifname):
    for k, v in interface_full_name_map.items():
        if ifname.startswith(v):
            return ifname.replace(v, k)
    return ifname


def get_node_layer_sort_preference(device_role):
    """Layer priority selection function
    Layer sort preference is designed as numeric value.
    This function identifies it by LAYERS_SORT_ORDER
    object position by default. With numeric values,
    the logic may be improved without changes on NeXt app side.
    0(null) results undefined layer position in NeXt UI.
    Valid indexes start with 1.
    """
    for i, role in enumerate(LAYERS_SORT_ORDER, start=1):
        if device_role == role:
            return i
    return 1


def get_icon_type(device_id):
    """
    Node icon getter function.
    Selection order:
    1. Based on 'icon_{icon_type}' tag in Netbox device
    2. Based on Netbox device type and ICON_MODEL_MAP
    3. Default 'undefined'
    """
    nb_device = Device.objects.get(id=device_id)
    if not nb_device:
        return 'unknown'
    for tag in nb_device.tags.names():
        if 'icon_' in tag:
            if tag.replace('icon_', '') in SUPPORTED_ICONS:
                return tag.replace('icon_', '')
    for model_base, icon_type in ICON_MODEL_MAP.items():
        if model_base in str(nb_device.device_type.model):
            return icon_type
    return 'unknown'


def get_site_topology(site_id):
    topology_dict = {'nodes': [], 'links': []}
    if not site_id:
        return topology_dict
    nb_devices = Device.objects.filter(site_id=site_id)
    if not nb_devices:
        return topology_dict
    links = []
    device_ids = [d.id for d in nb_devices]
    for nb_device in nb_devices:
        primary_ip = ''
        if nb_device.primary_ip:
            primary_ip = str(nb_device.primary_ip.address)
        topology_dict['nodes'].append({
            'id': nb_device.id,
            'name': nb_device.name,
            'primaryIP': primary_ip,
            'serial_number': nb_device.serial,
            'model': nb_device.device_type.model,
            'layerSortPreference': get_node_layer_sort_preference(
                nb_device.device_role.slug
            ),
            'icon': get_icon_type(
                nb_device.id
            ),
        })
        links_from_device = Cable.objects.filter(_termination_a_device_id=nb_device.id)
        if not links_from_device:
            continue
        for link in links_from_device:
            # Include links to devices from the same Site only
            if link._termination_b_device_id in device_ids:
                links.append(link)
    if not links:
        return topology_dict
    devices_seen = set()
    for link in links:
        nb_s_iface = Interface.objects.get(id=link.termination_a_id)
        nb_d_iface = Interface.objects.get(id=link.termination_b_id)
        s_node = nb_s_iface.device.id
        d_node = nb_d_iface.device.id
        
        devices_seen.add(link.termination_a.device.id)
        devices_seen.add(link.termination_b.device.id)
        
        topology_dict['links'].append({
            'id': link.id,
            'source': s_node,
            'target': d_node,
            "srcIfName": if_shortname(nb_s_iface.name),
            "tgtIfName": if_shortname(nb_d_iface.name)
        })
        
    if HIDE_UNCONNECTED:
        # Hide all devices that have no links
        topology_dict['nodes'] = [device for device in topology_dict['nodes'] if device['id'] in devices_seen]
        
    return topology_dict


class TopologyView(PermissionRequiredMixin, View):
    permission_required = ('dcim.view_site', 'dcim.view_device', 'dcim.view_cable')
    def get(self, request, site_id):
        return render(request, 'nextbox_ui_plugin/site_topology.html', {
            'source_data': json.dumps(get_site_topology(site_id))
        })
