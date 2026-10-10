import json
import threading

import desktop_study_companion.brain.provider as brain_provider
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

from desktop_study_companion.brain.provider import (
    ChatMessage,
    OllamaNativeProvider,
    OpenAICompatibleProvider,
    is_local_ollama_base_url,
    looks_like_reasoning_leak,
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



def test_local_ollama_detection() -> None:
    assert is_local_ollama_base_url("http://127.0.0.1:11434/v1")
    assert is_local_ollama_base_url("http://localhost:11434")
    assert not is_local_ollama_base_url("http://127.0.0.1:9999/v1")


def test_ollama_native_provider_disables_thinking() -> None:
    captured = {}

    class Handler(BaseHTTPRequestHandler):
        def do_POST(self):  # noqa: N802
            length = int(self.headers["Content-Length"])
            captured["path"] = self.path
            captured["json"] = json.loads(self.rfile.read(length))
            body = json.dumps(
                {
                    "message": {
                        "role": "assistant",
                        "content": "Vamos estudar.",
                        "thinking": "",
                    },
                    "done": True,
                    "done_reason": "stop",
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
        provider = OllamaNativeProvider(
            base_url=f"http://{host}:{port}/v1",
            model="qwen3-test",
            retries=0,
        )
        answer = provider.chat(
            system_prompt="system",
            messages=[ChatMessage("user", "oi")],
        )
    finally:
        server.shutdown()
        server.server_close()

    assert captured["path"] == "/api/chat"
    assert captured["json"]["think"] is False
    assert "/no_think" in captured["json"]["messages"][-1]["content"]
    assert "tools" not in captured["json"]
    assert answer == "Vamos estudar."



def test_reasoning_leak_detector_blocks_meta_reasoning() -> None:
    leaked = (
        "Okay, the user asked for the time. I need to recall the rules. "
        "The rules say I cannot access the computer."
    )
    assert looks_like_reasoning_leak(leaked)
    assert not looks_like_reasoning_leak(
        "Sim, estou te ouvindo. Vamos organizar seu estudo."
    )



def test_ollama_provider_recovers_from_reasoning_like_first_response() -> None:
    captured = []

    class Handler(BaseHTTPRequestHandler):
        def do_POST(self):  # noqa: N802
            length = int(self.headers["Content-Length"])
            payload = json.loads(self.rfile.read(length))
            captured.append(payload)
            if len(captured) == 1:
                content = (
                    "Okay, the user asked a question. I need to respond. "
                    "The rules say I should answer in Portuguese."
                )
            else:
                content = "Sim, estou te ouvindo. Como posso ajudar?"
            body = json.dumps(
                {
                    "message": {
                        "role": "assistant",
                        "content": content,
                        "thinking": "",
                    },
                    "done": True,
                    "done_reason": "stop",
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
        provider = OllamaNativeProvider(
            base_url=f"http://{host}:{port}/v1",
            model="qwen3:4b",
            retries=0,
        )
        answer = provider.chat(
            system_prompt="system",
            messages=[ChatMessage("user", "Você consegue me ouvir?")],
        )
    finally:
        server.shutdown()
        server.server_close()

    assert len(captured) == 2
    assert captured[0]["think"] is False
    assert captured[1]["think"] is False
    assert "/no_think" in captured[0]["messages"][-1]["content"]
    assert "Não descreva análise" in captured[1]["messages"][-1]["content"]
    assert answer == "Sim, estou te ouvindo. Como posso ajudar?"


def test_openai_provider_retries_rate_limit(monkeypatch) -> None:
    calls = {"count": 0}

    class Handler(BaseHTTPRequestHandler):
        def do_POST(self):  # noqa: N802
            calls["count"] += 1
            length = int(self.headers["Content-Length"])
            self.rfile.read(length)
            if calls["count"] == 1:
                self.send_response(429)
                self.send_header("Retry-After", "1")
                self.end_headers()
                return

            body = json.dumps(
                {"choices": [{"message": {"content": "Recuperado."}}]}
            ).encode()
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)

        def log_message(self, *_args):
            return

    monkeypatch.setattr(brain_provider.time, "sleep", lambda _seconds: None)
    server = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()

    try:
        host, port = server.server_address
        provider = OpenAICompatibleProvider(
            base_url=f"http://{host}:{port}/v1",
            model="test-model",
            retries=1,
        )
        answer = provider.chat(
            system_prompt="system",
            messages=[ChatMessage("user", "oi")],
        )
    finally:
        server.shutdown()
        server.server_close()

    assert calls["count"] == 2
    assert answer == "Recuperado."


def test_non_qwen_model_does_not_receive_no_think_command() -> None:
    provider = OllamaNativeProvider(
        base_url="http://127.0.0.1:11434/v1",
        model="llama3.2",
        retries=0,
    )
    outgoing = provider._outgoing_messages(
        "system",
        [ChatMessage("user", "oi")],
    )
    assert all("/no_think" not in item["content"] for item in outgoing)
