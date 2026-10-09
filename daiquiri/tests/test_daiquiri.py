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
import io
import json
import logging
import sys
import types
import typing
import unittest
import warnings
from unittest import mock

import daiquiri

real_excepthook = sys.excepthook


class TestDaiquiri(unittest.TestCase):
    def tearDown(self) -> None:
        # Be sure to reset the warning capture
        logging.captureWarnings(False)
        # Reset exception hook
        sys.excepthook = real_excepthook
        super().tearDown()

    def test_setup(self) -> None:
        daiquiri.setup()
        daiquiri.setup(level=logging.DEBUG)
        daiquiri.setup(program_name="foobar")

    def test_setup_fixes_windows_console(self) -> None:
        original_stderr = sys.stderr
        original_stream = daiquiri.output.STDERR.handler.stream
        wrapped_stderr = io.StringIO()

        def just_fix_windows_console() -> None:
            sys.stderr = wrapped_stderr

        colorama = types.ModuleType("colorama")
        colorama.__dict__["just_fix_windows_console"] = just_fix_windows_console

        try:
            with (
                mock.patch.object(sys, "platform", "win32"),
                mock.patch.dict(sys.modules, {"colorama": colorama}),
            ):
                daiquiri.setup(outputs=(), capture_warnings=False, set_excepthook=False)
                self.assertIs(daiquiri.output.STDERR.handler.stream, wrapped_stderr)
        finally:
            sys.stderr = original_stderr
            daiquiri.output.STDERR.handler.setStream(original_stream)

    def test_setup_without_colorama(self) -> None:
        with (
            mock.patch.object(sys, "platform", "win32"),
            mock.patch("builtins.__import__", side_effect=ImportError),
        ):
            daiquiri.setup(outputs=(), capture_warnings=False, set_excepthook=False)

    def test_excepthook(self) -> None:
        hook_ran = False

        def catcher(
            exctype: type[BaseException],
            value: BaseException,
            traceback: types.TracebackType | None,
        ) -> None:
            nonlocal hook_ran
            hook_ran = True
            real_excepthook(exctype, value, traceback)

        sys.excepthook = catcher

        sys.excepthook(Exception, Exception("boom"), None)
        assert hook_ran

        daiquiri.setup()

        hook_ran = False
        sys.excepthook(Exception, Exception("boom"), None)
        assert hook_ran

    def test_setup_json_formatter(self) -> None:
        stream = io.StringIO()
        daiquiri.setup(
            outputs=(
                daiquiri.output.Stream(
                    stream, formatter=daiquiri.formatter.JSON_FORMATTER
                ),
            )
        )
        daiquiri.getLogger(__name__).warning("foobar")
        expected: dict[str, typing.Any] = {"message": "foobar"}
        self.assertEqual(expected, json.loads(stream.getvalue()))

    def test_setup_json_formatter_with_extras(self) -> None:
        stream = io.StringIO()
        daiquiri.setup(
            outputs=(
                daiquiri.output.Stream(
                    stream, formatter=daiquiri.formatter.JSON_FORMATTER
                ),
            )
        )
        daiquiri.getLogger(__name__).warning("foobar", foo="bar")
        expected: dict[str, typing.Any] = {"message": "foobar", "foo": "bar"}
        self.assertEqual(expected, json.loads(stream.getvalue()))

    def test_get_logger_set_level(self) -> None:
        logger = daiquiri.getLogger(__name__)
        logger.setLevel(logging.DEBUG)

    def test_capture_warnings(self) -> None:
        stream = io.StringIO()
        daiquiri.setup(outputs=(daiquiri.output.Stream(stream),))
        warnings.warn("omg!")
        line = stream.getvalue()
        self.assertIn("WARNING  py.warnings: ", line)
        self.assertIn(
            "daiquiri/tests/test_daiquiri.py:95: "
            'UserWarning: omg!\n  warnings.warn("omg!")\n',
            line,
        )

    def test_no_capture_warnings(self) -> None:
        stream = io.StringIO()
        daiquiri.setup(
            outputs=(daiquiri.output.Stream(stream),), capture_warnings=False
        )
        warnings.warn("omg!")
        self.assertEqual("", stream.getvalue())

    def test_set_default_log_levels(self) -> None:
        daiquiri.set_default_log_levels((("amqp", "debug"), ("urllib3", "warn")))

    def test_parse_and_set_default_log_levels(self) -> None:
        daiquiri.parse_and_set_default_log_levels(("urllib3=warn", "foobar=debug"))

    def test_string_as_setup_outputs_arg(self) -> None:
        daiquiri.setup(outputs=("stderr", "stdout"))

        if daiquiri.handlers.syslog is not None:  # type: ignore[attr-defined]
            daiquiri.setup(outputs=("syslog",))

        if daiquiri.handlers.journal is not None:  # type: ignore[attr-defined]
            daiquiri.setup(outputs=("journal",))

    def test_special_kwargs(self) -> None:
        daiquiri.getLogger(__name__).info(
            "foobar", foo="bar", exc_info=True, stack_info=True
        )


def test_extra_with_two_loggers() -> None:
    stream = io.StringIO()
    daiquiri.setup(outputs=(daiquiri.output.Stream(stream),))
    log1 = daiquiri.getLogger("foobar")
    log1.error("argh")
    log2 = daiquiri.getLogger("foobar", key="value")
    log2.warning("boo")
    lines = stream.getvalue().strip().split("\n")
    assert lines[0].endswith("ERROR    foobar: argh")
    assert lines[1].endswith("WARNING  foobar [key: value]: boo")
