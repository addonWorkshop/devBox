import characterProcessing
import languageHandler
import speech

from .base import BaseFeature

SPACE = characterProcessing.processSpeechSymbol(languageHandler.getLanguage(), " ")
end_utterance_command = speech.commands.EndUtteranceCommand()


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


class SpaceFoldingFeature(BaseFeature):
    def __init__(self, global_plugin):
        super().__init__(global_plugin, "spaceFolding")

    def enable(self):
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

    def disable(self):
        speech._getSpellingSpeechWithoutCharMode = (
            self._speech__getSpellingSpeechWithoutCharMode
        )
        speech.speech._getSpellingSpeechWithoutCharMode = (
            self._speech_speech__getSpellingSpeechWithoutCharMode
        )
