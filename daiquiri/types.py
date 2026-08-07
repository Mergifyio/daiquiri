import logging


class ColoredLogRecord(logging.LogRecord):
    color: str
    color_stop: str


class ExtrasLogRecord(logging.LogRecord):
    extras_prefix: str
    extras_suffix: str
    extras: str
    _daiquiri_extra_keys: set[str]


class TTYDetectionLogRecord(logging.LogRecord):
    _stream_is_a_tty: bool
