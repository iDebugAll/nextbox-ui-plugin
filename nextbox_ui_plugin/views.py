#!./venv/bin/python

from django.shortcuts import render
from django.views.generic import View
from dcim.models import Cable, Device, Interface, DeviceRole
from ipam.models import VLAN
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

def get_vlan_topology(nb_devices_qs, vlans):

    topology_dict = {'nodes': [], 'links': []}
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
        primary_ip = ''
        if device.primary_ip:
            primary_ip = str(device.primary_ip.address)
        tags = [str(tag) for tag in device.tags.names()]
        for tag in tags:
            all_device_tags.add((tag, not tag_is_hidden(tag)))
        topology_dict['nodes'].append({
            'id': device.id,
            'name': device.name,
            'dcimDeviceLink': device_url,
            'primaryIP': primary_ip,
            'serial_number': device.serial,
            'model': device.device_type.model,
            'deviceRole': device.device_role.slug,
            'layerSortPreference': get_node_layer_sort_preference(
                device.device_role.slug
                ),
            'icon': get_icon_type(
                device.id
                ),
            'isPassive': device_is_passive,
            'tags': tags,
            })
        is_visible = not (device.device_role.slug in UNDISPLAYED_DEVICE_ROLE_SLUGS)
        device_roles.add((device.device_role.slug, device.device_role.name, is_visible))
    
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

                    topology_dict['links'].append({
                        'id': source_cable[1].id,
                        'source': source_cable[0].device.id,
                        'target': dest_cable[-1].device.id,
                        "srcIfName": if_shortname(source_cable[0].name),
                        "tgtIfName": if_shortname(dest_cable[-1].name),
                        })

    return topology_dict, device_roles, multi_cable_connections, list(all_device_tags)


def get_topology(nb_devices_qs):
    topology_dict = {'nodes': [], 'links': []}
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
        if nb_device.primary_ip:
            primary_ip = str(nb_device.primary_ip.address)
        tags = [str(tag) for tag in nb_device.tags.names()] or []
        tags = filter_tags(tags)
        for tag in tags:
            all_device_tags.add((tag, not tag_is_hidden(tag)))
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
            'dcimDeviceLink': device_url,
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
            # Include links to discovered devices only
            if link._termination_b_device_id in device_ids:
                links.append(link)
    device_roles = list(device_roles)
    device_roles.sort(key=lambda i: get_node_layer_sort_preference(i[0]))
    all_device_tags = list(all_device_tags)
    all_device_tags.sort()
    if not links:
        return topology_dict, device_roles, multi_cable_connections, list(all_device_tags)
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
    if NETBOX_CURRENT_VERSION >= version.parse("3.0"):
        template_name = 'nextbox_ui_plugin/topology_3.x.html'
    else:
        template_name = 'nextbox_ui_plugin/topology.html'

    def get(self, request):

        if not request.GET:
            self.queryset = Device.objects.none()
        elif 'saved_topology_id' in request.GET:
            self.queryset = Device.objects.none()

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
                topology_dict, device_roles, multi_cable_connections, device_tags = get_topology(self.queryset)
            else:
                topology_dict, device_roles, multi_cable_connections, device_tags = get_vlan_topology(self.queryset, vlans)

        return render(request, self.template_name, {
            'source_data': json.dumps(topology_dict),
            'display_unconnected': layout_context.get('displayUnconnected') or DISPLAY_UNCONNECTED,
            'device_roles': device_roles,
            'device_tags': device_tags,
            'undisplayed_roles': list(UNDISPLAYED_DEVICE_ROLE_SLUGS),
            'undisplayed_device_tags': list(UNDISPLAYED_DEVICE_TAGS),
            'display_logical_multicable_links': DISPLAY_LOGICAL_MULTICABLE_LINKS,
            'display_passive_devices': layout_context.get('displayPassiveDevices') or DISPLAY_PASSIVE_DEVICES,
            'initial_layout': INITIAL_LAYOUT,
            'filter_form': forms.TopologyFilterForm(
                layout_context.get('requestGET') or request.GET,
                label_suffix=''
            ),
            'load_saved_filter_form': forms.LoadSavedTopologyFilterForm(
                request.GET,
                label_suffix='',
                user=request.user
            ),
            'load_saved': SavedTopology.objects.all(), 
            'requestGET': dict(request.GET),
        })


class SiteTopologyView(TopologyView):
    if NETBOX_CURRENT_VERSION >= version.parse("3.0"):
        template_name = 'nextbox_ui_plugin/site_topology_3.x.html'
    else:
        template_name = 'nextbox_ui_plugin/site_topology.html'
