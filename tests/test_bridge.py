from __future__ import annotations

import socket
import tempfile
import time
import unittest
from pathlib import Path

from dg_flame_mcp.bridge_client import FlameBridgeClient
from dg_flame_mcp.flame_bridge import (
    FlameBridgeApplication,
    FlameRuntime,
    ImmediateScheduler,
    UnixSocketBridgeServer,
)
from dg_flame_mcp.protocol import new_request


class NamedObject:
    def __init__(self, name: str, uid: str | None = None) -> None:
        self.name = name
        if uid is not None:
            self.uid = uid


class FakeProjects:
    def __init__(self) -> None:
        self.current_project = NamedObject("Demo Project")
        self.current_project.current_workspace = NamedObject("Workspace")


class FakeMediaPanel:
    def __init__(self) -> None:
        self.selected_entries = [NamedObject("clip_A", "uid-1")]


class FakeFlame:
    def __init__(self) -> None:
        self.projects = FakeProjects()
        self.media_panel = FakeMediaPanel()
        self._tab = "Batch"
        self.shortcuts: list[str] = []
        self.buttons: list[tuple[str, float]] = []

    def get_version(self) -> str:
        return "2026.2"

    def get_version_stamp(self) -> str:
        return "2026.2.test"

    def get_current_tab(self) -> str:
        return self._tab

    def set_current_tab(self, tab: str) -> bool:
        self._tab = tab
        return True

    def execute_shortcut(self, description: str) -> bool:
        self.shortcuts.append(description)
        return True

    def press_button(self, name: str, param: float = 0.0) -> bool:
        self.buttons.append((name, param))
        return True


class FlameBridgeApplicationTests(unittest.TestCase):
    def setUp(self) -> None:
        self.flame = FakeFlame()
        self.runtime = FlameRuntime(self.flame)
        self.app = FlameBridgeApplication(self.runtime, ImmediateScheduler())

    def call(self, method: str, params: dict | None = None) -> dict:
        return self.app.handle(new_request(method, params))

    def test_context_and_selection(self) -> None:
        context = self.call("get_context")
        self.assertTrue(context["ok"])
        self.assertEqual(context["result"]["flame_version"], "2026.2")
        self.assertEqual(context["result"]["project"]["name"], "Demo Project")

        selection = self.call("get_selection")
        self.assertTrue(selection["ok"])
        self.assertEqual(selection["result"]["scope"], "media_panel")
        self.assertEqual(selection["result"]["entries"][0]["uid"], "uid-1")

    def test_set_current_tab_verifies_observed_state(self) -> None:
        response = self.call("set_current_tab", {"tab": "Timeline"})
        self.assertTrue(response["ok"])
        self.assertEqual(response["backend"], "python_api")
        self.assertTrue(response["verification"]["ok"])
        self.assertEqual(self.flame.get_current_tab(), "Timeline")

    def test_native_actions_are_disabled_by_default(self) -> None:
        response = self.call("execute_shortcut", {"description": "Example"})
        self.assertFalse(response["ok"])
        self.assertEqual(response["backend"], "native_shortcut")
        self.assertEqual(response["error"]["type"], "NativeActionsDisabledError")

    def test_native_actions_can_be_enabled_for_poc(self) -> None:
        runtime = FlameRuntime(self.flame, native_actions_enabled=True)
        app = FlameBridgeApplication(runtime, ImmediateScheduler())
        response = app.handle(
            new_request("execute_shortcut", {"description": "Example"})
        )
        self.assertTrue(response["ok"])
        self.assertEqual(self.flame.shortcuts, ["Example"])
        self.assertIsNone(response["verification"]["ok"])


@unittest.skipUnless(hasattr(socket, "AF_UNIX"), "requires Unix-domain sockets")
class UnixSocketRoundTripTests(unittest.TestCase):
    def test_round_trip(self) -> None:
        flame = FakeFlame()
        app = FlameBridgeApplication(
            FlameRuntime(flame),
            ImmediateScheduler(),
        )
        with tempfile.TemporaryDirectory() as tmp:
            path = str(Path(tmp) / "bridge.sock")
            server = UnixSocketBridgeServer(app, path)
            thread = server.start()

            deadline = time.monotonic() + 2.0
            while not Path(path).exists() and time.monotonic() < deadline:
                time.sleep(0.01)

            try:
                client = FlameBridgeClient(path, timeout=1.0)
                response = client.call("status")
                self.assertTrue(response["ok"])
                self.assertEqual(response["result"]["flame_version"], "2026.2")
            finally:
                server.stop()
                thread.join(timeout=1.0)


if __name__ == "__main__":
    unittest.main()
