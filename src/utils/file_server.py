"""Simple local file server for making local files accessible via URL.

HeyGen API requires audio to be at a public URL. This utility spins up a
temporary HTTP server to serve local files during the pipeline run.
"""

import os
import threading
from functools import partial
from http.server import HTTPServer, SimpleHTTPRequestHandler
from pathlib import Path


class LocalFileServer:
    """Serves local files over HTTP for API consumption."""

    def __init__(self, directory: str, port: int = 8099):
        self.directory = os.path.abspath(directory)
        self.port = port
        self._server = None
        self._thread = None

    def start(self) -> str:
        """Start the file server in a background thread.

        Returns:
            Base URL for accessing files (e.g., http://localhost:8099)
        """
        handler = partial(SimpleHTTPRequestHandler, directory=self.directory)
        self._server = HTTPServer(("0.0.0.0", self.port), handler)
        self._thread = threading.Thread(target=self._server.serve_forever, daemon=True)
        self._thread.start()
        return f"http://localhost:{self.port}"

    def get_url(self, file_path: str) -> str:
        """Get the URL for a local file.

        Args:
            file_path: Absolute or relative path to the file

        Returns:
            HTTP URL to access the file
        """
        abs_path = os.path.abspath(file_path)
        rel_path = os.path.relpath(abs_path, self.directory)
        return f"http://localhost:{self.port}/{rel_path}"

    def stop(self):
        """Stop the file server."""
        if self._server:
            self._server.shutdown()
            self._server = None
