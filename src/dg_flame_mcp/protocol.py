"""Wire protocol shared by the MCP server and the Flame-side bridge."""

from __future__ import annotations

import json
import uuid
from typing import Any, Mapping

PROTOCOL_VERSION = 1
MAX_MESSAGE_BYTES = 1024 * 1024


class BridgeProtocolError(ValueError):
    """Raised when a bridge message is malformed."""


def new_request(method: str, params: Mapping[str, Any] | None = None) -> dict[str, Any]:
    """Build a request envelope for the local Flame bridge."""
    if not method:
        raise BridgeProtocolError("method must be a non-empty string")
    return {
        "protocol_version": PROTOCOL_VERSION,
        "id": uuid.uuid4().hex,
        "method": method,
        "params": dict(params or {}),
    }


def validate_request(payload: Mapping[str, Any]) -> dict[str, Any]:
    """Validate and normalize a request received by the Flame bridge."""
    version = payload.get("protocol_version")
    if version != PROTOCOL_VERSION:
        raise BridgeProtocolError(
            f"unsupported protocol_version {version!r}; expected {PROTOCOL_VERSION}"
        )

    request_id = payload.get("id")
    method = payload.get("method")
    params = payload.get("params", {})

    if not isinstance(request_id, str) or not request_id:
        raise BridgeProtocolError("id must be a non-empty string")
    if not isinstance(method, str) or not method:
        raise BridgeProtocolError("method must be a non-empty string")
    if not isinstance(params, dict):
        raise BridgeProtocolError("params must be an object")

    return {
        "protocol_version": PROTOCOL_VERSION,
        "id": request_id,
        "method": method,
        "params": params,
    }


def success_response(
    request: Mapping[str, Any],
    *,
    backend: str,
    result: Any,
    verification: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    """Build a normalized successful response."""
    return {
        "protocol_version": PROTOCOL_VERSION,
        "id": request["id"],
        "method": request["method"],
        "ok": True,
        "backend": backend,
        "result": result,
        "error": None,
        "verification": dict(verification) if verification is not None else None,
    }


def error_response(
    *,
    request_id: str | None,
    method: str | None,
    backend: str,
    error_type: str,
    message: str,
    details: Any = None,
) -> dict[str, Any]:
    """Build a normalized error response."""
    return {
        "protocol_version": PROTOCOL_VERSION,
        "id": request_id,
        "method": method,
        "ok": False,
        "backend": backend,
        "result": None,
        "error": {
            "type": error_type,
            "message": message,
            "details": details,
        },
        "verification": None,
    }


def encode_message(payload: Mapping[str, Any]) -> bytes:
    """Encode one newline-delimited JSON message."""
    data = json.dumps(payload, ensure_ascii=False, separators=(",", ":")).encode("utf-8")
    if len(data) > MAX_MESSAGE_BYTES:
        raise BridgeProtocolError(
            f"message exceeds {MAX_MESSAGE_BYTES} byte protocol limit"
        )
    return data + b"\n"


def decode_message(data: bytes) -> dict[str, Any]:
    """Decode one JSON message."""
    if len(data) > MAX_MESSAGE_BYTES:
        raise BridgeProtocolError(
            f"message exceeds {MAX_MESSAGE_BYTES} byte protocol limit"
        )
    try:
        payload = json.loads(data.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise BridgeProtocolError(f"invalid JSON message: {exc}") from exc
    if not isinstance(payload, dict):
        raise BridgeProtocolError("message must be a JSON object")
    return payload
