#!./venv/bin/python

from django.shortcuts import render
from django.views.generic import View
from dcim.models import *
from ipam.models import *
from circuits.models import *
from extras.models import SavedFilter
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

        # Filter out cables with incomplete terminations
        links_from_device = [c for c in links_from_device if (c.a_terminations and c.b_terminations)]
        links_to_device = [c for c in links_to_device if (c.a_terminations and c.b_terminations)]
        
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
            'id': f'device-{nb_device.id}',
            'name': nb_device.name,
            'label': nb_device.name,
            'layer': get_node_layer_sort_preference(
                device_role_obj.slug
            ),
            'iconName': get_icon_type(
                nb_device.id
            ),
            'isPassive': device_is_passive,
            'isUnconnected': divice_is_unconnected,
            'tags': tags,
            'customAttributes': {
                'name': nb_device.name,
                'model': nb_device.device_type.model,
                'serialNumber': nb_device.serial,
                'deviceRole': device_role_obj.name,
                'primaryIP': primary_ip,
                'dcimDeviceLink': device_url,
            }
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
            "label": f"Cable {link.id}",
            "source": f"device-{link.a_terminations[0].device.id}",
            "target": f"device-{link.b_terminations[0].device.id}",
            "sourceInterface": link.a_terminations[0].name,
            "sourceInterfaceLabel": {'text': if_shortname(link.a_terminations[0].name)},
            "targetInterface": link.b_terminations[0].name,
            "targetInterfaceLabel": {'text': if_shortname(link.b_terminations[0].name)},
            "customAttributes": {
                "name": f"Cable {link.id}",
                "dcimCableURL": link_url,
                "source": link.a_terminations[0].device.name,
                "target": link.b_terminations[0].device.name,
            }
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

        side_a_interface = cable_path[0][0]
        side_b_interface = cable_path[-1][2]
        if not (side_a_interface and side_b_interface):
            continue
        else:
            side_a_interface = side_a_interface[0]
            side_b_interface = side_b_interface[0]

        if isinstance(side_a_interface, Interface) and isinstance(side_b_interface, Interface):
            if set([c[1][0] for c in cable_path]) in [set([c[1][0] for c in x]) for x in multi_cable_connections]:
                continue
            multi_cable_connections.append(cable_path)
    for cable_path in multi_cable_connections:
        source_device_id = f"device-{side_a_interface.device.id}"
        target_device_id = f"device-{side_b_interface.device.id}"
        topology_dict['edges'].append({
            "source": source_device_id,
            "target": target_device_id,
            "sourceInterface": link.a_terminations[0].name,
            "sourceInterfaceLabel": {'text': if_shortname(link.a_terminations[0].name)},
            "targetInterface": link.b_terminations[0].name,
            "targetInterfaceLabel": {'text': if_shortname(link.b_terminations[0].name)},
            "isLogicalMultiCable": True,
            "customAttributes": {
                "name": f"Multi-Cable Connection",
                "dcimCableURL": f"/dcim/interfaces/{side_a_interface.id}/trace/",
                "source": side_a_interface.device.name,
                "target": side_b_interface.device.name,
            }
        })
    return topology_dict, device_roles, multi_cable_connections, all_device_tags


class TopologyView(PermissionRequiredMixin, View):
    """Generic Topology View"""
    permission_required = ('dcim.view_site', 'dcim.view_device', 'dcim.view_cable')
    queryset = Device.objects.all()
    filterset = filters.TopologyFilterSet
    template_name = 'nextbox_ui_plugin/topology_4.x.html'

    def get(self, request):

        clean_request = request.GET.copy()

        if not clean_request:
            self.queryset = Device.objects.none()

        self.queryset = self.filterset(clean_request, self.queryset).qs

        saved_filter = None
        if 'filter_id' in clean_request and clean_request['filter_id']:
            filter_id = clean_request['filter_id']
            saved_filter = SavedFilter.objects.get(pk=filter_id)

        if saved_filter:
            # Extract only plugin-specific filters from the SavedFilter.
            # All NetBox-native filters are handled by filtersets.
            display_unconnected = saved_filter.parameters.get('display_unconnected', [DISPLAY_UNCONNECTED])[0]
            display_passive = saved_filter.parameters.get('display_passive', [DISPLAY_PASSIVE_DEVICES])[0]
        else:
            display_unconnected = DISPLAY_UNCONNECTED
            display_passive = DISPLAY_PASSIVE_DEVICES

        if clean_request.get('display_unconnected') is not None:
            display_unconnected = clean_request.get('display_unconnected')

        if clean_request.get('display_passive') is not None:
            display_passive = clean_request.get('display_passive')

        params = {
            'display_unconnected': str(display_unconnected).lower() == 'true',
            'display_passive': str(display_passive).lower() == 'true',
        }

        topology_dict, device_roles, multi_cable_connections, device_tags = get_topology(self.queryset, params)

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
