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
import json
import logging
import unittest
import warnings

import six.moves

import daiquiri


class TestDaiquiri(unittest.TestCase):
    def tearDown(self):
        # Be sure to reset the warning capture
        logging.captureWarnings(False)
        super(TestDaiquiri, self).tearDown()

    def test_setup(self):
        daiquiri.setup()
        daiquiri.setup(level=logging.DEBUG)
        daiquiri.setup(program_name="foobar")

    def test_setup_json_formatter(self):
        stream = six.moves.StringIO()
        daiquiri.setup(outputs=(
            daiquiri.output.Stream(
                stream, formatter=daiquiri.formatter.JSON_FORMATTER),
        ))
        daiquiri.getLogger(__name__).warning("foobar")
        self.assertEqual({"message": "foobar"},
                         json.loads(stream.getvalue()))

    def test_setup_json_formatter_with_extras(self):
        stream = six.moves.StringIO()
        daiquiri.setup(outputs=(
            daiquiri.output.Stream(
                stream, formatter=daiquiri.formatter.JSON_FORMATTER),
        ))
        daiquiri.getLogger(__name__).warning("foobar", foo="bar")
        self.assertEqual({"message": "foobar", "foo": "bar"},
                         json.loads(stream.getvalue()))

    def test_get_logger_set_level(self):
        logger = daiquiri.getLogger(__name__)
        logger.setLevel(logging.DEBUG)

    def test_capture_warnings(self):
        stream = six.moves.StringIO()
        daiquiri.setup(outputs=(
            daiquiri.output.Stream(stream),
        ))
        warnings.warn("omg!")
        line = stream.getvalue()
        self.assertIn("WARNING  py.warnings: ", line)
        self.assertIn("daiquiri/tests/test_daiquiri.py:62: "
                      "UserWarning: omg!\n  warnings.warn(\"omg!\")\n",
                      line)

    def test_no_capture_warnings(self):
        stream = six.moves.StringIO()
        daiquiri.setup(outputs=(
            daiquiri.output.Stream(stream),
        ), capture_warnings=False)
        warnings.warn("omg!")
        self.assertEqual("", stream.getvalue())

    def test_set_default_log_levels(self):
        daiquiri.set_default_log_levels((("amqp", "debug"),
                                         ("urllib3", "warn")))

    def test_parse_and_set_default_log_levels(self):
        daiquiri.parse_and_set_default_log_levels(
            ("urllib3=warn", "foobar=debug"))

    def test_string_as_setup_outputs_arg(self):
        daiquiri.setup(outputs=('stderr', 'stdout'))

        if daiquiri.handlers.syslog is not None:
            daiquiri.setup(outputs=('syslog',))

        if daiquiri.handlers.journal is not None:
            daiquiri.setup(outputs=('journal',))


def test_extra_with_two_loggers():
    stream = six.moves.StringIO()
    daiquiri.setup(outputs=(
        daiquiri.output.Stream(stream),
    ))
    log1 = daiquiri.getLogger("foobar")
    log1.error("argh")
    log2 = daiquiri.getLogger("foobar", key="value")
    log2.warning("boo")
    lines = stream.getvalue().strip().split("\n")
    assert lines[0].endswith("ERROR    foobar: argh")
    assert lines[1].endswith("WARNING  foobar [key: value]: boo")
