"""Minimal Flame-side bridge for the Phase 1 connection proof of concept.

This module deliberately uses only the Python standard library plus the
Autodesk-provided flame module.
"""

from __future__ import annotations

import os
import socket
import threading
import traceback
from pathlib import Path
from typing import Any, Callable, Mapping

from .bridge_client import default_socket_path
from .protocol import (
    MAX_MESSAGE_BYTES,
    BridgeProtocolError,
    decode_message,
    encode_message,
    error_response,
    success_response,
    validate_request,
)

_VALID_TABS = {"MediaHub", "Conform", "Timeline", "Effects", "Batch", "Tools"}


class MainThreadTimeoutError(TimeoutError):
    """Raised when Flame does not run a scheduled idle callback in time."""


class NativeActionsDisabledError(PermissionError):
    """Raised when an experimental native-action backend is disabled."""


class FlameMainThreadScheduler:
    """Schedule Flame work through flame.schedule_idle_event and wait."""

    def __init__(self, flame_module: Any, timeout: float = 10.0) -> None:
        self._flame = flame_module
        self._timeout = timeout

    def call(self, function: Callable[[], Any]) -> Any:
        completed = threading.Event()
        state: dict[str, Any] = {}

        def run_on_main_thread() -> None:
            try:
                state["result"] = function()
            except BaseException as exc:
                state["exception"] = exc
                state["traceback"] = traceback.format_exc()
            finally:
                completed.set()

        self._flame.schedule_idle_event(run_on_main_thread)
        if not completed.wait(self._timeout):
            raise MainThreadTimeoutError(
                "Flame did not execute the scheduled idle callback within "
                f"{self._timeout:g} seconds"
            )
        if "exception" in state:
            exc = state["exception"]
            raise RuntimeError(
                f"{type(exc).__name__}: {exc}\n{state.get('traceback', '')}"
            ) from exc
        return state.get("result")


class ImmediateScheduler:
    """Scheduler used by tests; executes the function immediately."""

    def call(self, function: Callable[[], Any]) -> Any:
        return function()


class FlameRuntime:
    """Small adapter around the Autodesk flame module."""

    def __init__(self, flame_module: Any, *, native_actions_enabled: bool = False) -> None:
        self.flame = flame_module
        self.native_actions_enabled = native_actions_enabled

    def capabilities(self) -> dict[str, Any]:
        return {
            "bridge_protocol": 1,
            "backends": {
                "python_api": {"available": True},
                "native_shortcut": {
                    "available": hasattr(self.flame, "execute_shortcut"),
                    "enabled": self.native_actions_enabled,
                    "live_verified": False,
                },
                "native_button": {
                    "available": hasattr(self.flame, "press_button"),
                    "enabled": self.native_actions_enabled,
                    "live_verified": False,
                },
            },
            "raw_python": {"available": False, "reason": "not exposed in Phase 1"},
            "ui_automation": {"available": False, "reason": "not implemented"},
        }

    def status(self) -> dict[str, Any]:
        context = self.get_context()
        selection = self.get_selection()
        return {
            "connected": True,
            "flame_version": context["flame_version"],
            "current_tab": context["current_tab"],
            "project": context["project"],
            "selection_count": len(selection["entries"]),
            "native_actions_enabled": self.native_actions_enabled,
        }

    def get_context(self) -> dict[str, Any]:
        project = self.flame.projects.current_project
        workspace = getattr(project, "current_workspace", None)
        return {
            "flame_version": _safe_call(self.flame, "get_version"),
            "flame_version_stamp": _safe_call(self.flame, "get_version_stamp"),
            "current_tab": _safe_call(self.flame, "get_current_tab"),
            "project": _object_ref(project),
            "workspace": _object_ref(workspace) if workspace is not None else None,
        }

    def get_selection(self) -> dict[str, Any]:
        entries = list(getattr(self.flame.media_panel, "selected_entries", []) or [])
        return {
            "scope": "media_panel",
            "entries": [_object_ref(entry) for entry in entries],
        }

    def set_current_tab(self, tab: str) -> tuple[dict[str, Any], dict[str, Any]]:
        if tab not in _VALID_TABS:
            raise ValueError(
                f"tab must be one of {', '.join(sorted(_VALID_TABS))}; got {tab!r}"
            )
        before = _safe_call(self.flame, "get_current_tab")
        call_result = self.flame.set_current_tab(tab)
        after = _safe_call(self.flame, "get_current_tab")
        return (
            {
                "requested_tab": tab,
                "before": before,
                "call_result": bool(call_result),
                "after": after,
            },
            {
                "ok": after == tab,
                "method": "flame.get_current_tab",
                "observed": after,
                "expected": tab,
            },
        )

    def execute_shortcut(self, description: str) -> tuple[dict[str, Any], dict[str, Any]]:
        self._require_native_actions()
        if not description:
            raise ValueError("description must be a non-empty string")
        call_result = self.flame.execute_shortcut(description)
        return (
            {"description": description, "call_result": bool(call_result)},
            {
                "ok": None,
                "method": "not_yet_defined",
                "note": "Semantic verification must be defined per shortcut.",
            },
        )

    def press_button(
        self, name: str, param: float = 0.0
    ) -> tuple[dict[str, Any], dict[str, Any]]:
        self._require_native_actions()
        if not name:
            raise ValueError("name must be a non-empty string")
        call_result = self.flame.press_button(name, param)
        return (
            {"name": name, "param": param, "call_result": bool(call_result)},
            {
                "ok": None,
                "method": "not_yet_defined",
                "note": "Semantic verification must be defined per button.",
            },
        )

    def _require_native_actions(self) -> None:
        if not self.native_actions_enabled:
            raise NativeActionsDisabledError(
                "native actions are disabled; start the bridge with "
                "enable_native_actions=True for an isolated test project"
            )


