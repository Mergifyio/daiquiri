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
import logging
import typing
import unittest

import daiquiri


class TestColorExtrasFormatter(unittest.TestCase):
    logger: daiquiri.KeywordArgumentAdapter
    stream: io.StringIO
    handler: daiquiri.handlers.TTYDetectorStreamHandler

    @classmethod
    def setUpClass(cls) -> None:
        cls.logger = daiquiri.getLogger("my_module")
        cls.logger.setLevel(logging.INFO)
        cls.stream = io.StringIO()
        cls.handler = daiquiri.handlers.TTYDetectorStreamHandler(cls.stream)
        cls.logger.logger.addHandler(cls.handler)
        super().setUpClass()

    def setUp(self) -> None:
        # Couldn't get readline() to return anything no matter what I tried, so
        # getvalue() is the only way to see what's in the stream. However this
        # requires the stream to be reset every time.
        self.stream.close()
        self.stream = io.StringIO()
        self.handler.stream = self.stream
        super().setUp()

    def test_no_keywords(self) -> None:
        format_string = "%(levelname)s %(name)s%(extras)s: %(message)s"
        formatter = daiquiri.formatter.ColorExtrasFormatter(fmt=format_string)
        self.handler.setFormatter(formatter)

        self.logger.info("test message")
        self.assertEqual(self.stream.getvalue(), "INFO my_module: test message\n")

    def test_no_keywords_with_extras(self) -> None:
        format_string = "%(levelname)s %(name)s%(extras)s: %(message)s"
        formatter = daiquiri.formatter.ColorExtrasFormatter(fmt=format_string)
        self.handler.setFormatter(formatter)

        self.logger.info("test message", test="a")
        self.assertEqual(
            self.stream.getvalue(), "INFO my_module [test: a]: test message\n"
        )

    def test_empty_keywords(self) -> None:
        format_string = "%(levelname)s %(name)s%(extras)s: %(message)s"
        formatter = daiquiri.formatter.ColorExtrasFormatter(
            fmt=format_string,
            keywords=set(),
        )
        self.handler.setFormatter(formatter)

        self.logger.info("test message", test="a")
        self.assertEqual(
            self.stream.getvalue(), "INFO my_module [test: a]: test message\n"
        )

    def test_keywords_no_extras(self) -> None:
        format_string = "%(levelname)s %(name)s %(test)s%(extras)s: %(message)s"
        formatter = daiquiri.formatter.ColorExtrasFormatter(
            fmt=format_string, keywords={"test"}
        )
        self.handler.setFormatter(formatter)

        self.logger.info("test message", test="a")
        self.assertEqual(self.stream.getvalue(), "INFO my_module a: test message\n")

    def test_keywords_with_extras(self) -> None:
        format_string = "%(levelname)s %(name)s %(test)s%(extras)s: %(message)s"
        formatter = daiquiri.formatter.ColorExtrasFormatter(
            fmt=format_string, keywords={"test"}
        )
        self.handler.setFormatter(formatter)

        self.logger.info("test message", test="a", test2="b")
        self.assertEqual(
            self.stream.getvalue(), "INFO my_module a [test2: b]: test message\n"
        )


class _TTYStringIO(io.StringIO):
    def isatty(self) -> bool:
        return True


class _MultiLineStr:
    def __str__(self) -> str:
        return "first\nsecond"


class TestEscapeControlChars(unittest.TestCase):
    FORMAT = "%(levelname)s %(name)s%(extras)s: %(message)s"

    def setUp(self) -> None:
        self.logger = daiquiri.getLogger("escape_module")
        self.logger.setLevel(logging.INFO)
        self.stream = io.StringIO()
        self.handler = daiquiri.handlers.TTYDetectorStreamHandler(self.stream)
        self.logger.logger.addHandler(self.handler)
        self.addCleanup(self.logger.logger.removeHandler, self.handler)

    def use(self, fmt: str = FORMAT, **kwargs: typing.Any) -> None:
        self.handler.setFormatter(
            daiquiri.formatter.ColorExtrasFormatter(
                fmt=fmt, escape_control_chars=True, **kwargs
            )
        )

    def test_off_by_default(self) -> None:
        self.handler.setFormatter(
            daiquiri.formatter.ColorExtrasFormatter(fmt=self.FORMAT)
        )
        self.logger.info("a\nb")
        self.assertEqual(self.stream.getvalue(), "INFO escape_module: a\nb\n")

    def test_message(self) -> None:
        self.use()
        self.logger.info("a\r\nINFO forged: b")
        self.assertEqual(
            self.stream.getvalue(), r"INFO escape_module: a\r\nINFO forged: b" + "\n"
        )

    def test_message_arguments(self) -> None:
        self.use()
        self.logger.info("user %s logged in", "bob\nINFO forged")
        self.assertEqual(
            self.stream.getvalue(),
            r"INFO escape_module: user bob\nINFO forged logged in" + "\n",
        )

    def test_percent_in_escaped_message_is_not_reinterpreted(self) -> None:
        self.use()
        self.logger.info("%s", "100%s\n")
        self.assertEqual(self.stream.getvalue(), r"INFO escape_module: 100%s\n" + "\n")

    def test_extra_value_and_name(self) -> None:
        self.use()
        self.logger.info("msg", user="bob\nx", extra={"k\ny": "v"})
        self.assertIn(r"[user: bob\nx]", self.stream.getvalue())
        self.assertIn(r"[k\ny: v]", self.stream.getvalue())
        self.assertEqual(self.stream.getvalue().count("\n"), 1)

    def test_extra_interpolated_by_custom_format(self) -> None:
        self.use(
            fmt="%(user)s %(count)d%(extras)s: %(message)s", keywords={"user", "count"}
        )
        self.logger.info("msg", user="bob\nx", count=3)
        self.assertEqual(self.stream.getvalue(), r"bob\nx 3: msg" + "\n")

    def test_object_whose_text_holds_a_newline(self) -> None:
        self.use()
        self.logger.info("msg", obj=_MultiLineStr())
        self.assertEqual(
            self.stream.getvalue(),
            r"INFO escape_module [obj: first\nsecond]: msg" + "\n",
        )

    def test_tab_is_kept(self) -> None:
        self.use()
        self.logger.info("a\tb")
        self.assertEqual(self.stream.getvalue(), "INFO escape_module: a\tb\n")

    def test_escape_sequence_escaped_but_colors_kept(self) -> None:
        self.handler.stream = _TTYStringIO()
        self.use(fmt="%(color)s%(message)s%(color_stop)s")
        self.logger.info("\033[2Jcleared")
        self.assertEqual(
            self.handler.stream.getvalue(),
            "\033[00;36m" + r"\x1b[2Jcleared" + "\033[0m\n",
        )

    def test_original_record_is_left_untouched(self) -> None:
        records: list[logging.LogRecord] = []

        class Collect(logging.Handler):
            def emit(self, record: logging.LogRecord) -> None:
                records.append(record)

        collector = Collect()
        self.logger.logger.addHandler(collector)
        self.addCleanup(self.logger.logger.removeHandler, collector)
        self.use()
        self.logger.info("a\n%s", "b", user="c\n")
        self.assertEqual(records[0].getMessage(), "a\nb")
        self.assertEqual(records[0].__dict__["user"], "c\n")

    def test_traceback_stays_multi_line(self) -> None:
        self.use()
        try:
            raise ValueError("boom")
        except ValueError:
            self.logger.exception("failed\nhere")
        output = self.stream.getvalue()
        self.assertTrue(output.startswith(r"ERROR escape_module: failed\nhere" + "\n"))
        self.assertIn("Traceback (most recent call last):\n", output)
