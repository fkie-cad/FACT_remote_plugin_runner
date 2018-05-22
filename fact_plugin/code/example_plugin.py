from analysis.RemotePluginBase import RemoteBasePlugin


class AnalysisPlugin(RemoteBasePlugin):
    NAME = 'example_plugin'
    DESCRIPTION = 'detects padding in file objects'
    VERSION = '0.1'
    FILE = __file__

    def __init__(self, plugin_administrator, config=None, recursive=True):
        super().__init__(plugin_administrator, config=config, recursive=recursive, plugin_path=__file__)
