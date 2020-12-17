#!./venv/bin/python

from django.shortcuts import render
from django.views.generic import View
from dcim.models import Cable, Device, Interface
from django.contrib.auth.mixins import PermissionRequiredMixin
from django.conf import settings
from packaging import version
import json
import re

NETBOX_CURRENT_VERSION = version.parse(settings.VERSION)

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


DEFAULT_ICON_ROLE_MAP = {
    'border': 'router',
    'edge-switch': 'switch',
    'edge-router': 'router',
    'core-router': 'router',
    'core-switch': 'switch',
    'distribution': 'switch',
    'distribution-router': 'router',
    'distribution-switch': 'switch',
    'leaf': 'switch',
    'spine': 'switch',
    'access': 'switch',
    'access-switch': 'switch',
}


PLUGIN_SETTINGS = settings.PLUGINS_CONFIG.get("nextbox_ui_plugin", dict())

MANUAL_LAYERS_SORT_ORDER = PLUGIN_SETTINGS.get("layers_sort_order", "")
LAYERS_SORT_ORDER = MANUAL_LAYERS_SORT_ORDER or DEFAULT_LAYERS_SORT_ORDER

MANUAL_ICON_MODEL_MAP = PLUGIN_SETTINGS.get("icon_model_map", "")
ICON_MODEL_MAP = MANUAL_ICON_MODEL_MAP or DEFAULT_ICON_MODEL_MAP

MANUAL_ICON_ROLE_MAP = PLUGIN_SETTINGS.get("icon_role_map", "")
ICON_ROLE_MAP = MANUAL_ICON_ROLE_MAP or DEFAULT_ICON_ROLE_MAP

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

# Hide devices tagged with these tags
UNDISPLAYED_DEVICE_TAGS = PLUGIN_SETTINGS.get("undisplayed_device_tags", tuple())

# Filter device tags listed in Select Layers menu
SELECT_LAYERS_LIST_INCLUDE_DEVICE_TAGS = PLUGIN_SETTINGS.get("select_layers_list_include_device_tags", tuple())
SELECT_LAYERS_LIST_EXCLUDE_DEVICE_TAGS = PLUGIN_SETTINGS.get("select_layers_list_exclude_device_tags", tuple())

# Defines the initial layer alignment direction on the view
INITIAL_LAYOUT = PLUGIN_SETTINGS.get("INITIAL_LAYOUT", 'auto')
if INITIAL_LAYOUT not in ('vertical', 'horizontal', 'auto'):
    INITIAL_LAYOUT = 'auto'


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
    3. Based on Netbox device role and ICON_ROLE_MAP
    4. Default 'undefined'
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
    for role_slug, icon_type in ICON_ROLE_MAP.items():
        if str(nb_device.device_role.slug) == role_slug:
            return icon_type
    return 'unknown'


def tag_is_hidden(tag):
    for tag_regex in UNDISPLAYED_DEVICE_TAGS:
        if re.search(tag_regex, tag):
            return True
    return False


def filter_tags(tags):
    if not tags:
        return []
    if SELECT_LAYERS_LIST_INCLUDE_DEVICE_TAGS:
        filtered_tags = []
        for tag in tags:
            for tag_regex in SELECT_LAYERS_LIST_INCLUDE_DEVICE_TAGS:
                if re.search(tag_regex, tag):
                    filtered_tags.append(tag)
                    break
            if tag_is_hidden(tag):
                filtered_tags.append(tag)
        tags = filtered_tags
    if SELECT_LAYERS_LIST_EXCLUDE_DEVICE_TAGS:
        filtered_tags = []
        for tag in tags:
            for tag_regex in SELECT_LAYERS_LIST_EXCLUDE_DEVICE_TAGS:
                if re.search(tag_regex, tag) and not tag_is_hidden(tag):
                    break
            else:
                filtered_tags.append(tag)
        tags = filtered_tags
    return tags


def get_site_topology(site_id):
    topology_dict = {'nodes': [], 'links': []}
    device_roles = set()
    site_device_tags = set()
    multi_cable_connections = []
    if not site_id:
        return topology_dict, device_roles, multi_cable_connections, list(site_device_tags)
    nb_devices = Device.objects.filter(site_id=site_id)
    if not nb_devices:
        return topology_dict, device_roles, multi_cable_connections, list(site_device_tags)
    links = []
    device_ids = [d.id for d in nb_devices]
    for nb_device in nb_devices:
        device_is_passive = False
        primary_ip = ''
        if nb_device.primary_ip:
            primary_ip = str(nb_device.primary_ip.address)
        tags = [str(tag) for tag in nb_device.tags.names()] or []
        tags = filter_tags(tags)
        for tag in tags:
            site_device_tags.add((tag, not tag_is_hidden(tag)))
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
            'tags': tags,
        })
        is_visible = not (nb_device.device_role.slug in UNDISPLAYED_DEVICE_ROLE_SLUGS)
        device_roles.add((nb_device.device_role.slug, nb_device.device_role.name, is_visible))
        if not links_from_device:
            continue
        for link in links_from_device:
            # Include links to devices from the same Site only
            if link._termination_b_device_id in device_ids:
                links.append(link)
    device_roles = list(device_roles)
    device_roles.sort(key=lambda i: get_node_layer_sort_preference(i[0]))
    site_device_tags = list(site_device_tags)
    site_device_tags.sort()
    if not links:
        return topology_dict, device_roles, multi_cable_connections, list(site_device_tags)
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
        if not (isinstance(link.termination_a, Interface) or isinstance(link.termination_b, Interface)):
            # Skip trace if none of cable terminations is an Interface
            continue
        interface_side = None
        if isinstance(link.termination_a, Interface):
            interface_side = link.termination_a
        elif isinstance(link.termination_b, Interface):
            interface_side = link.termination_b
        trace_result = interface_side.trace()
        if not trace_result:
            continue
        if NETBOX_CURRENT_VERSION >= version.parse("2.10.1"):
            # Version 2.10.1 introduces some changes in cable trace behavior.
            cable_path = trace_result
        else:
            cable_path, *ignore = trace_result
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
            "srcIfName": if_shortname(cable_path[0][0].name),
            "tgtIfName": if_shortname(cable_path[-1][2].name),
            "isLogicalMultiCable": True,
        })
    return topology_dict, device_roles, multi_cable_connections, site_device_tags


class TopologyView(PermissionRequiredMixin, View):
    """Site Topology View"""
    permission_required = ('dcim.view_site', 'dcim.view_device', 'dcim.view_cable')

    def get(self, request, site_id):
        topology_dict, device_roles, multi_cable_connections, device_tags = get_site_topology(site_id)

        return render(request, 'nextbox_ui_plugin/site_topology.html', {
            'source_data': json.dumps(topology_dict),
            'display_unconnected': DISPLAY_UNCONNECTED,
            'device_roles': device_roles,
            'device_tags': device_tags,
            'undisplayed_roles': list(UNDISPLAYED_DEVICE_ROLE_SLUGS),
            'undisplayed_device_tags': list(UNDISPLAYED_DEVICE_TAGS),
            'display_logical_multicable_links': DISPLAY_LOGICAL_MULTICABLE_LINKS,
            'display_passive_devices': DISPLAY_PASSIVE_DEVICES,
            'initial_layout': INITIAL_LAYOUT,
        })
