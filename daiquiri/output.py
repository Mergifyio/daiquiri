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
import os
import sys
import typing

try:
    import syslog
except ImportError:
    syslog = None  # type: ignore[assignment]

from daiquiri import formatter
from daiquiri import handlers


def get_program_name() -> str:
    """Return the name of the running program."""
    return os.path.basename(inspect.stack()[-1][1])


class Output:
    """Generic log output."""

    def __init__(
        self,
        handler: logging.Handler,
        formatter: logging.Formatter = formatter.TEXT_FORMATTER,
        level: typing.Optional[int] = None,
    ):
        self.handler = handler
        self.handler.setFormatter(formatter)
        if level is not None:
            self.handler.setLevel(level)

    def add_to_logger(self, logger: logging.Logger) -> None:
        """Add this output to a logger."""
        logger.addHandler(self.handler)


def _get_log_file_path(
    logfile: typing.Optional[str] = None,
    logdir: typing.Optional[str] = None,
    program_name: typing.Optional[str] = None,
    logfile_suffix: str = ".log",
) -> str:
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

    def __init__(
        self,
        filename: typing.Optional[str] = None,
        directory: typing.Optional[str] = None,
        suffix: str = ".log",
        program_name: typing.Optional[str] = None,
        formatter: logging.Formatter = formatter.TEXT_FORMATTER,
        level: typing.Optional[int] = None,
    ):
        """Log file output.

        :param filename: The log file path to write to. If directory is also
                         specified, both will be combined.

        :param directory: The log directory to write to. If no filename is
                          specified, the program name and suffix will be used
                          to contruct the full path relative to the directory.

        :param suffix: The log file name suffix. This will be only used if no
                       filename has been provided.

        :param program_name: Program name. Autodetected by default.

        """
        logpath = _get_log_file_path(filename, directory, program_name, suffix)
        handler = logging.handlers.WatchedFileHandler(logpath)
        super(File, self).__init__(handler, formatter, level)


class RotatingFile(Output):
    """Output to a file, rotating after a certain size."""

    handler: logging.handlers.RotatingFileHandler

    def __init__(
        self,
        filename: typing.Optional[str] = None,
        directory: typing.Optional[str] = None,
        suffix: str = ".log",
        program_name: typing.Optional[str] = None,
        formatter: logging.Formatter = formatter.TEXT_FORMATTER,
        level: typing.Optional[int] = None,
        max_size_bytes: int = 0,
        backup_count: int = 0,
    ):
        """Rotating log file output.

        :param filename: The log file path to write to. If directory is also
                         specified, both will be combined.

        :param directory: The log directory to write to. If no filename is
                          specified, the program name and suffix will be used
                          to contruct the full path relative to the directory.

        :param suffix: The log file name suffix. This will be only used if no
                       filename has been provided.

        :param program_name: Program name. Autodetected by default.

        :param max_size_bytes: Allow the file to rollover at a predetermined
                               size.

        :param backup_count: The maximum number of files to rotate logging
                             output between.

        """
        logpath = _get_log_file_path(filename, directory, program_name, suffix)
        handler = logging.handlers.RotatingFileHandler(
            logpath, maxBytes=max_size_bytes, backupCount=backup_count
        )
        super(RotatingFile, self).__init__(handler, formatter, level)

    def do_rollover(self) -> None:
        """Manually forces a log file rotation."""
        return self.handler.doRollover()


class TimedRotatingFile(Output):
    """Rotating log file output, triggered by a fixed interval."""

    handler: logging.handlers.TimedRotatingFileHandler

    def __init__(
        self,
        filename: typing.Optional[str] = None,
        directory: typing.Optional[str] = None,
        suffix: str = ".log",
        program_name: typing.Optional[str] = None,
        formatter: logging.Formatter = formatter.TEXT_FORMATTER,
        level: typing.Optional[int] = None,
        interval: typing.Union[float, int, datetime.timedelta] = datetime.timedelta(
            hours=24
        ),
        backup_count: int = 0,
    ):
        """Rotating log file output, triggered by a fixed interval.

        :param filename: The log file path to write to. If directory is also
                         specified, both will be combined.

        :param directory: The log directory to write to. If no filename is
                          specified, the program name and suffix will be used
                          to contruct the full path relative to the directory.

        :param suffix: The log file name suffix. This will be only used if no
                       filename has been provided.

        :param program_name: Program name. Autodetected by default.

        :param interval: datetime.timedelta instance representing how often a
                         new log file should be created.

        :param backup_count: The maximum number of files to rotate logging
                             output between.
        """
        logpath = _get_log_file_path(filename, directory, program_name, suffix)
        handler = logging.handlers.TimedRotatingFileHandler(
            logpath,
            when="S",
            interval=int(self._timedelta_to_seconds(interval)),
            backupCount=backup_count,
        )
        super(TimedRotatingFile, self).__init__(handler, formatter, level)

    def do_rollover(self) -> None:
        """Manually forces a log file rotation."""
        return self.handler.doRollover()

    @staticmethod
    def _timedelta_to_seconds(
        td: typing.Union[float, int, datetime.timedelta]
    ) -> float:
        """Convert a datetime.timedelta object into a seconds interval.

        :param td: datetime.timedelta
        :return: time in seconds
        :rtype: int
        """
        if isinstance(td, (int, float)):
            td = datetime.timedelta(seconds=td)
        return td.total_seconds()


