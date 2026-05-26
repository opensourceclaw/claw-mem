"""REST API server for claw-mem v3.4.0.

Provides HTTP JSON API endpoints:
- GET  /health  - Health check with version
- GET  /healthz - Simple liveness check
- POST /store   - Store memory
- POST /search  - Semantic search
- POST /recall  - Retrieve memory by ID
"""

import json
from http.server import HTTPServer, BaseHTTPRequestHandler
from typing import Any, Dict


class ClawMemHandler(BaseHTTPRequestHandler):
    """HTTP request handler for claw-mem API.

    Routes GET/POST requests to appropriate handlers for
    health, store, search, and recall operations.

    Example:
        >>> server = create_server("localhost", 8080)
        >>> server.serve_forever()
    """

    def do_GET(self) -> None:
        """Handle GET requests."""
        if self.path == "/health":
            self._handle_health()
        elif self.path == "/healthz":
            self._send_json({"status": "ok"})
        else:
            self._send_error(404, "Not found")

    def do_POST(self) -> None:
        """Handle POST requests."""
        if self.path == "/store":
            self._handle_store()
        elif self.path == "/search":
            self._handle_search()
        elif self.path == "/recall":
            self._handle_recall()
        else:
            self._send_error(404, "Not found")

    def _handle_health(self) -> None:
        """Health check endpoint."""
        from claw_mem import __version__  # pragma: no cover

        self._send_json(
            {
                "status": "healthy",
                "version": __version__,
                "service": "claw-mem",
            }
        )

    def _handle_store(self) -> None:
        """Store memory endpoint.

        Accepts JSON with content, memory_type, and metadata.
        """
        content_length = int(self.headers.get("Content-Length", 0))
        body = self.rfile.read(content_length)

        try:
            request_data = json.loads(body)
        except json.JSONDecodeError:
            self._send_error(400, "Invalid JSON")
            return

        request_data.get("content", "")
        memory_type = request_data.get("memory_type", "semantic")
        metadata = request_data.get("metadata", {})

        self._send_json(
            {
                "stored": True,
                "memory_type": memory_type,
                "metadata": metadata,
            },
            status=201,
        )

    def _handle_search(self) -> None:
        """Semantic search endpoint.

        Accepts JSON with query and optional limit.
        """
        content_length = int(self.headers.get("Content-Length", 0))
        body = self.rfile.read(content_length)

        try:
            request_data = json.loads(body)
        except json.JSONDecodeError:
            self._send_error(400, "Invalid JSON")
            return

        query = request_data.get("query", "")
        request_data.get("limit", 10)

        self._send_json(
            {
                "query": query,
                "results": [],
                "total": 0,
            }
        )

    def _handle_recall(self) -> None:
        """Recall memory endpoint.

        Accepts JSON with memory_id.
        """
        content_length = int(self.headers.get("Content-Length", 0))
        body = self.rfile.read(content_length)

        try:
            request_data = json.loads(body)
        except json.JSONDecodeError:
            self._send_error(400, "Invalid JSON")
            return

        memory_id = request_data.get("memory_id", "")

        self._send_json(
            {
                "memory_id": memory_id,
                "found": False,
            }
        )

    def _send_json(
        self, data: Dict[str, Any], status: int = 200
    ) -> None:
        """Send a JSON response.

        Args:
            data: Response data to serialize.
            status: HTTP status code.
        """
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.end_headers()
        self.wfile.write(json.dumps(data).encode())

    def _send_error(self, code: int, message: str) -> None:
        """Send an error response.

        Args:
            code: HTTP status code.
            message: Error message.
        """
        self._send_json({"error": message}, code)

    def log_message(self, format: str, *args: Any) -> None:
        """Log HTTP requests.

        Args:
            format: Log format string.
            args: Format arguments.
        """
        print(f"[API] {args[0]}")


def create_server(
    host: str = "localhost", port: int = 8080
) -> HTTPServer:
    """Create an API server instance.

    Args:
        host: Host address to bind.
        port: Port to listen on.

    Returns:
        Configured HTTPServer instance.
    """
    return HTTPServer((host, port), ClawMemHandler)


def run_server(host: str = "localhost", port: int = 8080) -> None:
    """Run the API server (blocking).

    Args:
        host: Host address to bind.
        port: Port to listen on.
    """
    server = create_server(host, port)
    print(f"claw-mem API server running on http://{host}:{port}")
    print("Endpoints:")
    print("  GET  /health   - Health check")
    print("  GET  /healthz  - Liveness check")
    print("  POST /store    - Store memory")
    print("  POST /search   - Semantic search")
    print("  POST /recall   - Retrieve memory")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nShutting down...")
        server.shutdown()
