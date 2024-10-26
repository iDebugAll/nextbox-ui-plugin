#!./venv/bin/python

from django.shortcuts import render
from django.views.generic import View
from dcim.models import *
from ipam.models import *
from circuits.models import *
from .models import SavedTopology
from . import forms, filters
from django.contrib.auth.mixins import PermissionRequiredMixin
from django.conf import settings
from packaging import version
import json
import re


NETBOX_CURRENT_VERSION = version.parse(settings.VERSION)

# Default NeXt UI icons
SUPPORTED_ICONS = {
    'network.switch',
    'network.router',
    'network.firewall',
    'network.wlc',
    'network.unknown',
    'network.server',
    'network.phone',
    'network.nexus5000',
    'network.ipphone',
    'network.host',
    'network.camera',
    'network.accesspoint',
    'network.groups',
    'network.groupm',
    'network.groupl',
    'network.cloud',
    'network.unlinked',
    'network.hostgroup',
    'network.wirelesshost',
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
    'CSR1000V': 'network.router',
    'Nexus': 'network.switch',
    'IOSXRv': 'network.router',
    'IOSv': 'network.switch',
    '2901': 'network.router',
    '2911': 'network.router',
    '2921': 'network.router',
    '2951': 'network.router',
    '4321': 'network.router',
    '4331': 'network.router',
    '4351': 'network.router',
    '4421': 'network.router',
    '4431': 'network.router',
    '4451': 'network.router',
    '2960': 'network.switch',
    '3750': 'network.switch',
    '3850': 'network.switch',
    'ASA': 'network.firewall',
}