class FlameBridgeApplication:
    """Dispatch normalized bridge requests to a Flame runtime."""

    _BACKENDS = {
        "status": "python_api",
        "capabilities": "bridge",
        "get_context": "python_api",
        "get_selection": "python_api",
        "set_current_tab": "python_api",
        "execute_shortcut": "native_shortcut",
        "press_button": "native_button",
    }

    def __init__(self, runtime: FlameRuntime, scheduler: Any) -> None:
        self.runtime = runtime
        self.scheduler = scheduler

    def handle(self, payload: Mapping[str, Any]) -> dict[str, Any]:
        try:
            request = validate_request(payload)
        except BridgeProtocolError as exc:
            return error_response(
                request_id=_string_or_none(payload.get("id")),
                method=_string_or_none(payload.get("method")),
                backend="bridge_protocol",
                error_type=type(exc).__name__,
                message=str(exc),
            )

        method = request["method"]
        backend = self._BACKENDS.get(method, "bridge")
        try:
            result, verification = self.scheduler.call(
                lambda: self._dispatch(method, request["params"])
            )
            return success_response(
                request,
                backend=backend,
                result=result,
                verification=verification,
            )
        except Exception as exc:
            return error_response(
                request_id=request["id"],
                method=method,
                backend=backend,
                error_type=type(exc).__name__,
                message=str(exc),
            )

    def _dispatch(
        self, method: str, params: Mapping[str, Any]
    ) -> tuple[Any, Mapping[str, Any] | None]:
        if method == "status":
            return self.runtime.status(), None
        if method == "capabilities":
            return self.runtime.capabilities(), None
        if method == "get_context":
            return self.runtime.get_context(), None
        if method == "get_selection":
            return self.runtime.get_selection(), None
        if method == "set_current_tab":
            return self.runtime.set_current_tab(_require_string(params, "tab"))
        if method == "execute_shortcut":
            return self.runtime.execute_shortcut(
                _require_string(params, "description")
            )
        if method == "press_button":
            name = _require_string(params, "name")
            param = params.get("param", 0.0)
            if not isinstance(param, (int, float)):
                raise ValueError("param must be a number")
            return self.runtime.press_button(name, float(param))
        raise ValueError(f"unknown bridge method {method!r}")


