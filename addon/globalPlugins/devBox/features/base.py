from abc import ABC, abstractmethod

import config
from globalPluginHandler import GlobalPlugin


class BaseFeature(ABC):
    def __init__(self, global_plugin, config_key):
        self.config_key = config_key
        self.global_plugin: GlobalPlugin = global_plugin
        self.is_enabled = False

    @property
    def features_config(self):
        return config.conf["devBox"]["features"]

    @property
    def should_be_enabled(self):
        return bool(self.features_config[self.config_key])

    def sync(self):
        if self.should_be_enabled:
            if not self.is_enabled:
                self._enable()
        else:
            if self.is_enabled:
                self._disable()

    def terminate(self):
        if self.is_enabled:
            self._disable()

    def _enable(self):
        self.enable()
        self.is_enabled = True

    def _disable(self):
        self.disable()
        self.is_enabled = False

    @abstractmethod
    def enable(self):
        pass

    @abstractmethod
    def disable(self):
        pass
