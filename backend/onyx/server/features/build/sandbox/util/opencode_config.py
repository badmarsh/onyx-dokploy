"""Shared opencode configuration generation.

This module provides a centralized way to generate opencode.json configuration
that is consistent across local and Kubernetes sandbox environments.
"""

import os
from typing import Any


DEFAULT_ALLOWED_EXTERNAL_DIRECTORIES = (
    "/workspace/files",
    "/workspace/demo_data",
    os.environ.get("PERSISTENT_DOCUMENT_STORAGE_PATH", "/app/file-system"),
)


def _normalize_directory_rule(path: str) -> str:
    """Normalize external directory rules while preserving the root path."""
    path = path.strip()
    if not path:
        return ""
    normalized = path.rstrip("/")
    return normalized or "/"


def _build_external_directory_permissions() -> dict[str, str]:
    """Build allowlist-style external directory permissions.

    The local Craft sandbox runs sessions under a shared container, so the
    default posture remains deny-by-default. We explicitly allow the standard
    knowledge directories plus any extra directories supplied via
    OPENCODE_ALLOWED_EXTERNAL_DIRECTORIES.
    """
    permissions: dict[str, str] = {"*": "deny"}
    configured_dirs = os.environ.get("OPENCODE_ALLOWED_EXTERNAL_DIRECTORIES", "")
    allowed_dirs = list(DEFAULT_ALLOWED_EXTERNAL_DIRECTORIES)
    allowed_dirs.extend(configured_dirs.split(","))

    for raw_path in allowed_dirs:
        path = _normalize_directory_rule(raw_path)
        if not path:
            continue
        permissions[path] = "allow"
        permissions[f"{path}/**"] = "allow"

    return permissions


def build_opencode_config(
    provider: str,
    model_name: str,
    api_key: str | None = None,
    api_base: str | None = None,
    disabled_tools: list[str] | None = None,
    dev_mode: bool = False,
) -> dict[str, Any]:
    """Build opencode.json configuration dict.

    Creates the configuration structure for the opencode CLI agent with
    provider-specific settings for thinking/reasoning and tool permissions.

    Args:
        provider: LLM provider type (e.g., "openai", "anthropic")
        model_name: Model name (e.g., "claude-sonnet-4-5", "gpt-4o")
        api_key: Optional API key for the provider
        api_base: Optional custom API base URL
        disabled_tools: Optional list of tools to disable (e.g., ["question", "webfetch"])
        dev_mode: If True, allow all external directories. If False (Docker/Kubernetes),
                  whitelist only the standard knowledge directories and any
                  paths from OPENCODE_ALLOWED_EXTERNAL_DIRECTORIES.

    Returns:
        Configuration dict ready to be serialized to JSON
    """
    opencode_model = f"{provider}/{model_name}"

    config: dict[str, Any] = {
        "$schema": "https://opencode.ai/config.json",
        "model": opencode_model,
        "provider": {},
    }

    provider_config: dict[str, Any] = {}

    if api_key:
        provider_config["options"] = {"apiKey": api_key}

    if api_base:
        provider_config["api"] = api_base

    options: dict[str, Any] = {}

    if provider == "openai":
        options["reasoningEffort"] = "high"
    elif provider == "anthropic":
        options["thinking"] = {
            "type": "enabled",
            "budgetTokens": 16000,
        }
    elif provider == "google":
        options["thinking_budget"] = 16000
        options["thinking_level"] = "high"
    elif provider == "bedrock":
        options["thinking"] = {
            "type": "enabled",
            "budgetTokens": 16000,
        }
    elif provider == "azure":
        options["reasoningEffort"] = "high"

    if options:
        provider_config["models"] = {
            model_name: {
                "options": options,
            }
        }

    config["provider"][provider] = provider_config

    config["permission"] = {
        "bash": {
            "rm": "deny",
            "ssh": "deny",
            "scp": "deny",
            "sftp": "deny",
            "ftp": "deny",
            "telnet": "deny",
            "nc": "deny",
            "netcat": "deny",
            "tac": "deny",
            "nl": "deny",
            "od": "deny",
            "xxd": "deny",
            "hexdump": "deny",
            "strings": "deny",
            "base64": "deny",
            "*": "allow",
        },
        "edit": {
            "opencode.json": "deny",
            "**/opencode.json": "deny",
            "*": "allow",
        },
        "write": {
            "opencode.json": "deny",
            "**/opencode.json": "deny",
            "*": "allow",
        },
        "read": {
            "*": "allow",
            "opencode.json": "deny",
            "**/opencode.json": "deny",
        },
        "grep": {
            "*": "allow",
            "opencode.json": "deny",
            "**/opencode.json": "deny",
        },
        "glob": {
            "*": "allow",
            "opencode.json": "deny",
            "**/opencode.json": "deny",
        },
        "list": "allow",
        "lsp": "allow",
        "patch": "allow",
        "skill": "allow",
        "question": "allow",
        "webfetch": "allow",
        "external_directory": (
            "allow" if dev_mode else _build_external_directory_permissions()
        ),
    }

    if disabled_tools:
        for tool in disabled_tools:
            config["permission"][tool] = "deny"

    return config
