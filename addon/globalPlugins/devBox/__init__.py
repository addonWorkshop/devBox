from pathlib import Path

import addonHandler
import api
import config
import globalCommands
import globalPluginHandler
import nvwave
import scriptHandler
import speech
import textInfos
import ui

from . import interface
from .features.diff_sounds import DiffSoundsFeature
from .features.space_folding import SpaceFoldingFeature

config.conf.spec["devBox"] = {
    "features": {
        "diffSounds": "boolean(default=false)",
        "spaceFolding": "boolean(default=false)",
    },
}
ADDON_ROOT = Path(addonHandler.getCodeAddon().installPath).resolve()
SOUNDS_DIR = ADDON_ROOT / "media"
DIFF_SOUNDS = {
    "-": "diffLineDeleted.wav",
    "+": "diffLineInserted.wav",
}
DIFF_SOUNDS = {k: str(SOUNDS_DIR / v) for k, v in DIFF_SOUNDS.items()}


# We need this to get translations fromNVDA standard catalog.
gettext = _


addonHandler.initTranslation()


class GlobalPlugin(globalPluginHandler.GlobalPlugin):
    scriptCategory = "Dev Box"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.config = config.conf["devBox"]
        self._diff_sounds_enabled = False
        self.features = [SpaceFoldingFeature(self), DiffSoundsFeature(self)]
        self.sync_features()
        interface.add_settings(self.on_config_change)
        config.post_configProfileSwitch.register(self.on_profile_switch)

    def on_config_change(self):
        self.sync_features()

    def on_profile_switch(self):
        self.sync_features()

    def sync_features(self):
        [feature.sync() for feature in self.features]

    def terminate(self):
        [feature.terminate() for feature in self.features]
        interface.remove_settings()
        config.post_configProfileSwitch.unregister(self.on_profile_switch)

    @scriptHandler.script(
        description=gettext(
            "Moves the review cursor to the previous line of the current navigator object and speaks it",
        ),
        resumeSayAllMode=speech.sayAll.CURSOR.REVIEW,
        category=globalCommands.SCRCAT_TEXTREVIEW,
        gestures=("kb:numpad7", "kb(laptop):NVDA+upArrow", "ts(text):flickUp"),
    )
    def script_review_previous_line(self, gesture):
        result = globalCommands.commands.script_review_previousLine(gesture)
        self.report_diff_line_status()
        return result

    @scriptHandler.script(
        description=gettext(
            "Reports the line of the current navigator object where the review cursor is situated. "
            "If this key is pressed twice, the current line will be spelled. "
            "Pressing three times will spell the line using character descriptions.",
        ),
        category=globalCommands.SCRCAT_TEXTREVIEW,
        gestures=("kb:numpad8", "kb(laptop):NVDA+shift+."),
        speakOnDemand=True,
    )
    def script_review_currentLine(self, gesture):
        result = globalCommands.commands.script_review_currentLine(gesture)
        if scriptHandler.getLastScriptRepeatCount() == 0:
            self.report_diff_line_status()
        return result

    @scriptHandler.script(
        description=gettext(
            "Moves the review cursor to the next line of the current navigator object and speaks it",
        ),
        resumeSayAllMode=speech.sayAll.CURSOR.REVIEW,
        category=globalCommands.SCRCAT_TEXTREVIEW,
        gestures=("kb:numpad9", "kb(laptop):NVDA+downArrow", "ts(text):flickDown"),
    )
    def script_review_nextLine(self, gesture):
        result = globalCommands.commands.script_review_nextLine(gesture)
        self.report_diff_line_status()
        return result

    def report_diff_line_status(self):
        if not self._diff_sounds_enabled:
            return
        info = api.getReviewPosition().copy()
        info.expand(textInfos.UNIT_LINE)
        text = info.text
        if not text or text[0] not in DIFF_SOUNDS:
            return
        nvwave.playWaveFile(DIFF_SOUNDS[text[0]])

    @scriptHandler.script(description=_("Report current line length"))
    def script_report_current_line_length(self, gesture):
        obj = api.getCaretObject()
        text_info = obj.makeTextInfo(textInfos.POSITION_CARET)
        text_info.expand(textInfos.UNIT_LINE)
        line = text_info.text.rstrip("\r\n")
        ui.message(str(len(line)))
