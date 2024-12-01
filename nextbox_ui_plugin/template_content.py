from netbox.plugins import PluginTemplateExtension

class SiteTopologyButton(PluginTemplateExtension):
    """
    Extend the DCIM site template to include content from this plugin.
    """
    models = ['dcim.site']

    def buttons(self):
        return self.render('nextbox_ui_plugin/site_topo_button_4.x.html')

template_extensions = [SiteTopologyButton]
