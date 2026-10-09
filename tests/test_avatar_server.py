from pathlib import Path

from desktop_study_companion.avatar.server import AvatarAssetServer


def test_avatar_server_constructs(tmp_path: Path) -> None:
    renderer = tmp_path / "renderer"
    renderer.mkdir()
    (renderer / "index.html").write_text("<html></html>", encoding="utf-8")
    model = tmp_path / "model.vrm"
    model.write_bytes(b"vrm")

    server = AvatarAssetServer(renderer, model)
    assert server.renderer_dir == renderer
    assert server.model_path == model
