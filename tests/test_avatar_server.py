from pathlib import Path
from urllib.request import urlopen

from desktop_study_companion.avatar.server import AvatarAssetServer


def test_avatar_server_constructs(tmp_path: Path) -> None:
    renderer = tmp_path / "renderer"
    renderer.mkdir()
    (renderer / "index.html").write_text("<html>avatar</html>", encoding="utf-8")
    model = tmp_path / "model.vrm"
    model.write_bytes(b"vrm")

    server = AvatarAssetServer(renderer, model)
    assert server.renderer_dir == renderer
    assert server.model_path == model


def test_avatar_server_serves_renderer_and_model(tmp_path: Path) -> None:
    renderer = tmp_path / "renderer"
    renderer.mkdir()
    (renderer / "index.html").write_text("<html>avatar</html>", encoding="utf-8")
    model = tmp_path / "model.vrm"
    model.write_bytes(b"vrm-bytes")

    server = AvatarAssetServer(renderer, model)
    base = server.start()
    try:
        with urlopen(base, timeout=2) as response:
            assert b"avatar" in response.read()

        with urlopen(base + "model.vrm", timeout=2) as response:
            assert response.read() == b"vrm-bytes"
    finally:
        server.close()
