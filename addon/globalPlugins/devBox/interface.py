import addonHandler
import config
import gui
from gui.nvdaControls import CustomCheckListBox

from .interface_helpers import (
    CheckListBoxToDictConverter,
    ConfigBoundSettingsPanel,
    bind_with_config,
)

addonHandler.initTranslation()


class DevBoxSettingsPanel(ConfigBoundSettingsPanel):
    title = addonHandler.getCodeAddon().manifest["summary"]

    def makeSettings(self, settings_sizer):
        self.config = config.conf["devBox"]
        sizer = gui.guiHelper.BoxSizerHelper(self, sizer=settings_sizer)
        # bind_with_config will try to check checkboxes, so let's add elements first
        features_list = sizer.addLabeledControl(
            _("Features"),
            CustomCheckListBox,
        )
        features_list.Append(_("Space folding"), "spaceFolding")
        features_list.Append(_("Diff sounds"), "diffSounds")
        self.feature_list = bind_with_config(
            features_list, "features", CheckListBoxToDictConverter
        )
        self.feature_list.SetSelection(0)


def add_settings(on_save_callback):
    DevBoxSettingsPanel.on_save_callback = on_save_callback
    gui.settingsDialogs.NVDASettingsDialog.categoryClasses.append(DevBoxSettingsPanel)


def remove_settings():
    gui.settingsDialogs.NVDASettingsDialog.categoryClasses.remove(DevBoxSettingsPanel)
