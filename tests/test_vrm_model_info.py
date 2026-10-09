import json
import struct

import pytest

from desktop_study_companion.avatar.model_info import (
    read_vrm_info,
    validate_companion_avatar,
)


def _write_vrm(path, *, expressions, spec_version="1.0"):
    document = {
        "asset": {"version": "2.0"},
        "extensions": {
            "VRMC_vrm": {
                "specVersion": spec_version,
                "meta": {"name": "Test Avatar"},
                "humanoid": {
                    "humanBones": {
                        f"bone{i}": {"node": i}
                        for i in range(25)
                    }
                },
                "expressions": {
                    "preset": {name: {} for name in expressions}
                },
            },
            "VRMC_springBone": {
                "springs": [{}, {}],
            },
        },
    }
    raw = json.dumps(document).encode("utf-8")
    padding = (4 - len(raw) % 4) % 4
    raw += b" " * padding
    total = 12 + 8 + len(raw)

    with path.open("wb") as handle:
        handle.write(struct.pack("<4sII", b"glTF", 2, total))
        handle.write(struct.pack("<I4s", len(raw), b"JSON"))
        handle.write(raw)


def test_reads_vrm1_metadata(tmp_path) -> None:
    required = {
        "neutral", "happy", "angry", "relaxed", "surprised",
        "blink", "aa", "ih", "ou", "ee", "oh",
    }
    path = tmp_path / "avatar.vrm"
    _write_vrm(path, expressions=required)

    info = validate_companion_avatar(path)

    assert info.name == "Test Avatar"
    assert info.spec_version == "1.0"
    assert info.humanoid_bone_count == 25
    assert info.spring_count == 2


def test_rejects_missing_required_expression(tmp_path) -> None:
    path = tmp_path / "avatar.vrm"
    _write_vrm(path, expressions={"neutral"})

    with pytest.raises(ValueError, match="missing required expressions"):
        validate_companion_avatar(path)


def test_rejects_non_vrm_binary(tmp_path) -> None:
    path = tmp_path / "not-vrm.vrm"
    path.write_bytes(b"not a vrm")

    with pytest.raises(ValueError):
        read_vrm_info(path)
