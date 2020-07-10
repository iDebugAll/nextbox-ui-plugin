from extras.plugins import PluginConfig

class NextBoxUIConfig(PluginConfig):
    name = 'nextbox_ui_plugin'
    verbose_name = 'NextBox UI'
    description = 'Test'
    version = '0.6.2'
    author = 'Igor Korotchenkov'
    author_email = 'iDebugAll@gmail.com'
    base_url = 'nextbox-ui'
    required_settings = []
    default_settings = {}
    caching_config = {
        '*': None
    }

config = NextBoxUIConfig
