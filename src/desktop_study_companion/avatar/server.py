from __future__ import annotations

import logging
import mimetypes
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

logger = logging.getLogger("desktop_study_companion.avatar.server")


class AvatarAssetServer:
    def __init__(self, renderer_dir: Path, model_path: Path) -> None:
        self.renderer_dir = renderer_dir
        self.model_path = model_path
        self.httpd: ThreadingHTTPServer | None = None
        self.thread: threading.Thread | None = None

    def start(self) -> str:
        renderer_dir = self.renderer_dir
        model_path = self.model_path

        class Handler(BaseHTTPRequestHandler):
            def do_GET(self):  # noqa: N802
                if self.path == "/favicon.ico":
                    self.send_response(204)
                    self.end_headers()
                    return
                if self.path == "/model.vrm":
                    target = model_path
                else:
                    rel = self.path.split("?", 1)[0].lstrip("/") or "index.html"
                    target = (renderer_dir / rel).resolve()
                    if not str(target).startswith(str(renderer_dir.resolve())):
                        self.send_error(403)
                        return
                if not target.exists() or not target.is_file():
                    logger.error(
                        "Avatar asset not found request=%s target=%s",
                        self.path,
                        target,
                    )
                    self.send_error(404)
                    return
                data = target.read_bytes()
                ctype = mimetypes.guess_type(target.name)[0] or "application/octet-stream"
                self.send_response(200)
                self.send_header("Content-Type", ctype)
                self.send_header("Content-Length", str(len(data)))
                self.send_header("Cache-Control", "no-store")
                self.end_headers()
                self.wfile.write(data)

            def log_message(self, *_args):
                return

        self.httpd = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
        self.thread = threading.Thread(target=self.httpd.serve_forever, daemon=True)
        self.thread.start()
        host, port = self.httpd.server_address
        url = f"http://{host}:{port}/"
        logger.info("Avatar asset server started at %s", url)
        return url

    def close(self) -> None:
        if self.httpd is not None:
            self.httpd.shutdown()
            self.httpd.server_close()
            self.httpd = None
            logger.info("Avatar asset server stopped")
