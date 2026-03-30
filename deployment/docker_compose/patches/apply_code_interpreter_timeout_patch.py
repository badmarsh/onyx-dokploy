from __future__ import annotations

from pathlib import Path


def _patch_file(path: Path, replacements: list[tuple[str, str]]) -> None:
    text = path.read_text()
    original = text

    for old, new in replacements:
        if new in text:
            continue
        if old not in text:
            print(f"[patch] skipped {path}: expected snippet not found")
            return
        text = text.replace(old, new, 1)

    if text != original:
        path.write_text(text)
        print(f"[patch] updated {path}")
    else:
        print(f"[patch] already patched {path}")


_patch_file(
    Path("/app/app/services/executor_docker.py"),
    replacements=[
        (
            """[self.docker_binary, "version", "--format", "{{.Server.Version}}"],\n                capture_output=True,\n                timeout=5,\n                check=False,""",
            """[self.docker_binary, "version", "--format", "{{.Server.Version}}"],\n                capture_output=True,\n                timeout=10,\n                check=False,""",
        ),
        (
            """[self.docker_binary, "image", "inspect", image_with_tag],\n                capture_output=True,\n                timeout=5,\n                check=False,""",
            """[self.docker_binary, "image", "inspect", image_with_tag],\n                capture_output=True,\n                timeout=10,\n                check=False,""",
        ),
    ],
)

_patch_file(
    Path("/app/app/main.py"),
    replacements=[
        (
            """[docker_bin, "image", "inspect", image_with_tag],\n        capture_output=True,\n        timeout=10,\n        check=False,""",
            """[docker_bin, "image", "inspect", image_with_tag],\n        capture_output=True,\n        timeout=30,\n        check=False,""",
        ),
    ],
)
