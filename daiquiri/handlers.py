#    Licensed under the Apache License, Version 2.0 (the "License"); you may
#    not use this file except in compliance with the License. You may obtain
#    a copy of the License at
#
#         http://www.apache.org/licenses/LICENSE-2.0
#
#    Unless required by applicable law or agreed to in writing, software
#    distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
#    WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
#    License for the specific language governing permissions and limitations
#    under the License.

import logging
import logging.config
import logging.handlers
import os
import typing

try:
    from systemd import journal
except ImportError:
    journal = None


from daiquiri import types

# This is a copy of the numerical constants from syslog.h. The
# definition of these goes back at least 20 years, and is specifically
# 3 bits in a packed field, so these aren't likely to ever need
# changing.
SYSLOG_MAP = {
    "CRITICAL": 2,
    "ERROR": 3,
    "WARNING": 4,
    "WARN": 4,
    "INFO": 6,
    "DEBUG": 7,
}


_SYSLOG_PRIORITY_NAMES = {
    2: "crit",
    3: "err",
    4: "warning",
    6: "info",
    7: "debug",
}

# Local syslog sockets: Linux, macOS, FreeBSD.
_SYSLOG_SOCKETS = ("/dev/log", "/var/run/syslog", "/var/run/log")

# LOG_USER as the syslog module defines it: facilities there are shifted by 3
# bits, unlike logging.handlers.SysLogHandler's.
_SYSLOG_LOG_USER = logging.handlers.SysLogHandler.LOG_USER << 3


def _default_syslog_address() -> str | tuple[str, int]:
    for path in _SYSLOG_SOCKETS:
        if os.path.exists(path):
            return path
    return ("localhost", logging.handlers.SYSLOG_UDP_PORT)


class SyslogHandler(logging.handlers.SysLogHandler):
    """Syslog based handler.

    Each handler sends its messages with its own program name and facility:
    unlike syslog.openlog, nothing process-wide is changed, so several
    handlers with different facilities, and the application's own use of
    the syslog module, do not interfere.

    :param program_name: The identity prepended to each message.
    :param facility: A facility as defined by the syslog module, such as
                     syslog.LOG_AUTH. Defaults to LOG_USER.
    :param address: Where to send the messages: the path of a Unix socket or
                    a (host, port) tuple for UDP. Defaults to the first local
                    syslog socket found (/dev/log, /var/run/syslog,
                    /var/run/log), else localhost on UDP port 514.
    """

    def __init__(
        self,
        program_name: str,
        facility: int | None = None,
        address: str | tuple[str, int] | None = None,
    ) -> None:
        self.syslog_facility = facility if facility is not None else _SYSLOG_LOG_USER
        super().__init__(
            address=address if address is not None else _default_syslog_address(),
            facility=self.syslog_facility >> 3,
        )
        self.ident = f"{program_name}: "

    def mapPriority(self, levelName: str) -> str:
        return _SYSLOG_PRIORITY_NAMES[SYSLOG_MAP.get(levelName, 7)]


class JournalHandler(logging.Handler):
    """Journald based handler. Only available on platforms using systemd."""

    program_name: str

    def __init__(self, program_name: str) -> None:
        if not journal:
            raise RuntimeError("Systemd bindings do not exist")
        super().__init__()
        self.program_name = program_name

    def emit(self, record: logging.LogRecord) -> None:
        priority = SYSLOG_MAP.get(record.levelname, 7)
        message = self.format(record)

        extras = {
            "CODE_FILE": record.pathname,
            "CODE_LINE": record.lineno,
            "CODE_FUNC": record.funcName,
            "THREAD_NAME": record.threadName,
            "PROCESS_NAME": record.processName,
            "LOGGER_NAME": record.name,
            "LOGGER_LEVEL": record.levelname,
            "SYSLOG_IDENTIFIER": self.program_name,
            "PRIORITY": priority,
        }

        if record.exc_text:
            extras["EXCEPTION_TEXT"] = record.exc_text

        if record.exc_info:
            extras["EXCEPTION_INFO"] = record.exc_info

        if hasattr(record, "_daiquiri_extra_keys"):
            record = typing.cast(types.ExtrasLogRecord, record)
            for k in record._daiquiri_extra_keys:
                if k != "_daiquiri_extra_keys":
                    extras[k.upper()] = getattr(record, k)

        journal.send(message, **extras)


if typing.TYPE_CHECKING:
    _TTYDetectorStreamHandlerBase = logging.StreamHandler[typing.Any]
else:
    _TTYDetectorStreamHandlerBase = logging.StreamHandler


class TTYDetectorStreamHandler(_TTYDetectorStreamHandlerBase):
    """Stream handler that adds a hint in the record if the stream is a TTY."""

    def format(self, record: logging.LogRecord) -> str:
        record = typing.cast(types.TTYDetectionLogRecord, record)
        if hasattr(self.stream, "isatty"):
            try:
                record._stream_is_a_tty = self.stream.isatty()
            except ValueError:
                # Stream has been closed, usually during interpretor shutdown
                record._stream_is_a_tty = False
        else:
            record._stream_is_a_tty = False
        s = super().format(record)
        del record._stream_is_a_tty
        return s


class PlainTextSocketHandler(logging.handlers.SocketHandler):
    """Socket handler that uses format and encode the record."""

    def __init__(self, hostname: str, port: int, encoding: str = "utf-8") -> None:
        self.encoding = encoding
        super().__init__(hostname, port)

    def makePickle(self, record: logging.LogRecord) -> bytes:
        return self.format(record).encode(self.encoding) + b"\n"


class PlainTextDatagramHandler(logging.handlers.DatagramHandler):
    """Socket handler that uses format and encode the record."""

    def __init__(self, hostname: str, port: int, encoding: str = "utf-8") -> None:
        self.encoding = encoding
        super().__init__(hostname, port)

    def makePickle(self, record: logging.LogRecord) -> bytes:
        return self.format(record).encode(self.encoding) + b"\n"
