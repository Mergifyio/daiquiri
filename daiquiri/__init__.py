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
import sys
try:
    import syslog
except ImportError:
    syslog = None
import traceback
import weakref

from daiquiri import handlers


class KeywordArgumentAdapter(logging.LoggerAdapter):
    """Logger adapter to add keyword arguments to log record's extra data

    Keywords passed to the log call are added to the "extra"
    dictionary passed to the underlying logger so they are emitted
    with the log message and available to the format string.

    Special keywords:

    extra
      An existing dictionary of extra values to be passed to the
      logger. If present, the dictionary is copied and extended.

    """

    def process(self, msg, kwargs):
        # Make a new extra dictionary combining the values we were
        # given when we were constructed and anything from kwargs.
        extra = self.extra.copy()
        if 'extra' in kwargs:
            extra.update(kwargs.pop('extra'))
        # Move any unknown keyword arguments into the extra
        # dictionary.
        for name in list(kwargs.keys()):
            if name == 'exc_info':
                continue
            extra[name] = kwargs.pop(name)
        extra['_daiquiri_extra'] = extra
        kwargs['extra'] = extra
        return msg, kwargs


_LOGGERS = weakref.WeakValueDictionary()


def getLogger(name=None, **kwargs):
    """Build a logger with the given name.

    :param name: The name for the logger. This is usually the module
                 name, ``__name__``.
    :type name: string
    """
    if name not in _LOGGERS:
        # NOTE(jd) Keep using the `adapter' variable here because so it's not
        # collected by Python since _LOGGERS contains only a weakref
        adapter = KeywordArgumentAdapter(logging.getLogger(name), kwargs)
        _LOGGERS[name] = adapter
    return _LOGGERS[name]


def _get_log_file_path(logfile=None, logdir=None, binary=None,
                       logfile_suffix=".log"):
    if not logdir:
        return logfile

    if logfile and logdir:
        return os.path.join(logdir, logfile)

    if logdir:
        binary = binary or handlers._get_binary_name()
        return os.path.join(logdir, binary) + logfile_suffix


def _find_facility(facility):
    # NOTE(jd): Check the validity of facilities at run time as they differ
    # depending on the OS and Python version being used.
    valid_facilities = [f for f in
                        ["LOG_KERN", "LOG_USER", "LOG_MAIL",
                         "LOG_DAEMON", "LOG_AUTH", "LOG_SYSLOG",
                         "LOG_LPR", "LOG_NEWS", "LOG_UUCP",
                         "LOG_CRON", "LOG_AUTHPRIV", "LOG_FTP",
                         "LOG_LOCAL0", "LOG_LOCAL1", "LOG_LOCAL2",
                         "LOG_LOCAL3", "LOG_LOCAL4", "LOG_LOCAL5",
                         "LOG_LOCAL6", "LOG_LOCAL7"]
                        if getattr(syslog, f, None)]

    facility = facility.upper()

    if not facility.startswith("LOG_"):
        facility = "LOG_" + facility

    if facility not in valid_facilities:
        raise TypeError('syslog facility must be one of: %s' %
                        ', '.join("'%s'" % fac
                                  for fac in valid_facilities))

    return getattr(syslog, facility)


DEFAULT_FORMAT = (
    "%(asctime)s [%(process)d] %(color)s%(levelname)s "
    "%(name)s: %(message)s%(color_stop)s"
)


def setup(debug=False,
          format=DEFAULT_FORMAT,
          date_format=None,
          use_journal=False, use_syslog=False,
          use_stderr=None,
          logfile=None, logdir=None, binary=None,
          syslog_facility="user"):
    """Setup Python logging.

    This will setup basic handlers for Python logging.

    :param debug: Enable debug log level
    :param format: The default log string format
    :param use_journal: Send log to journald
    :param use_syslog: Send log to syslog
    :param use_stderr: Write log to stderr
    If set to `None`, log will only be printed if all other log mechanism
    are disabled.
    :param logfile: The log file to write to.
    :param logdir: The log directory to write to.
    :param binary: Program name. Autodetected by default.
    :param syslog_facility: The syslog facility to use.
    """
    # Sometimes logging occurs before logging is ready
    # To avoid "No handlers could be found," temporarily log to sys.stderr.
    root_logger = logging.getLogger(None)
    if not root_logger.handlers:
        root_logger.addHandler(logging.StreamHandler())

    def logging_excepthook(exc_type, value, tb):
        logging.getLogger(binary).critical(
            "".join(traceback.format_exception_only(exc_type, value)))

    sys.excepthook = logging_excepthook

    # Remove all handlers
    for handler in list(root_logger.handlers):
        root_logger.removeHandler(handler)

    logpath = _get_log_file_path(logfile, logdir, binary)

    if logpath or use_journal:
        if use_journal:
            root_logger.addHandler(handlers.JournalHandler())
        if logpath:
            root_logger.addHandler(
                logging.handlers.WatchedFileHandler(logpath))
    else:
        streamlog = handlers.ColorStreamHandler(sys.stderr)
        root_logger.addHandler(streamlog)

    if use_syslog:
        if syslog is None:
            raise RuntimeError("syslog is not available on this platform")
        facility = _find_facility(syslog_facility)
        syslog_handler = handlers.SyslogHandler(facility=facility)
        root_logger.addHandler(syslog_handler)

    for handler in root_logger.handlers:
        handler.setFormatter(logging.Formatter(fmt=format,
                                               datefmt=date_format))

    if debug:
        root_logger.setLevel(logging.DEBUG)
    else:
        root_logger.setLevel(logging.INFO)
