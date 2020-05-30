#!./venv/bin/python

from django.shortcuts import render
from django.views.generic import View
from dcim.models import Cable, Device, Interface
from dcim.models.device_components import CableTermination
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

# Defines whether Devices with no connections
# are displayed on the topology view by default or not.
DISPLAY_UNCONNECTED = PLUGIN_SETTINGS.get("DISPLAY_UNCONNECTED", True)

# Defines whether logical links between end-devices for multi-cable hops
# are displayed in addition to the physical cabling on the topology view by default or not.
DISPLAY_LOGICAL_MULTICABLE_LINKS = PLUGIN_SETTINGS.get("DISPLAY_LOGICAL_MULTICABLE_LINKS", False)

# Defines whether passive devices
# are displayed on the topology view by default or not.
# Passive devices are patch pannels, power distribution units, etc.
DISPLAY_PASSIVE_DEVICES = PLUGIN_SETTINGS.get("DISPLAY_PASSIVE_DEVICES", False)

# Hide these roles by default
UNDISPLAYED_DEVICE_ROLE_SLUGS = PLUGIN_SETTINGS.get("undisplayed_device_role_slugs", tuple())


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
    device_roles = set()
    multi_cable_connections = []
    if not site_id:
        return topology_dict, device_roles, multi_cable_connections
    nb_devices = Device.objects.filter(site_id=site_id)
    if not nb_devices:
        return topology_dict, device_roles, multi_cable_connections
    links = []
    device_ids = [d.id for d in nb_devices]
    for nb_device in nb_devices:
        device_is_passive = False
        primary_ip = ''
        if nb_device.primary_ip:
            primary_ip = str(nb_device.primary_ip.address)
        links_from_device = Cable.objects.filter(_termination_a_device_id=nb_device.id)
        links_to_device = Cable.objects.filter(_termination_b_device_id=nb_device.id)
        if links_from_device:
            # Device is considered passive if it has no linked Interfaces.
            # Passive cabling devices use Rear and Front Ports.
            for link in links_from_device:
                if isinstance(link.termination_a, Interface) and link.termination_a.device.id == nb_device.id:
                    break
            else:
                device_is_passive = True
        if links_to_device:
            for link in links_to_device:
                if isinstance(link.termination_b, Interface) and link.termination_b.device.id == nb_device.id:
                    break
            else:
                device_is_passive = True
        topology_dict['nodes'].append({
            'id': nb_device.id,
            'name': nb_device.name,
            'primaryIP': primary_ip,
            'serial_number': nb_device.serial,
            'model': nb_device.device_type.model,
            'deviceRole': nb_device.device_role.slug,
            'layerSortPreference': get_node_layer_sort_preference(
                nb_device.device_role.slug
            ),
            'icon': get_icon_type(
                nb_device.id
            ),
            'isPassive': device_is_passive,
        })
        is_visible = not (nb_device.device_role.slug in UNDISPLAYED_DEVICE_ROLE_SLUGS)
        device_roles.add((nb_device.device_role.slug, nb_device.device_role.name, is_visible))
        if not links_from_device:
            continue
        for link in links_from_device:
            # Include links to devices from the same Site only
            if link._termination_b_device_id in device_ids:
                links.append(link)
    if not links:
        return topology_dict, device_roles, multi_cable_connections
    link_ids = set()
    for link in links:
        link_ids.add(link.id)
        topology_dict['links'].append({
            'id': link.id,
            'source': link.termination_a.device.id,
            'target': link.termination_b.device.id,
            "srcIfName": if_shortname(link.termination_a.name),
            "tgtIfName": if_shortname(link.termination_b.name)
        })
        cable_path, endpoint = link.termination_a.trace()
        # identify segmented cable paths between end-devices
        if len(cable_path) < 2:
            continue
        if isinstance(cable_path[0][0], Interface) and isinstance(cable_path[-1][2], Interface):
            if set([c[1] for c in cable_path]) in [set([c[1] for c in x]) for x in multi_cable_connections]:
                continue
            multi_cable_connections.append(cable_path)
    for cable_path in multi_cable_connections:
        link_id = max(link_ids) + 1  # dummy ID for a logical link
        link_ids.add(link_id)
        topology_dict['links'].append({
            'id': link_id,
            'source': cable_path[0][0].device.id,
            'target': cable_path[-1][2].device.id,
            "srcIfName": if_shortname(cable_path[-1][2].name),
            "tgtIfName": if_shortname(cable_path[-1][2].name),
            "isLogicalMultiCable": True,
        })
    return topology_dict, device_roles, multi_cable_connections


class TopologyView(PermissionRequiredMixin, View):
    """Site Topology View"""
    permission_required = ('dcim.view_site', 'dcim.view_device', 'dcim.view_cable')

    def get(self, request, site_id):
        topology_dict, device_roles, multi_cable_connections = get_site_topology(site_id)

        return render(request, 'nextbox_ui_plugin/site_topology.html', {
            'source_data': json.dumps(topology_dict),
            'display_unconnected': DISPLAY_UNCONNECTED,
            'device_roles': device_roles,
            'undisplayed_roles': list(UNDISPLAYED_DEVICE_ROLE_SLUGS),
            'display_logical_multicable_links': DISPLAY_LOGICAL_MULTICABLE_LINKS,
            'display_passive_devices': DISPLAY_PASSIVE_DEVICES,
        })
