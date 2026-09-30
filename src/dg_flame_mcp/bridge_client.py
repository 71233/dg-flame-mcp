"""Client for the local Flame bridge."""

from __future__ import annotations

import os
import socket
import tempfile
from pathlib import Path
from typing import Any, Mapping

from .protocol import (
    MAX_MESSAGE_BYTES,
    BridgeProtocolError,
    decode_message,
    encode_message,
    new_request,
)


class BridgeUnavailableError(ConnectionError):
    """Raised when the Flame-side bridge cannot be reached."""


def default_socket_path() -> str:
    """Return the default per-user Unix-domain socket path."""
    configured = os.environ.get("DG_FLAME_MCP_SOCKET")
    if configured:
        return configured
    uid = getattr(os, "getuid", lambda: os.getpid())()
    return str(Path(tempfile.gettempdir()) / f"dg-flame-mcp-{uid}.sock")


class FlameBridgeClient:
    """One-request-per-connection client for the experimental bridge protocol."""

    def __init__(self, socket_path: str | None = None, timeout: float = 5.0) -> None:
        self.socket_path = socket_path or default_socket_path()
        self.timeout = timeout

    def call(
        self, method: str, params: Mapping[str, Any] | None = None
    ) -> dict[str, Any]:
        request = new_request(method, params)

        if not hasattr(socket, "AF_UNIX"):
            raise BridgeUnavailableError(
                "Unix-domain sockets are not supported on this platform"
            )

        try:
            with socket.socket(socket.AF_UNIX, socket.SOCK_STREAM) as sock:
                sock.settimeout(self.timeout)
                sock.connect(self.socket_path)
                sock.sendall(encode_message(request))
                raw = _recv_line(sock)
        except OSError as exc:
            raise BridgeUnavailableError(
                f"cannot reach Flame bridge at {self.socket_path}: {exc}"
            ) from exc

        response = decode_message(raw)
        if response.get("id") != request["id"]:
            raise BridgeProtocolError(
                "bridge response id does not match the request id"
            )
        return response


def _recv_line(sock: socket.socket) -> bytes:
    chunks: list[bytes] = []
    size = 0
    while True:
        chunk = sock.recv(65536)
        if not chunk:
            break
        newline = chunk.find(b"\n")
        if newline >= 0:
            chunks.append(chunk[:newline])
            size += newline
            break
        chunks.append(chunk)
        size += len(chunk)
        if size > MAX_MESSAGE_BYTES:
            raise BridgeProtocolError("bridge message exceeds protocol limit")
    if not chunks and size == 0:
        raise BridgeProtocolError("bridge closed connection without a response")
    return b"".join(chunks)