class UnixSocketBridgeServer:
    """Experimental local Unix-domain socket server used by Flame."""

    def __init__(
        self,
        application: FlameBridgeApplication,
        socket_path: str | None = None,
    ) -> None:
        self.application = application
        self.socket_path = socket_path or default_socket_path()
        self._stop = threading.Event()
        self._thread: threading.Thread | None = None

    def start(self) -> threading.Thread:
        if self._thread is not None and self._thread.is_alive():
            return self._thread
        self._thread = threading.Thread(
            target=self.serve_forever,
            name="DGFlameMCPBridge",
            daemon=True,
        )
        self._thread.start()
        return self._thread

    def serve_forever(self) -> None:
        if not hasattr(socket, "AF_UNIX"):
            raise RuntimeError("Unix-domain sockets are not supported on this platform")

        path = Path(self.socket_path)
        path.parent.mkdir(parents=True, exist_ok=True)
        _prepare_socket_path(path)

        listener = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        try:
            listener.bind(str(path))
            os.chmod(path, 0o600)
            listener.listen(8)
            listener.settimeout(0.25)
            while not self._stop.is_set():
                try:
                    connection, _ = listener.accept()
                except socket.timeout:
                    continue
                with connection:
                    self._handle_connection(connection)
        finally:
            listener.close()
            try:
                path.unlink()
            except FileNotFoundError:
                pass

    def stop(self) -> None:
        self._stop.set()
        if self._thread is not None:
            self._thread.join(timeout=1.0)

    def _handle_connection(self, connection: socket.socket) -> None:
        try:
            raw = _recv_line(connection)
            payload = decode_message(raw)
            response = self.application.handle(payload)
        except Exception as exc:
            response = error_response(
                request_id=None,
                method=None,
                backend="bridge_protocol",
                error_type=type(exc).__name__,
                message=str(exc),
            )
        try:
            connection.sendall(encode_message(response))
        except OSError:
            pass


_SERVER: UnixSocketBridgeServer | None = None


def start_bridge(
    *,
    socket_path: str | None = None,
    enable_native_actions: bool | None = None,
) -> UnixSocketBridgeServer:
    """Start the singleton bridge from inside Flame."""
    global _SERVER
    if _SERVER is not None:
        return _SERVER

    import flame  # type: ignore[import-not-found]

    if enable_native_actions is None:
        enable_native_actions = (
            os.environ.get("DG_FLAME_MCP_ENABLE_NATIVE_ACTIONS", "").lower()
            in {"1", "true", "yes", "on"}
        )

    runtime = FlameRuntime(
        flame,
        native_actions_enabled=bool(enable_native_actions),
    )
    app = FlameBridgeApplication(runtime, FlameMainThreadScheduler(flame))
    _SERVER = UnixSocketBridgeServer(app, socket_path)
    _SERVER.start()
    return _SERVER


def stop_bridge() -> None:
    """Stop the singleton Flame bridge."""
    global _SERVER
    if _SERVER is not None:
        _SERVER.stop()
        _SERVER = None


def _prepare_socket_path(path: Path) -> None:
    if not path.exists():
        return
    probe = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
    try:
        probe.settimeout(0.2)
        probe.connect(str(path))
    except OSError:
        path.unlink(missing_ok=True)
    else:
        raise RuntimeError(f"a DG Flame MCP bridge is already listening at {path}")
    finally:
        probe.close()


def _recv_line(connection: socket.socket) -> bytes:
    chunks: list[bytes] = []
    size = 0
    while True:
        chunk = connection.recv(65536)
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
            raise BridgeProtocolError("bridge request exceeds protocol limit")
    if not chunks and size == 0:
        raise BridgeProtocolError("empty bridge request")
    return b"".join(chunks)


def _require_string(params: Mapping[str, Any], key: str) -> str:
    value = params.get(key)
    if not isinstance(value, str) or not value:
        raise ValueError(f"{key} must be a non-empty string")
    return value


def _string_or_none(value: Any) -> str | None:
    return value if isinstance(value, str) else None


def _safe_call(obj: Any, name: str) -> Any:
    function = getattr(obj, name, None)
    if function is None:
        return None
    try:
        return _json_value(function())
    except Exception:
        return None


def _object_ref(obj: Any) -> dict[str, Any]:
    result: dict[str, Any] = {"type": type(obj).__name__}
    for name in ("name", "uid"):
        try:
            value = getattr(obj, name)
        except Exception:
            continue
        result[name] = _json_value(value)
    return result


def _json_value(value: Any) -> Any:
    if value is None or isinstance(value, (bool, int, float, str)):
        return value
    if isinstance(value, (list, tuple)):
        return [_json_value(item) for item in value]
    if isinstance(value, dict):
        return {str(key): _json_value(item) for key, item in value.items()}
    return str(value)
