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
import collections.abc
import logging
import logging.config
import logging.handlers
import sys
import traceback
import typing

from daiquiri import output


class KeywordArgumentAdapter(logging.LoggerAdapter):
    """Logger adapter to add keyword arguments to log record's extra data.

    Keywords passed to the log call are added to the "extra"
    dictionary passed to the underlying logger so they are emitted
    with the log message and available to the format string.

    Special keywords:

    extra
      An existing dictionary of extra values to be passed to the
      logger. If present, the dictionary is copied and extended.

    """

    def process(
        self, msg: typing.Any, kwargs: "collections.abc.MutableMapping[str, typing.Any]"
    ) -> typing.Tuple[typing.Any, "collections.abc.MutableMapping[str, typing.Any]"]:
        # Make a new extra dictionary combining the values we were
        # given when we were constructed and anything from kwargs.
        if self.extra is not None:
            extra = dict(self.extra)
        if "extra" in kwargs:
            extra.update(kwargs.pop("extra"))
        # Move any unknown keyword arguments into the extra
        # dictionary.
        for name in list(kwargs.keys()):
            if name in ("exc_info", "stack_info"):
                continue
            extra[name] = kwargs.pop(name)
        extra["_daiquiri_extra_keys"] = set(extra.keys())
        kwargs["extra"] = extra
        return msg, kwargs

    if sys.version_info.major == 2:

        def setLevel(self, level):
            """Set the specified level on the underlying logger."""
            self.logger.setLevel(level)


def getLogger(name: typing.Optional[str] = None, **kwargs) -> KeywordArgumentAdapter:
    """Build a logger with the given name.

    :param name: The name for the logger. This is usually the module
                 name, ``__name__``.
    :type name: string
    """
    return KeywordArgumentAdapter(logging.getLogger(name), kwargs)


def setup(
    level: int = logging.WARNING,
    outputs: typing.List[output.Output] = [output.STDERR],
    program_name: typing.Optional[str] = None,
    capture_warnings: bool = True,
    set_excepthook: bool = True,
):
    """Set up Python logging.

    This sets up basic handlers for Python logging.

    :param level: Root log level.
    :param outputs: Iterable of outputs to log to.
    :param program_name: The name of the program. Auto-detected if not set.
    :param capture_warnings: Capture warnings from the `warnings` module.
    """
    root_logger = logging.getLogger(None)

    # Remove all handlers
    for handler in list(root_logger.handlers):
        root_logger.removeHandler(handler)

    # Add configured handlers
    for out in outputs:
        if isinstance(out, str):
            if out not in output.preconfigured:
                raise RuntimeError("Output {} is not available".format(out))
            out = output.preconfigured[out]

        out.add_to_logger(root_logger)

    root_logger.setLevel(level)

    if set_excepthook:
        program_logger = logging.getLogger(program_name)

        def logging_excepthook(exc_type, value, tb):
            program_logger.critical(
                "".join(traceback.format_exception(exc_type, value, tb))
            )

        sys.excepthook = logging_excepthook

    if capture_warnings:
        logging.captureWarnings(True)


def parse_and_set_default_log_levels(
    default_log_levels: typing.Iterable[str], separator: str = "="
) -> None:
    """Set default log levels for some loggers.

    :param default_log_levels: List of strings with format
                               <logger_name><separator><log_level>
    """
    levels = []
    for pair in default_log_levels:
        result = pair.split(separator, 1)
        if len(result) != 2:
            raise ValueError("Wrong log level format: `%s`" % result)
        levels.append(typing.cast(typing.Tuple[str, str], tuple(result)))
    return set_default_log_levels(levels)


def set_default_log_levels(
    loggers_and_log_levels: typing.Iterable[
        typing.Tuple[typing.Optional[str], typing.Union[str, int]]
    ]
) -> None:
    """Set default log levels for some loggers.

    :param loggers_and_log_levels: List of tuple (logger name, level).
    """
    for logger, level in loggers_and_log_levels:
        if isinstance(level, str):
            level = level.upper()
        logging.getLogger(logger).setLevel(level)