DEFAULT_ICON_ROLE_MAP = {
    'border': 'network.router',
    'edge-switch': 'network.switch',
    'edge-router': 'network.router',
    'core-router': 'network.router',
    'core-switch': 'network.switch',
    'distribution': 'network.switch',
    'distribution-router': 'network.router',
    'distribution-switch': 'network.switch',
    'leaf': 'network.switch',
    'spine': 'network.switch',
    'access': 'network.switch',
    'access-switch': 'network.switch',
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
if DISPLAY_UNCONNECTED not in (True, False):
    DISPLAY_UNCONNECTED = False

# Defines whether passive devices
# are displayed on the topology view by default or not.
# Passive devices are patch pannels, power distribution units, etc.
DISPLAY_PASSIVE_DEVICES = PLUGIN_SETTINGS.get("DISPLAY_PASSIVE_DEVICES", False)
if DISPLAY_PASSIVE_DEVICES not in (True, False):
    DISPLAY_PASSIVE_DEVICES = False

# Hide these roles by default
UNDISPLAYED_DEVICE_ROLE_SLUGS = PLUGIN_SETTINGS.get("undisplayed_device_role_slugs", tuple())

# Hide devices tagged with these tags
UNDISPLAYED_DEVICE_TAGS = PLUGIN_SETTINGS.get("undisplayed_device_tags", tuple())

# Filter device tags listed in Select Layers menu
SELECT_LAYERS_LIST_INCLUDE_DEVICE_TAGS = PLUGIN_SETTINGS.get("select_layers_list_include_device_tags", tuple())
SELECT_LAYERS_LIST_EXCLUDE_DEVICE_TAGS = PLUGIN_SETTINGS.get("select_layers_list_exclude_device_tags", tuple())

# Defines the initial layer alignment direction on the view
INITIAL_LAYOUT = PLUGIN_SETTINGS.get("INITIAL_LAYOUT", 'forceDirected')

if INITIAL_LAYOUT not in ('vertica', 'horizontal', 'layered', 'forceDirected', 'auto'):
    INITIAL_LAYOUT = 'forceDirected'

# Translate from legacy options
if INITIAL_LAYOUT == 'auto':
    INITIAL_LAYOUT = 'forceDirected'
elif INITIAL_LAYOUT in ('vertical', 'horizontal'):
    INITIAL_LAYOUT = 'layered'


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
    if NETBOX_CURRENT_VERSION >= version.parse("4.0.0"):
        device_role_obj = nb_device.role
    else:
        device_role_obj = nb_device.device_role
    if not nb_device:
        return 'unknown'
    for tag in nb_device.tags.names():
        if 'icon_' in tag:
            if tag.replace('icon_', 'network.') in SUPPORTED_ICONS:
                return tag.replace('icon_', 'network.')
    for model_base, icon_type in ICON_MODEL_MAP.items():
        if model_base in str(nb_device.device_type.model):
            if icon_type.startswith('network.'):
                return icon_type
            else:
                return f'network.{icon_type}'
    for role_slug, icon_type in ICON_ROLE_MAP.items():
        if str(device_role_obj.slug) == role_slug:
            if icon_type.startswith('network.'):
                return icon_type
            else:
                return f'network.{icon_type}'
    return 'network.unknown'


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

def get_vlan_topology(nb_devices_qs, vlans):

    topology_dict = {'nodes': [], 'edges': []}
    device_roles = set()
    all_device_tags = set()
    multi_cable_connections = []
    vlan = VLAN.objects.get(id=vlans)
    interfaces = vlan.get_interfaces()
    filtred_devices = [d.id for d in nb_devices_qs]
    filtred_interfaces = []
    for interface in interfaces:
        if interface.is_connectable:
            direct_device_id = interface.device.id
            interface_trace = interface.trace()
            if len(interface_trace) != 0:
                termination_b_iface = interface_trace[-1][-1]
                connected_device_id = termination_b_iface.device.id
                if (direct_device_id in filtred_devices) or (direct_device_id in filtred_devices):
                    filtred_interfaces.append(interface)

    

    devices = []
    for interface in filtred_interfaces:
        if interface.is_connectable:
            if interface.device not in devices:
                devices.append(interface.device)
            interface_trace = interface.trace()
            if len(interface_trace) != 0:
                termination_b_iface = interface_trace[-1][-1]
                if termination_b_iface.device not in devices:
                    devices.append(termination_b_iface.device)
         

    device_ids = [d.id for d in devices]
    for device in devices:
        device_is_passive = False
        device_url = device.get_absolute_url()
        if NETBOX_CURRENT_VERSION >= version.parse("4.0.0"):
            device_role_obj = device.role
        else:
            device_role_obj = device.device_role
        primary_ip = ''
        if device.primary_ip:
            primary_ip = str(device.primary_ip.address)
        tags = [str(tag) for tag in device.tags.names()]
        for tag in tags:
            all_device_tags.add((tag, not tag_is_hidden(tag)))
        topology_dict['nodes'].append({
            'id': device.name,
            'name': device.name,
            'label': {'text': device.name},
            'dcimDeviceLink': device_url,
            'primaryIP': primary_ip,
            'serial_number': device.serial,
            'model': device.device_type.model,
            'deviceRole': device_role_obj.slug,
            'layer': get_node_layer_sort_preference(
                device_role_obj.slug
                ),
            'iconName': get_icon_type(
                device.id
                ),
            'isPassive': device_is_passive,
            'tags': tags,
            })
        is_visible = not (device_role_obj.slug in UNDISPLAYED_DEVICE_ROLE_SLUGS)
        device_roles.add((device_role_obj.slug, device_role_obj.name, is_visible))
    
    mapped_links = []
    for interface in filtred_interfaces:
        if interface.is_connectable:
            interface_trace = interface.trace()
            if len(interface_trace) != 0:
                source_cable = interface_trace[0]
                dest_cable = interface_trace[-1]
                mapping_link = [source_cable[0].device.id,dest_cable[-1].device.id]
                if (mapping_link not in mapped_links) and (mapping_link.reverse() not in mapped_links):
                    mapped_links.append(mapping_link)

                    topology_dict['edges'].append({
                        'id': source_cable[1].id,
                        'dcimCableURL': source_cable[1].get_absolute_url(),
                        'label': f"Cable {source_cable[1].id}",
                        'source': source_cable[0].device.name,
                        'target': dest_cable[-1].device.name,
                        'sourceDeviceName': source_cable[0].device.name,
                        'targetDeviceName': dest_cable[-1].device.name,
                        "srcIfName": if_shortname(source_cable[0].name),
                        "tgtIfName": if_shortname(dest_cable[-1].name),
                        })

    return topology_dict, device_roles, multi_cable_connections, list(all_device_tags)


def get_topology(nb_devices_qs, params):
    display_unconnected = params.get('display_unconnected')
    display_passive = params.get('display_passive')
    topology_dict = {'nodes': [], 'edges': []}
    device_roles = set()
    all_device_tags = set()
    multi_cable_connections = []
    if not nb_devices_qs:
        return topology_dict, device_roles, multi_cable_connections, list(all_device_tags)
    links = []
    device_ids = [d.id for d in nb_devices_qs]
    for nb_device in nb_devices_qs:
        device_is_passive = False
        device_url = nb_device.get_absolute_url()
        primary_ip = ''
        if NETBOX_CURRENT_VERSION >= version.parse("4.0.0"):
            device_role_obj = nb_device.role
        else:
            device_role_obj = nb_device.device_role
        if nb_device.primary_ip:
            primary_ip = str(nb_device.primary_ip.address)
        tags = [str(tag) for tag in nb_device.tags.names()] or []
        tags = filter_tags(tags)
        for tag in tags:
            all_device_tags.add((tag, not tag_is_hidden(tag)))
        # Device is considered passive if it has no linked Interfaces.
        # Passive cabling devices use Rear and Front Ports.
        links_from_device = Cable.objects.filter(terminations__cable_end='A', terminations___device_id=nb_device.id)
        links_to_device = Cable.objects.filter(terminations__cable_end='B', terminations___device_id=nb_device.id)
        interfaces_found = False
        if links_from_device:
            for link in links_from_device:
                for ab_link in link.a_terminations + link.b_terminations:
                    if isinstance(ab_link, Interface) and ab_link.device.id == nb_device.id:
                        interfaces_found = True
                        break
        if links_to_device:
            for link in links_to_device:
                for ab_link in link.a_terminations + link.b_terminations:
                    if isinstance(ab_link, Interface) and ab_link.device.id == nb_device.id:
                        interfaces_found = True
                        break
        if links_to_device or links_from_device:
            device_is_passive = not interfaces_found
        
        if not (links_from_device or links_to_device):
            divice_is_unconnected = True
        else:
            divice_is_unconnected = False

        if display_unconnected is False and divice_is_unconnected:
            continue

        node_data = {
            'id': nb_device.name,
            'name': nb_device.name,
            'label': {'text': nb_device.name},
            'dcimDeviceLink': device_url,
            'primaryIP': primary_ip,
            'serial_number': nb_device.serial,
            'model': nb_device.device_type.model,
            'deviceRole': device_role_obj.slug,
            'layer': get_node_layer_sort_preference(
                device_role_obj.slug
            ),
            'iconName': get_icon_type(
                nb_device.id
            ),
            'isPassive': device_is_passive,
            'isUnconnected': divice_is_unconnected,
            'tags': tags,
        }

        if display_passive:
            is_visible = not (device_role_obj.slug in UNDISPLAYED_DEVICE_ROLE_SLUGS)
            device_roles.add((device_role_obj.slug, device_role_obj.name, is_visible))
            topology_dict['nodes'].append(node_data)
        elif not display_passive and not device_is_passive:
            is_visible = not (device_role_obj.slug in UNDISPLAYED_DEVICE_ROLE_SLUGS)
            device_roles.add((device_role_obj.slug, device_role_obj.name, is_visible))
            topology_dict['nodes'].append(node_data)

        if not links_from_device:
            continue
        for link in links_from_device:
            # Exclude PowerFeed-connected links
            if (isinstance(link.a_terminations[0], PowerFeed) or (isinstance(link.b_terminations[0], PowerFeed))):
                continue
            # Exclude CircuitTermination-connected links
            if (isinstance(link.a_terminations[0], CircuitTermination) or (isinstance(link.b_terminations[0], CircuitTermination))):
                continue
            # Include links to discovered devices only
            if link.b_terminations[0].device_id in device_ids:
                links.append(link)

    device_roles = list(device_roles)
    device_roles.sort(key=lambda i: get_node_layer_sort_preference(i[0]))
    all_device_tags = list(all_device_tags)
    all_device_tags.sort()
    if not links:
        return topology_dict, device_roles, multi_cable_connections, list(all_device_tags)
    link_ids = set()
    for link in links:
        interface_to_interface = isinstance(link.a_terminations[0], Interface) and isinstance(link.b_terminations[0], Interface)
        at_least_one_interface = isinstance(link.a_terminations[0], Interface) or isinstance(link.b_terminations[0], Interface)
        link_url = link.get_absolute_url()
        edge_data = {
            'label': f"Cable {link.id}",
            'dcimCableURL': link_url,
            'source': link.a_terminations[0].device.name,
            'target': link.b_terminations[0].device.name,
            "sourceInterfaceLabel": if_shortname(link.a_terminations[0].name),
            "targetInterfaceLabel": if_shortname(link.b_terminations[0].name)
        }
        if display_passive:
            link_ids.add(link.id)
            topology_dict['edges'].append(edge_data)

        if not display_passive and interface_to_interface:
            link_ids.add(link.id)
            topology_dict['edges'].append(edge_data)

        if not at_least_one_interface:
            # Skip trace if none of cable terminations is an Interface
            continue
        if display_passive:
            # Do not calculate logical links if passive devices are displayed
            continue
        interface_side = None
        if isinstance(link.a_terminations[0], Interface):
            interface_side = link.a_terminations[0]
        elif isinstance(link.b_terminations[0], Interface):
            interface_side = link.b_terminations[0]
        trace_result = interface_side.trace()
        if not trace_result:
            continue
        cable_path = trace_result
        # identify segmented cable paths between end-devices
        if len(cable_path) < 2:
            continue
        if isinstance(cable_path[0][0][0], Interface) and isinstance(cable_path[-1][2][0], Interface):
            if set([c[1][0] for c in cable_path]) in [set([c[1][0] for c in x]) for x in multi_cable_connections]:
                continue
            multi_cable_connections.append(cable_path)
    for cable_path in multi_cable_connections:
        topology_dict['edges'].append({
            'source': cable_path[0][0][0].device.name,
            'target': cable_path[-1][2][0].device.name,
            "sourceInterfaceLabel": if_shortname(cable_path[0][0][0].name),
            "targetInterfaceLabel": if_shortname(cable_path[-1][2][0].name),
            "isLogicalMultiCable": True,
        })
    return topology_dict, device_roles, multi_cable_connections, all_device_tags


def get_saved_topology(id):
    topology_dict = {}
    device_roles = []
    device_tags = []
    device_roles_detailed = []
    device_tags_detailed = []
    layout_context = {}
    topology_data = SavedTopology.objects.get(id=id)
    if not topology_data:
        return topology_dict, device_roles, device_tags, layout_context
    topology_dict = dict(topology_data.topology)
    if 'nodes' not in topology_dict:
        return topology_dict, device_roles, device_tags, layout_context
    device_roles = list(set([str(d.get('deviceRole')) for d in topology_dict['nodes'] if d.get('deviceRole')]))
    for device_role in device_roles:
        is_visible = not (device_role in UNDISPLAYED_DEVICE_ROLE_SLUGS)
        device_role_obj = DeviceRole.objects.get(slug=device_role)
        if not device_role_obj:
            device_roles_detailed.append((device_role, device_role, is_visible))
            continue
        device_roles_detailed.append((device_role_obj.slug, device_role_obj.name, is_visible))
    device_roles_detailed.sort(key=lambda i: get_node_layer_sort_preference(i[0]))
    device_tags = set()
    for device in topology_dict['nodes']:
        if 'tags' not in device:
            continue
        for tag in device['tags']:
            device_tags.add(str(tag))
    device_tags = list(device_tags)
    device_tags_detailed = list([(tag, not tag_is_hidden(tag)) for tag in device_tags])
    layout_context = dict(topology_data.layout_context)
    return topology_dict, device_roles_detailed, device_tags_detailed, layout_context


class TopologyView(PermissionRequiredMixin, View):
    """Generic Topology View"""
    permission_required = ('dcim.view_site', 'dcim.view_device', 'dcim.view_cable')
    queryset = Device.objects.all()
    filterset = filters.TopologyFilterSet
    template_name = 'nextbox_ui_plugin/topology_4.x.html'

    def get(self, request):

        if not request.GET:
            self.queryset = Device.objects.none()
        elif 'saved_topology_id' in request.GET:
            self.queryset = Device.objects.none()

        display_unconnected = request.GET.get('display_unconnected')
        if display_unconnected is not None:
            display_unconnected = display_unconnected.lower == 'true'

        display_passive = request.GET.get('display_passive')
        if display_passive is not None:
            display_passive = display_passive.lower() == 'true'
        else:
            display_passive = DISPLAY_PASSIVE_DEVICES

        params = {
            'display_unconnected': display_unconnected,
            'display_passive': display_passive,
        }

        saved_topology_id = request.GET.get('saved_topology_id')
        layout_context = {}

        if saved_topology_id is not None:
            topology_dict, device_roles, device_tags, layout_context = get_saved_topology(saved_topology_id)
        else:
            vlans = []
            if 'vlan_id' in request.GET:
                clean_request = request.GET.copy()
                clean_request.pop('vlan_id')
                vlans = request.GET.get('vlan_id')
            else:
                clean_request = request.GET.copy()

            self.queryset = self.filterset(clean_request, self.queryset).qs
            if len(vlans) == 0:
                topology_dict, device_roles, multi_cable_connections, device_tags = get_topology(self.queryset, params)
            else:
                topology_dict, device_roles, multi_cable_connections, device_tags = get_vlan_topology(self.queryset, vlans)

        return render(request, self.template_name, {
            'source_data': json.dumps(topology_dict),
            'initial_layout': INITIAL_LAYOUT,
            'filter_form': forms.TopologyFilterForm(
                request.GET,
                label_suffix=''
            ),
            'model': Device,
            'requestGET': dict(request.GET),
        })
