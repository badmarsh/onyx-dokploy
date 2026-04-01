import http.client
from pathlib import Path
from unittest.mock import Mock

from onyx.server.features.build.sandbox.local.process_manager import ProcessManager


class _DummyResponse:
    def __init__(self, status: int = 200) -> None:
        self.status = status

    def __enter__(self) -> "_DummyResponse":
        return self

    def __exit__(self, exc_type: object, exc: object, tb: object) -> None:
        return None


def test_wait_for_server_retries_remote_disconnect(
    monkeypatch: object,
) -> None:
    manager = ProcessManager()
    process = Mock()
    process.poll.return_value = None

    responses = iter(
        [
            http.client.RemoteDisconnected("Remote end closed connection"),
            _DummyResponse(),
        ]
    )

    def fake_urlopen(url: str, timeout: int) -> _DummyResponse:
        result = next(responses)
        if isinstance(result, Exception):
            raise result
        return result

    monkeypatch.setattr(
        "onyx.server.features.build.sandbox.local.process_manager.urllib.request.urlopen",
        fake_urlopen,
    )
    monkeypatch.setattr(
        "onyx.server.features.build.sandbox.local.process_manager.time.sleep",
        lambda _: None,
    )

    assert (
        manager._wait_for_server(
            "http://localhost:3017",
            timeout=1,
            poll_interval=0,
            process=process,
        )
        is True
    )


def test_start_nextjs_server_defaults_to_webpack(monkeypatch: object) -> None:
    manager = ProcessManager()
    web_dir = Path("/tmp/fake-web")
    package_json = web_dir / "package.json"

    commands: list[list[str]] = []

    class _DummyProcess:
        pid = 123
        returncode = None

        def poll(self) -> None:
            return None

    monkeypatch.setattr(
        "onyx.server.features.build.sandbox.local.process_manager.Path.exists",
        lambda self: self in {web_dir, package_json},
    )
    monkeypatch.setattr(
        "onyx.server.features.build.sandbox.local.process_manager.subprocess.Popen",
        lambda command, cwd, stdout, stderr: commands.append(command) or _DummyProcess(),
    )
    monkeypatch.setattr(
        manager,
        "_wait_for_server",
        lambda url, timeout, process: True,
    )
    monkeypatch.delenv("SANDBOX_NEXTJS_BUNDLER", raising=False)

    process = manager.start_nextjs_server(web_dir=web_dir, port=3017)

    assert process.pid == 123
    assert commands == [["npm", "run", "dev", "--", "--webpack", "-p", "3017"]]