class Stream(Output):
    """Generic stream output."""

    def __init__(
        self,
        stream: typing.TextIO = sys.stderr,
        formatter: logging.Formatter = formatter.TEXT_FORMATTER,
        level: typing.Optional[int] = None,
    ) -> None:
        super(Stream, self).__init__(
            handlers.TTYDetectorStreamHandler(stream), formatter, level
        )


STDERR = Stream()
STDOUT = Stream(sys.stdout)


class Journal(Output):
    def __init__(
        self,
        program_name: typing.Optional[str] = None,
        formatter: logging.Formatter = formatter.TEXT_FORMATTER,
        level: typing.Optional[int] = None,
    ) -> None:
        program_name = program_name or get_program_name()
        super(Journal, self).__init__(
            handlers.JournalHandler(program_name), formatter, level
        )


class Syslog(Output):
    def __init__(
        self,
        program_name: typing.Optional[str] = None,
        facility: str = "user",
        formatter: logging.Formatter = formatter.TEXT_FORMATTER,
        level: typing.Optional[int] = None,
    ) -> None:
        if syslog is None:
            # FIXME(jd) raise something more specific
            raise RuntimeError("syslog is not available on this platform")
        super(Syslog, self).__init__(
            handlers.SyslogHandler(
                program_name=program_name or get_program_name(),
                facility=self._find_facility(facility),
            ),
            formatter,
            level,
        )

    @staticmethod
    def _find_facility(facility: str) -> int:
        # NOTE(jd): Check the validity of facilities at run time as they differ
        # depending on the OS and Python version being used.
        valid_facilities = [
            f
            for f in [
                "LOG_KERN",
                "LOG_USER",
                "LOG_MAIL",
                "LOG_DAEMON",
                "LOG_AUTH",
                "LOG_SYSLOG",
                "LOG_LPR",
                "LOG_NEWS",
                "LOG_UUCP",
                "LOG_CRON",
                "LOG_AUTHPRIV",
                "LOG_FTP",
                "LOG_LOCAL0",
                "LOG_LOCAL1",
                "LOG_LOCAL2",
                "LOG_LOCAL3",
                "LOG_LOCAL4",
                "LOG_LOCAL5",
                "LOG_LOCAL6",
                "LOG_LOCAL7",
            ]
            if getattr(syslog, f, None)
        ]

        facility = facility.upper()

        if not facility.startswith("LOG_"):
            facility = "LOG_" + facility

        if facility not in valid_facilities:
            raise TypeError(
                "syslog facility must be one of: %s"
                % ", ".join("'%s'" % fac for fac in valid_facilities)
            )

        return int(getattr(syslog, facility))


class Datadog(Output):
    def __init__(
        self,
        hostname: str = "127.0.0.1",
        port: int = 10518,
        formatter: logging.Formatter = formatter.DATADOG_FORMATTER,
        level: typing.Optional[int] = None,
        handler_class: typing.Type[
            logging.handlers.SocketHandler
        ] = handlers.PlainTextSocketHandler,
    ):
        super(Datadog, self).__init__(
            handler_class(hostname, port),
            formatter=formatter,
            level=level,
        )


# FIXME(jd): Is this useful? Remove it?
preconfigured: typing.Dict[str, typing.Union[Stream, Output]] = {
    "stderr": STDERR,
    "stdout": STDOUT,
}

if syslog is not None:
    preconfigured["syslog"] = Syslog()

if handlers.journal is not None:  # type: ignore[attr-defined]
    preconfigured["journal"] = Journal()
