from extras.plugins import PluginTemplateExtension
from django.conf import settings
from packaging import version

NETBOX_CURRENT_VERSION = version.parse(settings.VERSION)


class SiteTopologyButtons(PluginTemplateExtension):
    """
    Extend the DCIM site template to include content from this plugin.
    """
    model = 'dcim.site'

    def buttons(self):
        if NETBOX_CURRENT_VERSION >= version.parse("3.0"):
            return self.render('nextbox_ui_plugin/site_topo_button_3.x.html')
        else:
            return self.render('nextbox_ui_plugin/site_topo_button.html')


# PluginTemplateExtension subclasses must be packaged into an iterable named
# template_extensions to be imported by NetBox.
template_extensions = [SiteTopologyButtons]
