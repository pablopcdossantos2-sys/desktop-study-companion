from __future__ import annotations

import json
import struct
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True, slots=True)
class VrmModelInfo:
    name: str
    spec_version: str
    expressions: frozenset[str]
    humanoid_bone_count: int
    spring_count: int


_REQUIRED_EXPRESSIONS = frozenset(
    {
        "neutral",
        "happy",
        "angry",
        "relaxed",
        "surprised",
        "blink",
        "aa",
        "ih",
        "ou",
        "ee",
        "oh",
    }
)


def read_vrm_info(path: str | Path) -> VrmModelInfo:
    path = Path(path)
    with path.open("rb") as handle:
        header = handle.read(12)
        if len(header) != 12:
            raise ValueError("VRM file is too short")

        magic, gltf_version, declared_length = struct.unpack("<4sII", header)
        if magic != b"glTF":
            raise ValueError("not a binary glTF/VRM file")
        if gltf_version != 2:
            raise ValueError(f"unsupported glTF version: {gltf_version}")
        if declared_length != path.stat().st_size:
            raise ValueError("VRM declared length does not match file size")

        chunk_header = handle.read(8)
        if len(chunk_header) != 8:
            raise ValueError("VRM JSON chunk header is missing")
        chunk_length, chunk_type = struct.unpack("<I4s", chunk_header)
        if chunk_type != b"JSON":
            raise ValueError("first GLB chunk is not JSON")

        raw = handle.read(chunk_length)
        document = json.loads(raw.decode("utf-8").rstrip(" \t\r\n\x00"))

    extensions = document.get("extensions", {})
    vrm = extensions.get("VRMC_vrm")
    if not isinstance(vrm, dict):
        raise ValueError("VRMC_vrm extension is missing")

    meta = vrm.get("meta", {})
    expressions = vrm.get("expressions", {}).get("preset", {})
    bones = vrm.get("humanoid", {}).get("humanBones", {})
    springs = extensions.get("VRMC_springBone", {}).get("springs", [])

    return VrmModelInfo(
        name=str(meta.get("name") or ""),
        spec_version=str(vrm.get("specVersion") or ""),
        expressions=frozenset(expressions.keys()),
        humanoid_bone_count=len(bones),
        spring_count=len(springs),
    )


def validate_companion_avatar(path: str | Path) -> VrmModelInfo:
    info = read_vrm_info(path)

    if not info.spec_version.startswith("1."):
        raise ValueError(
            f"Desktop Study Companion requires VRM 1.x; got {info.spec_version!r}"
        )

    missing = sorted(_REQUIRED_EXPRESSIONS - info.expressions)
    if missing:
        raise ValueError(
            "VRM is missing required expressions: " + ", ".join(missing)
        )

    if info.humanoid_bone_count < 20:
        raise ValueError(
            f"VRM humanoid skeleton looks incomplete: {info.humanoid_bone_count} bones"
        )

    return info
