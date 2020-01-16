# -*- coding: utf-8 -*-
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

try:
    from systemd import journal
except ImportError:
    journal = None
try:
    import syslog
except ImportError:
    syslog = None


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


class SyslogHandler(logging.Handler):
    """Syslog based handler. Only available on UNIX-like platforms."""

    def __init__(self, program_name, facility=None):
        # Default values always get evaluated, for which reason we avoid
        # using 'syslog' directly, which may not be available.
        facility = facility if facility is not None else syslog.LOG_USER
        if not syslog:
            raise RuntimeError("Syslog not available on this platform")
        super(SyslogHandler, self).__init__()
        syslog.openlog(program_name, 0, facility)

    def emit(self, record):
        priority = SYSLOG_MAP.get(record.levelname, 7)
        message = self.format(record)
        syslog.syslog(priority, message)


class JournalHandler(logging.Handler):
    """Journald based handler. Only available on platforms using systemd."""

    def __init__(self, program_name):
        if not journal:
            raise RuntimeError("Systemd bindings do not exist")
        super(JournalHandler, self).__init__()
        self.program_name = program_name

    def emit(self, record):
        priority = SYSLOG_MAP.get(record.levelname, 7)
        message = self.format(record)

        extras = {
            'CODE_FILE': record.pathname,
            'CODE_LINE': record.lineno,
            'CODE_FUNC': record.funcName,
            'THREAD_NAME': record.threadName,
            'PROCESS_NAME': record.processName,
            'LOGGER_NAME': record.name,
            'LOGGER_LEVEL': record.levelname,
            'SYSLOG_IDENTIFIER': self.program_name,
            'PRIORITY': priority
        }

        if record.exc_text:
            extras['EXCEPTION_TEXT'] = record.exc_text

        if record.exc_info:
            extras['EXCEPTION_INFO'] = record.exc_info

        if hasattr(record, "_daiquiri_extra_keys"):
            for k, v in record._daiquiri_extra_keys:
                if k != "_daiquiri_extra_keys":
                    extras[k.upper()] = getattr(record, k)

        journal.send(message, **extras)


class TTYDetectorStreamHandler(logging.StreamHandler):
    """Stream handler that adds a hint in the record if the stream is a TTY."""

    def format(self, record):
        if hasattr(self.stream, "isatty"):
            try:
                record._stream_is_a_tty = self.stream.isatty()
            except ValueError:
                # Stream has been closed, usually during interpretor shutdown
                record._stream_is_a_tty = False
        else:
            record._stream_is_a_tty = False
        s = super(TTYDetectorStreamHandler, self).format(record)
        del record._stream_is_a_tty
        return s


class PlainTextSocketHandler(logging.handlers.SocketHandler):
    """Socket handler that uses format and encode the record."""

    def __init__(self, hostname, port, encoding="utf-8"):
        self.encoding = encoding
        super(PlainTextSocketHandler, self).__init__(hostname, port)

    def makePickle(self, record):
        return self.format(record).encode(self.encoding) + b"\n"
