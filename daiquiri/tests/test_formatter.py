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
        super(TestColorExtrasFormatter, cls).setUpClass()

    def setUp(self) -> None:
        # Couldn't get readline() to return anything no matter what I tried, so
        # getvalue() is the only way to see what's in the stream. However this
        # requires the stream to be reset every time.
        self.stream.close()
        self.stream = io.StringIO()
        self.handler.stream = self.stream
        super(TestColorExtrasFormatter, self).setUp()

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
        format_string = "%(levelname)s %(name)s" " %(test)s%(extras)s: %(message)s"
        formatter = daiquiri.formatter.ColorExtrasFormatter(
            fmt=format_string, keywords={"test"}
        )
        self.handler.setFormatter(formatter)

        self.logger.info("test message", test="a")
        self.assertEqual(self.stream.getvalue(), "INFO my_module a: test message\n")

    def test_keywords_with_extras(self) -> None:
        format_string = "%(levelname)s %(name)s" " %(test)s%(extras)s: %(message)s"
        formatter = daiquiri.formatter.ColorExtrasFormatter(
            fmt=format_string, keywords={"test"}
        )
        self.handler.setFormatter(formatter)

        self.logger.info("test message", test="a", test2="b")
        self.assertEqual(
            self.stream.getvalue(), "INFO my_module a [test2: b]: test message\n"
        )
