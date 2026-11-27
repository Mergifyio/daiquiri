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
import os
import shutil
import socket
import ssl
import subprocess
import tempfile
import threading
import unittest

from daiquiri import formatter, handlers, output


class _Server:
    """Accept one connection and keep what the client sent."""

    def __init__(self, context: ssl.SSLContext | None = None) -> None:
        self.context = context
        self.listener = socket.create_server(("127.0.0.1", 0))
        self.listener.settimeout(5)
        self.port = self.listener.getsockname()[1]
        self.received = b""
        self.thread = threading.Thread(target=self._serve, daemon=True)
        self.thread.start()

    def _serve(self) -> None:
        try:
            conn, _ = self.listener.accept()
        except OSError:
            return
        conn.settimeout(5)
        try:
            if self.context is not None:
                conn = self.context.wrap_socket(conn, server_side=True)
            while not self.received.endswith(b"\n"):
                data = conn.recv(4096)
                if not data:
                    break
                self.received += data
        except OSError:
            pass
        finally:
            conn.close()

    def join(self) -> bytes:
        self.thread.join(10)
        self.listener.close()
        return self.received


@unittest.skipIf(shutil.which("openssl") is None, "openssl not available")
class TestTLSPlainTextSocketHandler(unittest.TestCase):
    certdir: str
    cert: str
    key: str

    @classmethod
    def setUpClass(cls) -> None:
        # Generated at run time so that no private key is shipped.
        cls.certdir = tempfile.mkdtemp()
        cls.cert = os.path.join(cls.certdir, "cert.pem")
        cls.key = os.path.join(cls.certdir, "key.pem")
        subprocess.run(
            [
                "openssl",
                "req",
                "-x509",
                "-newkey",
                "rsa:2048",
                "-nodes",
                "-days",
                "1",
                "-subj",
                "/CN=localhost",
                "-addext",
                "subjectAltName=DNS:localhost,IP:127.0.0.1",
                "-keyout",
                cls.key,
                "-out",
                cls.cert,
            ],
            check=True,
            capture_output=True,
        )
        super().setUpClass()

    @classmethod
    def tearDownClass(cls) -> None:
        shutil.rmtree(cls.certdir, ignore_errors=True)
        super().tearDownClass()

    def server_context(self) -> ssl.SSLContext:
        context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
        context.load_cert_chain(self.cert, self.key)
        return context

    def client_context(self) -> ssl.SSLContext:
        return ssl.create_default_context(cafile=self.cert)

    def emit(self, handler: logging.Handler, server: _Server, message: str) -> bytes:
        """Log message through handler and return what the server received.

        The handler is closed only once the server has read: closing a TLS
        socket with unread data (the TLS 1.3 session ticket) can reset the
        connection and discard what was sent.
        """
        handler.setFormatter(logging.Formatter("%(message)s"))
        try:
            handler.handle(
                logging.LogRecord("test", logging.INFO, "", 0, message, None, None)
            )
            return server.join()
        finally:
            handler.close()

    def test_sends_over_tls(self) -> None:
        server = _Server(self.server_context())
        handler = handlers.TLSPlainTextSocketHandler(
            "127.0.0.1", server.port, ssl_context=self.client_context()
        )
        self.assertEqual(self.emit(handler, server, "secret"), b"secret\n")

    def test_untrusted_certificate_sends_nothing(self) -> None:
        server = _Server(self.server_context())
        # Default context: the system's authorities do not trust this cert.
        handler = handlers.TLSPlainTextSocketHandler("127.0.0.1", server.port)
        self.assertEqual(self.emit(handler, server, "secret"), b"")
        self.assertIsNone(handler.sock)

    def test_no_fallback_to_plain_tcp(self) -> None:
        server = _Server(context=None)
        handler = handlers.TLSPlainTextSocketHandler(
            "127.0.0.1", server.port, ssl_context=self.client_context()
        )
        received = self.emit(handler, server, "secret")
        self.assertNotIn(b"secret", received)
        # What reached the plain TCP server is a TLS handshake record.
        self.assertTrue(received.startswith(b"\x16"), received[:10])

    def test_datadog_output_with_context_set_on_subclass(self) -> None:
        server = _Server(self.server_context())
        context = self.client_context()

        class Handler(handlers.TLSPlainTextSocketHandler):
            ssl_context = context

        out = output.Datadog(
            hostname="127.0.0.1", port=server.port, handler_class=Handler
        )
        logger = logging.getLogger("test_tls.datadog")
        logger.propagate = False
        out.add_to_logger(logger)
        self.addCleanup(logger.removeHandler, out.handler)
        self.assertIs(out.handler.formatter, formatter.DATADOG_FORMATTER)
        try:
            logger.error("over tls")
            received = server.join()
        finally:
            out.handler.close()
        payload = json.loads(received)
        self.assertEqual(payload["message"], "over tls")
        self.assertEqual(payload["status"], "error")
