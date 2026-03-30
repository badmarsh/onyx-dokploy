import signal
from pathlib import Path
from unittest.mock import Mock

from onyx.server.features.build.sandbox.local.process_manager import ProcessManager


def test_start_nextjs_server_uses_isolated_process_group(
    monkeypatch,
    tmp_path: Path,
) -> None:
    web_dir = tmp_path / "web"
    web_dir.mkdir()
    (web_dir / "package.json").write_text("{}")

    process = Mock()
    process.pid = 1234

    captured_args: tuple[object, ...] = ()
    captured_kwargs: dict[str, object] = {}

    def mock_popen(*args, **kwargs):  # type: ignore[no-untyped-def]
        nonlocal captured_args
        captured_args = args
        captured_kwargs.update(kwargs)
        return process

    manager = ProcessManager()

    monkeypatch.setattr(
        "onyx.server.features.build.sandbox.local.process_manager.subprocess.Popen",
        mock_popen,
    )
    monkeypatch.setattr(manager, "_wait_for_server", lambda *args, **kwargs: True)

    started_process = manager.start_nextjs_server(web_dir=web_dir, port=3001)

    assert started_process is process
    assert captured_kwargs["start_new_session"] is True
    assert captured_kwargs["cwd"] == web_dir
    assert captured_args == (
        ["npm", "run", "dev", "--", "--webpack", "-p", "3001"],
    )


def test_terminate_process_kills_process_group_when_isolated(monkeypatch) -> None:
    manager = ProcessManager()
    signals: list[tuple[int, int]] = []

    monkeypatch.setattr(manager, "is_process_running", lambda pid: True)
    monkeypatch.setattr(
        "onyx.server.features.build.sandbox.local.process_manager.os.getpgid",
        lambda pid: 4321,
    )
    monkeypatch.setattr(
        "onyx.server.features.build.sandbox.local.process_manager.os.getpgrp",
        lambda: 9999,
    )
    monkeypatch.setattr(
        "onyx.server.features.build.sandbox.local.process_manager.os.killpg",
        lambda pgid, sig: signals.append((pgid, sig)),
    )
    monkeypatch.setattr(manager, "_is_process_group_running", lambda pgid: False)

    assert manager.terminate_process(4321) is True
    assert signals == [(4321, signal.SIGTERM)]


def test_terminate_process_kills_child_tree_when_group_is_not_isolated(
    monkeypatch,
) -> None:
    manager = ProcessManager()
    running = {100: True, 101: True, 102: True}
    signals: list[tuple[int, int]] = []

    monkeypatch.setattr(manager, "is_process_running", lambda pid: running.get(pid, False))
    monkeypatch.setattr(
        "onyx.server.features.build.sandbox.local.process_manager.os.getpgid",
        lambda pid: 50,
    )
    monkeypatch.setattr(
        "onyx.server.features.build.sandbox.local.process_manager.os.getpgrp",
        lambda: 50,
    )
    monkeypatch.setattr(manager, "_get_child_process_ids", lambda pid: [101, 102])

    def mock_kill(pid: int, sig: int) -> None:
        signals.append((pid, sig))
        running[pid] = False

    monkeypatch.setattr(
        "onyx.server.features.build.sandbox.local.process_manager.os.kill",
        mock_kill,
    )

    assert manager.terminate_process(100) is True
    assert signals == [
        (100, signal.SIGTERM),
        (101, signal.SIGTERM),
        (102, signal.SIGTERM),
    ]
