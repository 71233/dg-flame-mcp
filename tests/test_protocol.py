from __future__ import annotations

import unittest

from dg_flame_mcp.protocol import (
    BridgeProtocolError,
    decode_message,
    encode_message,
    new_request,
    validate_request,
)


class ProtocolTests(unittest.TestCase):
    def test_request_round_trip(self) -> None:
        request = new_request("get_context", {"detail": True})
        decoded = decode_message(encode_message(request).rstrip(b"\n"))
        self.assertEqual(validate_request(decoded), request)

    def test_rejects_unknown_protocol_version(self) -> None:
        request = new_request("status")
        request["protocol_version"] = 999
        with self.assertRaises(BridgeProtocolError):
            validate_request(request)


if __name__ == "__main__":
    unittest.main()
