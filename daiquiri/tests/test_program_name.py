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
import os
import pathlib
import subprocess
import sys
import threading
import types

import pytest

from daiquiri import output

DAIQUIRI_ROOT = str(pathlib.Path(output.__file__).resolve().parent.parent)

PRINT_NAME = "import daiquiri.output; print(daiquiri.output.get_program_name())\n"


def _main_module(spec_name: str | None) -> types.ModuleType:
    module = types.ModuleType("__main__")
    module.__spec__ = (
        types.SimpleNamespace(name=spec_name) if spec_name is not None else None  # type: ignore[assignment]
    )
    return module


@pytest.mark.parametrize(
    ("spec_name", "argv", "expected"),
    [
        (None, ["/usr/local/bin/script.py", "--flag"], "script.py"),
        (None, ["/usr/local/bin/myapp"], "myapp"),
        ("myapp.__main__", ["/srv/myapp/__main__.py"], "myapp"),
        ("myapp.cli", ["/srv/myapp/cli.py"], "myapp.cli"),
        ("__main__", ["/srv/app.zip"], "app.zip"),
        (None, ["-c"], "python"),
        (None, [""], "python"),
        (None, [], "python"),
    ],
)
def test_get_program_name(
    monkeypatch: pytest.MonkeyPatch,
    spec_name: str | None,
    argv: list[str],
    expected: str,
) -> None:
    monkeypatch.setitem(sys.modules, "__main__", _main_module(spec_name))
    monkeypatch.setattr(sys, "argv", argv)
    assert output.get_program_name() == expected


def test_get_program_name_from_thread(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setitem(sys.modules, "__main__", _main_module(None))
    monkeypatch.setattr(sys, "argv", ["/usr/local/bin/myapp"])
    names: list[str] = []
    thread = threading.Thread(target=lambda: names.append(output.get_program_name()))
    thread.start()
    thread.join()
    assert names == ["myapp"]


def _run(args: list[str], cwd: pathlib.Path) -> str:
    env = dict(os.environ, PYTHONPATH=DAIQUIRI_ROOT)
    return subprocess.run(
        [sys.executable, *args],
        cwd=cwd,
        env=env,
        capture_output=True,
        text=True,
        check=True,
    ).stdout.strip()


def test_get_program_name_real_interpreter(tmp_path: pathlib.Path) -> None:
    package = tmp_path / "myapp"
    package.mkdir()
    (package / "__init__.py").write_text("")
    (package / "__main__.py").write_text(PRINT_NAME)
    (tmp_path / "script.py").write_text(PRINT_NAME)

    assert _run(["-m", "myapp"], tmp_path) == "myapp"
    assert _run(["script.py"], tmp_path) == "script.py"
    assert _run(["-c", PRINT_NAME], tmp_path) == "python"
