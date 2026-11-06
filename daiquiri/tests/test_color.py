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

import pytest

import daiquiri
from daiquiri.formatter import ColorFormatter

RED = ColorFormatter.LEVEL_COLORS[logging.ERROR]


class TTYStream(io.StringIO):
    def isatty(self) -> bool:
        return True


def _log(stream: io.StringIO) -> str:
    daiquiri.setup(
        outputs=(daiquiri.output.Stream(stream),),
        set_excepthook=False,
        capture_warnings=False,
    )
    daiquiri.getLogger("test").error("boom")
    return stream.getvalue()


def _is_colored(output: str) -> bool:
    return RED in output and ColorFormatter.COLOR_STOP in output


def test_tty_is_colored() -> None:
    assert _is_colored(_log(TTYStream()))


def test_non_tty_is_not_colored() -> None:
    assert not _is_colored(_log(io.StringIO()))


def test_no_color_disables_colors_on_a_tty(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("NO_COLOR", "1")
    output = _log(TTYStream())
    assert "\033[" not in output
    assert output.endswith("test: boom\n")


def test_force_color_enables_colors_without_a_tty(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("FORCE_COLOR", "1")
    assert _is_colored(_log(io.StringIO()))


def test_no_color_wins_over_force_color(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("NO_COLOR", "1")
    monkeypatch.setenv("FORCE_COLOR", "1")
    assert not _is_colored(_log(TTYStream()))


@pytest.mark.parametrize("value", ["0", "false", "no"])
def test_any_non_empty_value_counts(
    monkeypatch: pytest.MonkeyPatch, value: str
) -> None:
    monkeypatch.setenv("NO_COLOR", value)
    assert not _is_colored(_log(TTYStream()))
    monkeypatch.delenv("NO_COLOR")
    monkeypatch.setenv("FORCE_COLOR", value)
    assert _is_colored(_log(io.StringIO()))


def test_empty_values_are_ignored(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("NO_COLOR", "")
    monkeypatch.setenv("FORCE_COLOR", "")
    assert _is_colored(_log(TTYStream()))
    assert not _is_colored(_log(io.StringIO()))
