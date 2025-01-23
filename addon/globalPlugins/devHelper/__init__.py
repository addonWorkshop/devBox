from pathlib import Path

import addonHandler
import api
import characterProcessing
import globalCommands
import globalPluginHandler
import languageHandler
import nvwave
import scriptHandler
import speech
import textInfos

SOUNDS_DIR = Path(__file__).parent / "media"
DIFF_SOUNDS = {
    "-": "diffLineDeleted.wav",
    "+": "diffLineInserted.wav",
}
DIFF_SOUNDS = {k: str(SOUNDS_DIR / v) for k, v in DIFF_SOUNDS.items()}

SPACE = characterProcessing.processSpeechSymbol(languageHandler.getLanguage(), " ")
end_utterance_command = speech.commands.EndUtteranceCommand()

# We need this to get translations fromNVDA standard catalog.
gettext = _
addonHandler.initTranslation()


def get_spelling_speech_decorator(func):
    def wrapper(*args, **kwargs):
        original_commands = list(func(*args, **kwargs))
        new_commands = []
        spaces_buffer = []

        def flush_spaces_buffer():
            spaces_amount = len(spaces_buffer) // 2
            if spaces_amount < 2:
                new_commands.extend(spaces_buffer)
            else:
                new_commands.append(f"{spaces_amount} {SPACE}")
                new_commands.append(end_utterance_command)
            spaces_buffer.clear()

        cursor = 0
        while cursor < len(original_commands):
            command = original_commands[cursor]
            if isinstance(command, str) and command == SPACE:
                spaces_buffer.extend(original_commands[cursor : cursor + 2])
                cursor += 2  # Space and end utterance command
                continue
            flush_spaces_buffer()
            new_commands.append(command)
            cursor += 1
        flush_spaces_buffer()
        return new_commands

    return wrapper


class GlobalPlugin(globalPluginHandler.GlobalPlugin):
    scriptCategory = "Dev Helper"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._speech__getSpellingSpeechWithoutCharMode = (
            speech._getSpellingSpeechWithoutCharMode
        )
        speech._getSpellingSpeechWithoutCharMode = get_spelling_speech_decorator(
            speech._getSpellingSpeechWithoutCharMode
        )
        self._speech_speech__getSpellingSpeechWithoutCharMode = (
            speech.speech._getSpellingSpeechWithoutCharMode
        )
        speech.speech._getSpellingSpeechWithoutCharMode = get_spelling_speech_decorator(
            speech.speech._getSpellingSpeechWithoutCharMode
        )

    def terminate(self):
        speech._getSpellingSpeechWithoutCharMode = (
            self._speech__getSpellingSpeechWithoutCharMode
        )
        speech.speech._getSpellingSpeechWithoutCharMode = (
            self._speech_speech__getSpellingSpeechWithoutCharMode
        )

    @scriptHandler.script(
        description=gettext(
            # Translators: Input help mode message for move review cursor to previous line command.
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
            # Translators: Input help mode message for read current line under review cursor command.
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
            # Translators: Input help mode message for move review cursor to next line command.
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
        info = api.getReviewPosition().copy()
        info.expand(textInfos.UNIT_LINE)
        text = info.text
        if not text or text[0] not in DIFF_SOUNDS:
            return
        nvwave.playWaveFile(DIFF_SOUNDS[text[0]])
