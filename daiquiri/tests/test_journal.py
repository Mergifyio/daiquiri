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
import typing

import pytest

import daiquiri
from daiquiri import handlers


class FakeJournal:
    """Records calls, with the same signature as systemd.journal.send."""

    def __init__(self) -> None:
        self.sent: list[dict[str, typing.Any]] = []

    def send(
        self,
        MESSAGE: str,
        MESSAGE_ID: typing.Any = None,
        CODE_FILE: typing.Any = None,
        CODE_LINE: typing.Any = None,
        CODE_FUNC: typing.Any = None,
        **kwargs: typing.Any,
    ) -> None:
        self.sent.append(
            {
                "MESSAGE": MESSAGE,
                "MESSAGE_ID": MESSAGE_ID,
                "CODE_FILE": CODE_FILE,
                "CODE_LINE": CODE_LINE,
                "CODE_FUNC": CODE_FUNC,
                **kwargs,
            }
        )


@pytest.fixture
def journal(
    monkeypatch: pytest.MonkeyPatch,
) -> typing.Iterator[FakeJournal]:
    fake = FakeJournal()
    monkeypatch.setattr(handlers, "journal", fake)
    output = daiquiri.output.Journal(program_name="myapp")
    daiquiri.setup(
        outputs=(output,),
        level=logging.INFO,
        set_excepthook=False,
        capture_warnings=False,
    )
    yield fake
    logging.getLogger().removeHandler(output.handler)


def test_extras_are_sent_as_fields(journal: FakeJournal) -> None:
    daiquiri.getLogger("test").info("hello", user="bob")
    (fields,) = journal.sent
    assert fields["USER"] == "bob"
    assert fields["PRIORITY"] == 6
    assert fields["SYSLOG_IDENTIFIER"] == "myapp"
    assert fields["LOGGER_NAME"] == "test"


def test_extras_do_not_override_handler_fields(journal: FakeJournal) -> None:
    daiquiri.getLogger("test").info(
        "hello",
        priority=0,
        syslog_identifier="sshd",
        code_file="/etc/fake.py",
        code_line=1,
        message_id="fe2e1f39d3e84b1b9b8a7c0d1e2f3a4b",
    )
    (fields,) = journal.sent
    assert fields["PRIORITY"] == 6
    assert fields["SYSLOG_IDENTIFIER"] == "myapp"
    assert fields["CODE_FILE"] == __file__
    assert fields["CODE_LINE"] != 1
    assert fields["MESSAGE_ID"] is None
    assert fields["EXTRA_PRIORITY"] == 0
    assert fields["EXTRA_SYSLOG_IDENTIFIER"] == "sshd"
    assert fields["EXTRA_CODE_FILE"] == "/etc/fake.py"
    assert fields["EXTRA_CODE_LINE"] == 1
    assert fields["EXTRA_MESSAGE_ID"] == "fe2e1f39d3e84b1b9b8a7c0d1e2f3a4b"


@pytest.mark.parametrize("name", ["MESSAGE", "Message"])
def test_message_extra_does_not_raise(journal: FakeJournal, name: str) -> None:
    daiquiri.getLogger("test").info(
        "hello", **typing.cast(dict[str, typing.Any], {name: "spoofed"})
    )
    (fields,) = journal.sent
    assert fields["MESSAGE"].endswith("hello")
    assert fields["EXTRA_MESSAGE"] == "spoofed"


@pytest.mark.parametrize(
    ("name", "field"),
    [
        ("request-id", "REQUEST_ID"),
        ("user.name", "USER_NAME"),
        ("_private", "EXTRA__PRIVATE"),
        ("2fa", "EXTRA_2FA"),
    ],
)
def test_invalid_field_names_are_sanitised(
    journal: FakeJournal, name: str, field: str
) -> None:
    daiquiri.getLogger("test").info(
        "hello", **typing.cast(dict[str, typing.Any], {name: "value"})
    )
    (fields,) = journal.sent
    assert fields[field] == "value"


def test_send_error_goes_to_handle_error(
    journal: FakeJournal, monkeypatch: pytest.MonkeyPatch
) -> None:
    def broken_send(*args: typing.Any, **kwargs: typing.Any) -> None:
        raise OSError("journal unavailable")

    errors: list[logging.LogRecord] = []
    monkeypatch.setattr(journal, "send", broken_send)
    monkeypatch.setattr(handlers.JournalHandler, "handleError", errors.append)
    daiquiri.getLogger("test").info("hello")
    assert len(errors) == 1
