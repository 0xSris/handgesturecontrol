from __future__ import annotations

import mimetypes
import socket
import threading
import urllib.parse
from dataclasses import dataclass
from functools import partial
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path


@dataclass(frozen=True)
class ShareStatus:
    active: bool
    url: str | None = None
    root: str | None = None
    message: str = "share disabled"


class ShareServer:
    def __init__(self, share_path: str | None, port: int = 8765) -> None:
        self._share_path = Path(share_path).resolve() if share_path else None
        self._port = port
        self._server: ThreadingHTTPServer | None = None
        self._thread: threading.Thread | None = None
        self._url: str | None = None

    @property
    def status(self) -> ShareStatus:
        if self._share_path is None:
            return ShareStatus(False, message="set --share-path to enable")
        if self._server is None:
            return ShareStatus(False, root=str(self._share_path), message="share stopped")
        return ShareStatus(True, self._url, str(self._share_path), "share active")

    def start(self) -> ShareStatus:
        if self._share_path is None:
            return self.status
        if self._server is not None:
            return self.status
        if not self._share_path.exists():
            raise FileNotFoundError(f"Share path does not exist: {self._share_path}")

        root = self._share_path if self._share_path.is_dir() else self._share_path.parent
        handler = partial(ShareRequestHandler, directory=str(root), shared_file=self._share_path if self._share_path.is_file() else None)
        self._server = ThreadingHTTPServer(("", self._port), handler)
        port = self._server.server_address[1]
        self._url = f"http://{local_ip()}:{port}/"
        self._thread = threading.Thread(target=self._server.serve_forever, daemon=True)
        self._thread.start()
        return self.status

    def stop(self) -> ShareStatus:
        if self._server is not None:
            self._server.shutdown()
            self._server.server_close()
            self._server = None
            self._thread = None
            self._url = None
        return self.status

    def toggle(self) -> ShareStatus:
        if self._server is None:
            return self.start()
        return self.stop()

    def close(self) -> None:
        self.stop()


class ShareRequestHandler(SimpleHTTPRequestHandler):
    def __init__(self, *args, shared_file: Path | None = None, **kwargs) -> None:
        self._shared_file = shared_file
        super().__init__(*args, **kwargs)

    def log_message(self, format: str, *args: object) -> None:
        return None

    def do_GET(self) -> None:
        if self.path == "/" and self._shared_file is not None:
            self._send_single_file_download()
            return
        super().do_GET()

    def _send_single_file_download(self) -> None:
        assert self._shared_file is not None
        filename = self._shared_file.name
        body = self._shared_file.read_bytes()
        self.send_response(200)
        self.send_header("Content-Type", content_type(self._shared_file))
        self.send_header("Content-Disposition", f"attachment; filename*=UTF-8''{urllib.parse.quote(filename)}")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)


def local_ip() -> str:
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as sock:
            sock.connect(("8.8.8.8", 80))
            return sock.getsockname()[0]
    except OSError:
        return socket.gethostbyname(socket.gethostname())


def content_type(path: Path) -> str:
    return mimetypes.guess_type(path.name)[0] or "application/octet-stream"
