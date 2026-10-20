import datetime
from pathlib import Path

import addonHandler
import api
import config
import controlTypes
import globalCommands
import globalPluginHandler
import logHandler
import nvwave
import scriptHandler
import speech
import textInfos
import ui
from config.configFlags import LoggingLevel

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
            "Moves the review cursor to the top line of the current navigator object and speaks it",
        ),
        category=globalCommands.SCRCAT_TEXTREVIEW,
        gestures=("kb:shift+numpad7", "kb(laptop):NVDA+control+home"),
    )
    def script_review_top(self, gesture):
        result = globalCommands.commands.script_review_top(gesture)
        self.report_diff_line_status()
        return result

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

    @scriptHandler.script(
        description=gettext(
            "Moves the review cursor to the bottom line of the current navigator object and speaks it",
        ),
        category=globalCommands.SCRCAT_TEXTREVIEW,
        gestures=("kb:shift+numpad9", "kb(laptop):NVDA+control+end"),
    )
    def script_review_bottom(self, gesture):
        result = globalCommands.commands.script_review_bottom(gesture)
        self.report_diff_line_status()
        return result

    @scriptHandler.script(
        description=_("Moves the review cursor one screen up and speaks the line"),
        category=globalCommands.SCRCAT_TEXTREVIEW,
        gesture="kb:control+numpad7",
    )
    def script_review_previous_screen(self, gesture):
        self.switch_screen(-1)

    @scriptHandler.script(
        description=_("Moves the review cursor one screen down and speaks the line"),
        category=globalCommands.SCRCAT_TEXTREVIEW,
        gesture="kb:control+numpad9",
    )
    def script_review_next_screen(self, gesture):
        self.switch_screen(1)

    def switch_screen(self, direction):
        text_pattern = getattr(api.getNavigatorObject(), "UIATextPattern", None)
        visible_ranges = text_pattern.GetVisibleRanges() if text_pattern else None
        if not visible_ranges or not visible_ranges.length:
            lines_amount = 40
        else:
            lines_amount = len(visible_ranges.GetElement(0).GetBoundingRectangles()) // 4 - 1
        info = api.getReviewPosition().copy()
        info.expand(textInfos.UNIT_LINE)
        info.collapse()
        new_info = info.copy()
        moved = new_info.move(textInfos.UNIT_LINE, lines_amount * direction)
        new_info.expand(textInfos.UNIT_LINE)
        if moved == 0 or (direction == 1 and info.start == new_info.start):
            ui.reviewMessage(gettext("Top") if direction == -1 else gettext("Bottom"))
        else:
            api.setReviewPosition(new_info)
        speech.speakTextInfo(
            new_info,
            unit=textInfos.UNIT_LINE,
            reason=controlTypes.OutputReason.CARET,
        )
        self.report_diff_line_status()

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

    @scriptHandler.script(
        description=_("Report current second in a minute"),
        gesture="kb:nvda+control+f12",
    )
    def script_report_current_second(self, gesture):
        ui.message(str(datetime.datetime.now().second))

    @scriptHandler.script(description="Cycle logging level between info and debug (unredacted)")
    def script_cycle_logging_levels(self, gesture):
        if logHandler.isLogLevelForced():
            ui.message("logging level is forced and cannot be changed")
            return
        current_level_name = config.conf["general"]["loggingLevel"]
        current_level = LoggingLevel[current_level_name]
        target_level = (
            LoggingLevel.INFO
            if current_level is LoggingLevel.DEBUG_UNREDACTED
            else LoggingLevel.DEBUG_UNREDACTED
        )
        config.conf["general"]["loggingLevel"] = target_level.name
        logHandler.setLogLevelFromConfig()
        ui.message(target_level.name)
