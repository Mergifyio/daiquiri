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
import socket
import unittest
from unittest import mock

import daiquiri
from daiquiri import handlers, output

try:
    import syslog
except ImportError:
    syslog = None  # type: ignore[assignment]

# Facilities as the syslog module defines them (shifted by 3 bits).
LOG_USER = 1 << 3
LOG_AUTH = 4 << 3
LOG_LOCAL0 = 16 << 3


class TestSyslogHandler(unittest.TestCase):
    def setUp(self) -> None:
        self.receiver = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.addCleanup(self.receiver.close)
        self.receiver.bind(("127.0.0.1", 0))
        self.receiver.settimeout(5)
        self.address = self.receiver.getsockname()
        self.logger = logging.getLogger(f"test_syslog.{self.id()}")
        self.logger.setLevel(logging.DEBUG)
        self.logger.propagate = False

    def handler(
        self, program_name: str, facility: int | None = None
    ) -> handlers.SyslogHandler:
        handler = handlers.SyslogHandler(program_name, facility, address=self.address)
        handler.setFormatter(logging.Formatter("%(message)s"))
        self.logger.addHandler(handler)
        self.addCleanup(handler.close)
        self.addCleanup(self.logger.removeHandler, handler)
        return handler

    def receive(self) -> bytes:
        return self.receiver.recv(4096)

    def test_default_facility_is_user(self) -> None:
        self.handler("prog")
        self.logger.info("hello")
        self.assertEqual(self.receive(), b"<14>prog: hello\x00")

    def test_each_handler_keeps_its_facility_and_identity(self) -> None:
        self.handler("audit", LOG_AUTH)
        # Built last: with a process-wide openlog, both handlers would use it.
        self.handler("app", LOG_LOCAL0)
        self.logger.warning("hello")
        self.assertEqual(
            sorted([self.receive(), self.receive()]),
            [b"<132>app: hello\x00", b"<36>audit: hello\x00"],
        )

    def test_level_mapping(self) -> None:
        self.handler("prog", LOG_USER)
        logging.addLevelName(25, "NOTICE_TEST")
        for level, priority in [
            (logging.DEBUG, 7),
            (logging.INFO, 6),
            (logging.WARNING, 4),
            (logging.ERROR, 3),
            (logging.CRITICAL, 2),
            (25, 7),
        ]:
            self.logger.log(level, "m")
            self.assertEqual(self.receive(), f"<{8 + priority}>prog: m\x00".encode())

    @unittest.skipIf(syslog is None, "syslog module not available")
    def test_handler_does_not_call_openlog(self) -> None:
        with mock.patch("syslog.openlog") as openlog:
            self.handler("prog", LOG_AUTH)
            output.Syslog(program_name="prog", facility="auth").handler.close()
        openlog.assert_not_called()

    @unittest.skipIf(syslog is None, "syslog module not available")
    def test_syslog_output_facility(self) -> None:
        out = output.Syslog(program_name="prog", facility="local0")
        self.addCleanup(out.handler.close)
        assert isinstance(out.handler, handlers.SyslogHandler)
        self.assertEqual(out.handler.syslog_facility, syslog.LOG_LOCAL0)
        self.assertEqual(out.handler.ident, "prog: ")


class TestPreconfigured(unittest.TestCase):
    def test_built_on_first_use_only(self) -> None:
        built = output.Stream()
        factory = mock.Mock(return_value=built)
        with (
            mock.patch.dict(output._lazy_preconfigured, {"lazy_test": factory}),
            mock.patch.dict(output.preconfigured),
        ):
            self.assertNotIn("lazy_test", output.preconfigured)
            self.assertIs(output.get_preconfigured("lazy_test"), built)
            self.assertIs(output.get_preconfigured("lazy_test"), built)
        factory.assert_called_once_with()

    def test_unknown_output(self) -> None:
        with self.assertRaisesRegex(RuntimeError, "Output nope is not available"):
            daiquiri.setup(outputs=["nope"])
