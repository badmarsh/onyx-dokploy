from pathlib import Path

from onyx.server.features.build.sandbox.local.agent_client import (
    _build_session_environment,
)


def test_build_session_environment_uses_session_local_directories(
    tmp_path: Path,
) -> None:
    env = _build_session_environment(str(tmp_path))

    assert env["HOME"] == str(tmp_path / ".home")
    assert env["TMPDIR"] == str(tmp_path / "tmp")
    assert env["XDG_CACHE_HOME"] == str(tmp_path / ".cache")
    assert env["CRAFT_REPOS_DIR"] == str(tmp_path / "repos")
    assert env["CRAFT_DOWNLOADS_DIR"] == str(tmp_path / "downloads")
    assert env["CRAFT_TMP_DIR"] == str(tmp_path / "tmp")

    for directory_name in (".home", "tmp", ".cache", "repos", "downloads"):
        assert (tmp_path / directory_name).is_dir()
