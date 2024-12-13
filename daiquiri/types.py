# flake8: noqa: A005
import logging
import typing


class ColoredLogRecord(logging.LogRecord):
    color: str
    color_stop: str


class ExtrasLogRecord(logging.LogRecord):
    extras_prefix: str
    extras_suffix: str
    extras: str
    _daiquiri_extra_keys: typing.Set[str]


class TTYDetectionLogRecord(logging.LogRecord):
    _stream_is_a_tty: bool
