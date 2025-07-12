from .base import BaseFeature


class DiffSoundsFeature(BaseFeature):
    def __init__(self, global_plugin):
        super().__init__(global_plugin, "diffSounds")

    def enable(self):
        self.global_plugin._diff_sounds_enabled = True

    def disable(self):
        self.global_plugin._diff_sounds_enabled = False
