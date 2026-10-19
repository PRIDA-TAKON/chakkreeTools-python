"""
Unit tests for AgentStreamer in chakkree_tools/ingetrazo_plugin/agent_streamer.py
"""

import http.server
import json
import threading
import pytest
import yaml

from chakkree_tools.ingetrazo_plugin.agent_streamer import (
    AgentStreamer,
    AgentStreamerError,
    stream_to_ingetrazo,
)
from chakkree_tools.rc.footing import PileCap
from chakkree_tools.rc.column import Column


class MockBridgeHandler(http.server.BaseHTTPRequestHandler):
    """Mock HTTP server handler simulating IngeTrazo Agent Bridge (Port 8482)."""

    def do_GET(self):
        if self.path in ("/", "/api/v1/health"):
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(json.dumps({"status": "ok", "agent": "IngeTrazo Bridge"}).encode("utf-8"))
        else:
            self.send_response(404)
            self.end_headers()

    def do_POST(self):
        content_length = int(self.headers.get("Content-Length", 0))
        body = self.rfile.read(content_length).decode("utf-8")

        if self.path == "/api/v1/error":
            self.send_response(500)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(json.dumps({"error": "Internal Server Error"}).encode("utf-8"))
            return

        # Try parsing body as YAML
        try:
            data = yaml.safe_load(body)
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            res = {
                "success": True,
                "schema": data.get("schema"),
                "elements_count": len(data.get("elements", [])),
            }
            self.wfile.write(json.dumps(res).encode("utf-8"))
        except Exception as e:
            self.send_response(400)
            self.end_headers()
            self.wfile.write(json.dumps({"error": str(e)}).encode("utf-8"))

    def log_message(self, format, *args):
        # Silence logging during tests
        pass


@pytest.fixture
def mock_bridge_server():
    server = http.server.HTTPServer(("127.0.0.1", 0), MockBridgeHandler)
    host, port = server.server_address
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    yield host, port
    server.shutdown()
    server.server_close()


def test_is_bridge_available_online(mock_bridge_server):
    host, port = mock_bridge_server
    streamer = AgentStreamer(host=host, port=port)
    assert streamer.is_bridge_available() is True


def test_is_bridge_available_offline():
    # Use unused port on localhost
    streamer = AgentStreamer(host="127.0.0.1", port=59999, timeout=0.5)
    assert streamer.is_bridge_available() is False


def test_stream_manifest_dict(mock_bridge_server):
    host, port = mock_bridge_server
    streamer = AgentStreamer(host=host, port=port)

    manifest = {
        "schema": "IFC4-Minimal",
        "project": {"name": "Test Bridge Stream"},
        "elements": [{"id": "C1", "class": "IfcColumn"}],
    }

    res = streamer.stream_manifest(manifest)
    assert res["status_code"] == 200
    assert res["success"] is True
    assert res["response"]["elements_count"] == 1
    assert res["response"]["schema"] == "IFC4-Minimal"


def test_stream_manifest_yaml_string(mock_bridge_server):
    host, port = mock_bridge_server
    streamer = AgentStreamer(host=host, port=port)

    yaml_str = """
schema: IFC4-Minimal
project:
  name: String Stream Test
elements:
  - id: F1
    class: IfcFooting
"""

    res = streamer.stream_manifest(yaml_str)
    assert res["status_code"] == 200
    assert res["response"]["elements_count"] == 1


def test_stream_elements(mock_bridge_server):
    host, port = mock_bridge_server
    streamer = AgentStreamer(host=host, port=port)

    f1 = PileCap.create_n_piles(id_str="F1", pile_count=2)
    c1 = Column(id="C1", width=0.3, depth=0.3, height=3.5)

    res = streamer.stream_elements([f1, c1], project_name="Live Stream Test")
    assert res["status_code"] == 200
    assert res["response"]["elements_count"] == 2


def test_stream_to_ingetrazo_convenience(mock_bridge_server):
    host, port = mock_bridge_server
    c1 = Column(id="C1", width=0.4, depth=0.4, height=4.0)

    res = stream_to_ingetrazo([c1], host=host, port=port)
    assert res["status_code"] == 200
    assert res["response"]["elements_count"] == 1


def test_stream_error_handling_server_error(mock_bridge_server):
    host, port = mock_bridge_server
    streamer = AgentStreamer(host=host, port=port)

    with pytest.raises(AgentStreamerError) as exc_info:
        streamer.stream_manifest({"schema": "IFC4-Minimal"}, path="/api/v1/error")
    assert "HTTP 500 Error" in str(exc_info.value)


def test_stream_error_handling_connection_refused():
    streamer = AgentStreamer(host="127.0.0.1", port=59999, timeout=0.5)

    with pytest.raises(AgentStreamerError) as exc_info:
        streamer.stream_manifest({"schema": "IFC4-Minimal"})
    assert "Failed to connect" in str(exc_info.value)
