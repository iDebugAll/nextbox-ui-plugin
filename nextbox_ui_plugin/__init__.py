from extras.plugins import PluginConfig

class NextBoxUIConfig(PluginConfig):
    name = 'nextbox_ui_plugin'
    verbose_name = 'NextBox UI'
    description = 'A topology visualization plugin for Netbox powered by NextUI Toolkit.'
    version = '0.9.1'
    author = 'Igor Korotchenkov'
    author_email = 'iDebugAll@gmail.com'
    base_url = 'nextbox-ui'
    required_settings = []
    default_settings = {}
    caching_config = {
        '*': None
    }

config = NextBoxUIConfig
