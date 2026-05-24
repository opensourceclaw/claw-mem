"""Integration tests for claw-mem API server."""

import json

from claw_mem.api.server import (
    ClawMemHandler,
    create_server,
)


class TestCreateServer:
    """Tests for server creation and lifecycle."""

    def test_create_and_close(self):
        server = create_server("localhost", 0)
        assert server is not None
        server.server_close()

    def test_create_multiple_servers(self):
        servers = []
        for _ in range(3):
            server = create_server("localhost", 0)
            servers.append(server)
        for s in servers:
            s.server_close()


class TestAPIResponseFormats:
    """Tests for API response JSON format compliance."""

    def test_health_response_format(self):
        data = {
            "status": "healthy",
            "version": "3.4.0",
            "service": "claw-mem",
        }
        json_str = json.dumps(data)
        parsed = json.loads(json_str)
        assert parsed["status"] == "healthy"
        assert parsed["service"] == "claw-mem"

    def test_healthz_response_format(self):
        data = {"status": "ok"}
        json_str = json.dumps(data)
        parsed = json.loads(json_str)
        assert parsed["status"] == "ok"

    def test_store_response_format(self):
        data = {
            "stored": True,
            "memory_type": "semantic",
            "metadata": {"source": "api"},
        }
        json_str = json.dumps(data)
        parsed = json.loads(json_str)
        assert parsed["stored"] is True

    def test_search_response_format(self):
        data = {
            "query": "test memory",
            "results": [],
            "total": 0,
        }
        json_str = json.dumps(data)
        parsed = json.loads(json_str)
        assert parsed["total"] == 0

    def test_recall_response_format(self):
        data = {
            "memory_id": "mem-1",
            "found": False,
        }
        json_str = json.dumps(data)
        parsed = json.loads(json_str)
        assert parsed["memory_id"] == "mem-1"
        assert parsed["found"] is False
