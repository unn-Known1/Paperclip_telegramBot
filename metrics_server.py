"""Tiny HTTP server to expose /metrics for Prometheus scraping."""

import logging
import threading
from http.server import HTTPServer, BaseHTTPRequestHandler

import config

logger = logging.getLogger(__name__)

try:
    from prometheus_client import generate_latest, CONTENT_TYPE_LATEST

    PROMETHEUS_AVAILABLE = True
except ImportError:
    PROMETHEUS_AVAILABLE = False


class _MetricsHandler(BaseHTTPRequestHandler):
    """Serve Prometheus metrics on GET /metrics."""

    def do_GET(self):
        if self.path == "/metrics" and PROMETHEUS_AVAILABLE:
            data = generate_latest()
            self.send_response(200)
            self.send_header("Content-Type", CONTENT_TYPE_LATEST)
            self.end_headers()
            self.wfile.write(data)
        elif self.path == "/healthz":
            self.send_response(200)
            self.end_headers()
            self.wfile.write(b"ok")
        else:
            self.send_response(404)
            self.end_headers()

    def log_message(self, fmt, *args):
        # Silence noisy HTTP logs
        pass


def start_metrics_server() -> None:
    """Start the metrics HTTP server in a background daemon thread."""
    if not config.METRICS_ENABLED:
        return
    if not PROMETHEUS_AVAILABLE:
        logger.warning("METRICS_ENABLED=true but prometheus_client is not installed")
        return

    port = config.METRICS_PORT
    server = HTTPServer(("0.0.0.0", port), _MetricsHandler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    logger.info("Metrics server started on :%d", port)
