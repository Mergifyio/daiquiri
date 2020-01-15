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
import datetime
import inspect
import logging
import logging.handlers
import numbers
import os
import sys
try:
    import syslog
except ImportError:
    syslog = None

from daiquiri import formatter
from daiquiri import handlers


def get_program_name():
    return os.path.basename(inspect.stack()[-1][1])


class Output(object):
    """Generic log output."""

    def __init__(self, handler, formatter=formatter.TEXT_FORMATTER,
                 level=None):
        self.handler = handler
        self.handler.setFormatter(formatter)
        if level is not None:
            self.handler.setLevel(level)

    def add_to_logger(self, logger):
        """Add this output to a logger."""
        logger.addHandler(self.handler)


def _get_log_file_path(logfile=None, logdir=None, program_name=None,
                       logfile_suffix=".log"):
    ret_path = None

    if not logdir:
        ret_path = logfile

    if not ret_path and logfile and logdir:
        ret_path = os.path.join(logdir, logfile)

    if not ret_path and logdir:
        program_name = program_name or get_program_name()
        ret_path = os.path.join(logdir, program_name) + logfile_suffix

    if not ret_path:
        raise ValueError("Unable to determine log file destination")

    return ret_path


class File(Output):
    """Ouput to a file."""

    def __init__(self, filename=None, directory=None, suffix=".log",
                 program_name=None, formatter=formatter.TEXT_FORMATTER,
                 level=None):
        """Log file output.

        :param filename: The log file path to write to.
        If directory is also specified, both will be combined.
        :param directory: The log directory to write to.
        If no filename is specified, the program name and suffix will be used
        to contruct the full path relative to the directory.
        :param suffix: The log file name suffix.
        This will be only used if no filename has been provided.
        :param program_name: Program name. Autodetected by default.
        """
        logpath = _get_log_file_path(filename, directory,
                                     program_name, suffix)
        handler = logging.handlers.WatchedFileHandler(logpath)
        super(File, self).__init__(handler, formatter, level)


class RotatingFile(Output):
    """Output to a file, rotating after a certain size."""

    def __init__(self, filename=None, directory=None, suffix='.log',
                 program_name=None, formatter=formatter.TEXT_FORMATTER,
                 level=None, max_size_bytes=0, backup_count=0):
        """Rotating log file output.

        :param filename: The log file path to write to.
        If directory is also specified, both will be combined.
        :param directory: The log directory to write to.
        If no filename is specified, the program name and suffix will be used
        to contruct the full path relative to the directory.
        :param suffix: The log file name suffix.
        This will be only used if no filename has been provided.
        :param program_name: Program name. Autodetected by default.
        :param max_size_bytes: allow the file to rollover at a
        predetermined size.
        :param backup_count: the maximum number of files to rotate
        logging output between.
        """
        logpath = _get_log_file_path(filename, directory,
                                     program_name, suffix)
        handler = logging.handlers.RotatingFileHandler(
            logpath, maxBytes=max_size_bytes, backupCount=backup_count)
        super(RotatingFile, self).__init__(handler, formatter, level)

    def do_rollover(self):
        """Manually forces a log file rotation."""
        return self.handler.doRollover()


class TimedRotatingFile(Output):
    """Rotating log file output, triggered by a fixed interval."""

    def __init__(self, filename=None, directory=None, suffix='.log',
                 program_name=None, formatter=formatter.TEXT_FORMATTER,
                 level=None, interval=datetime.timedelta(hours=24),
                 backup_count=0):
        """Rotating log file output, triggered by a fixed interval.

        :param filename: The log file path to write to.
        If directory is also specified, both will be combined.
        :param directory: The log directory to write to.
        If no filename is specified, the program name and suffix will be used
        to contruct the full path relative to the directory.
        :param suffix: The log file name suffix.
        This will be only used if no filename has been provided.
        :param program_name: Program name. Autodetected by default.
        :param interval: datetime.timedelta instance representing
        how often a new log file should be created.
        :param backup_count: the maximum number of files to rotate
        logging output between.
        """
        logpath = _get_log_file_path(filename, directory,
                                     program_name, suffix)
        handler = logging.handlers.TimedRotatingFileHandler(
            logpath,
            when='S',
            interval=self._timedelta_to_seconds(interval),
            backupCount=backup_count)
        super(TimedRotatingFile, self).__init__(handler, formatter, level)

    def do_rollover(self):
        """Manually forces a log file rotation."""
        return self.handler.doRollover()

    @staticmethod
    def _timedelta_to_seconds(td):
        """Convert a datetime.timedelta object into a seconds interval for
        rotating file ouput.

        :param td: datetime.timedelta
        :return: time in seconds
        :rtype: int
        """
        if isinstance(td, numbers.Real):
            td = datetime.timedelta(seconds=td)
        return td.total_seconds()


class Stream(Output):
    """Generic stream output."""

    def __init__(self, stream=sys.stderr, formatter=formatter.TEXT_FORMATTER,
                 level=None):
        super(Stream, self).__init__(handlers.TTYDetectorStreamHandler(stream),
                                     formatter, level)


STDERR = Stream()
STDOUT = Stream(sys.stdout)


class Journal(Output):
    def __init__(self, program_name=None,
                 formatter=formatter.TEXT_FORMATTER, level=None):
        program_name = program_name or get_program_name
        super(Journal, self).__init__(handlers.JournalHandler(program_name),
                                      formatter, level)


class Syslog(Output):
    def __init__(self, program_name=None, facility="user",
                 formatter=formatter.TEXT_FORMATTER, level=None):
        if syslog is None:
            # FIXME(jd) raise something more specific
            raise RuntimeError("syslog is not available on this platform")
        super(Syslog, self).__init__(
            handlers.SyslogHandler(
                program_name=program_name or get_program_name(),
                facility=self._find_facility(facility)),
            formatter, level)

    @staticmethod
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


class Datadog(Output):
    def __init__(self, hostname="127.0.0.1", port=10518,
                 formatter=formatter.DATADOG_FORMATTER, level=None):
        super(Datadog, self).__init__(
            handlers.PlainTextSocketHandler(hostname, port),
            formatter=formatter, level=level,
        )


preconfigured = {
    'stderr': STDERR,
    'stdout': STDOUT,
}

if syslog is not None:
    preconfigured['syslog'] = Syslog()

if handlers.journal is not None:
    preconfigured['journal'] = Journal()
