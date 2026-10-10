import json
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

from desktop_study_companion.brain.provider import (
    ChatMessage,
    OpenAICompatibleProvider,
    sanitize_assistant_text,
)


def test_sanitizer_removes_internal_reasoning_and_control_marker() -> None:
    marker = "[" + "TOOL" + ":noop]"
    raw = f"<think>segredo</think>Olá {marker} mundo."
    assert sanitize_assistant_text(raw) == "Olá mundo."


def test_openai_compatible_provider_posts_chat_without_tools() -> None:
    captured = {}

    class Handler(BaseHTTPRequestHandler):
        def do_POST(self):  # noqa: N802
            length = int(self.headers["Content-Length"])
            captured["path"] = self.path
            captured["json"] = json.loads(self.rfile.read(length))
            marker = "[" + "ACTION" + ":noop]"
            body = json.dumps(
                {
                    "choices": [
                        {"message": {"content": f"Olá! {marker}"}}
                    ]
                }
            ).encode()
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)

        def log_message(self, *_args):
            return

    server = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()

    try:
        host, port = server.server_address
        provider = OpenAICompatibleProvider(
            base_url=f"http://{host}:{port}/v1",
            model="test-model",
            retries=0,
        )
        answer = provider.chat(
            system_prompt="system",
            messages=[ChatMessage("user", "oi")],
        )
    finally:
        server.shutdown()
        server.server_close()

    assert captured["path"] == "/v1/chat/completions"
    assert "tools" not in captured["json"]
    assert captured["json"]["stream"] is False
    assert answer == "Olá!"
