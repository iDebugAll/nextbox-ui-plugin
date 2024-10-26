from netbox.plugins import PluginMenu, PluginMenuItem

menu = PluginMenu(
    label='Topology Viewer',
    icon_class='mdi mdi-map-search-outline',
    groups=(
        ('TOPOLOGY',
            (PluginMenuItem(
                link='plugins:nextbox_ui_plugin:topology',
                link_text='Topology',
                permissions = ('dcim.view_site', 'dcim.view_device', 'dcim.view_cable'),
            ),)
        ),
    ),
)
