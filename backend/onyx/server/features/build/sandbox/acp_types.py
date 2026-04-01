"""Shared ACP event marker types for sandbox backends."""

from dataclasses import dataclass


@dataclass
class SSEKeepalive:
    """Marker event instructing the API layer to emit an SSE keepalive comment."""
