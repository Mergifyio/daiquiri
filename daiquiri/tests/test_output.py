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
import sys
import syslog
import typing
import unittest
from datetime import timedelta
from unittest import mock

import daiquiri
from daiquiri import output


class DatadogMatcher(object):
    def __init__(self, expected: typing.Any) -> None:
        self.expected = expected

    def __eq__(self, other: typing.Any) -> bool:
        return bool(json.loads(other.decode()[:-1]) == self.expected)

    def __repr__(self) -> str:
        return (
            "b'"
            + json.dumps(self.expected, default=lambda x: "unserializable")
            + "\\n'"
        )


class TestOutput(unittest.TestCase):
    def test_find_facility(self) -> None:
        self.assertEqual(syslog.LOG_USER, output.Syslog._find_facility("user"))
        self.assertEqual(syslog.LOG_LOCAL1, output.Syslog._find_facility("log_local1"))
        self.assertEqual(syslog.LOG_LOCAL2, output.Syslog._find_facility("LOG_local2"))
        self.assertEqual(syslog.LOG_LOCAL3, output.Syslog._find_facility("LOG_LOCAL3"))
        self.assertEqual(syslog.LOG_LOCAL4, output.Syslog._find_facility("LOCaL4"))

    def test_get_log_file_path(self) -> None:
        self.assertEqual("foobar.log", output._get_log_file_path("foobar.log"))
        self.assertEqual(
            "/var/log/foo/foobar.log",
            output._get_log_file_path("foobar.log", logdir="/var/log/foo"),
        )
        self.assertEqual(
            "/var/log/foobar.log",
            output._get_log_file_path(logdir="/var/log", program_name="foobar"),
        )
        self.assertEqual(
            "/var/log/foobar.log",
            output._get_log_file_path(logdir="/var/log", program_name="foobar"),
        )
        self.assertEqual(
            "/var/log/foobar.journal",
            output._get_log_file_path(
                logdir="/var/log", logfile_suffix=".journal", program_name="foobar"
            ),
        )

    def test_timedelta_seconds(self) -> None:
        fn = output.TimedRotatingFile._timedelta_to_seconds
        hour = 60 * 60  # seconds * minutes

        one_hour = [
            timedelta(hours=1),
            timedelta(minutes=60),
            timedelta(seconds=hour),
        ]
        for t in one_hour:
            self.assertEqual(hour, fn(t))

        assert hour == fn(float(hour))
        assert hour == fn(hour)

        error_cases = [
            "string",
            ["some", "list"],
            (
                "some",
                "tuple",
            ),
            ("tuple",),
            {"dict": "mapping"},
        ]
        for t in error_cases:  # type: ignore[assignment]
            self.assertRaises(AttributeError, fn, t)

    def test_datadog(self) -> None:
        with mock.patch("socket.socket") as mock_socket:
            socket_instance = mock_socket.return_value
            daiquiri.setup(outputs=(daiquiri.output.Datadog(),), level=logging.DEBUG)
            logger = daiquiri.getLogger()
            logger.error("foo", bar=1)
            logger.info("bar")
            expected_error_1 = {
                "status": "error",
                "message": "foo",
                "bar": 1,
                "logger": {"name": "root"},
                "timestamp": mock.ANY,
            }
            expected_info_1 = {
                "status": "info",
                "message": "bar",
                "logger": {"name": "root"},
                "timestamp": mock.ANY,
            }
            expected_error_2 = {
                "status": "error",
                "message": "backtrace",
                "logger": {"name": "saymyname"},
                "timestamp": mock.ANY,
                "error": {
                    "kind": "ZeroDivisionError",
                    "stack": None,
                    "message": mock.ANY,
                },
            }
            if sys.version_info >= (3, 12):
                expected_error_1.update({"taskName": None})
                expected_info_1.update({"taskName": None})
                expected_error_2.update({"taskName": None})
            try:
                1 / 0
            except ZeroDivisionError:
                logger = daiquiri.getLogger("saymyname")
                logger.exception("backtrace")
            socket_instance.connect.assert_called_once_with(("127.0.0.1", 10518))
            socket_instance.sendall.assert_has_calls(
                [
                    mock.call(DatadogMatcher(expected_error_1)),
                    mock.call(DatadogMatcher(expected_info_1)),
                    mock.call(DatadogMatcher(expected_error_2)),
                ]
            )
