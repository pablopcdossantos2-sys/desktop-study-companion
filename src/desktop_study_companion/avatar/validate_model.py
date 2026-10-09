from __future__ import annotations

import argparse

from .model_info import validate_companion_avatar


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("path")
    args = parser.parse_args()

    info = validate_companion_avatar(args.path)
    print(
        f"VRM OK: name={info.name!r}, spec={info.spec_version}, "
        f"bones={info.humanoid_bone_count}, springs={info.spring_count}, "
        f"expressions={len(info.expressions)}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
