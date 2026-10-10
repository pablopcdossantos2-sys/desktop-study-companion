from __future__ import annotations

import argparse
import sys
import wave
from pathlib import Path


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(add_help=False)
    parser.add_argument("--model-id", required=True)
    parser.add_argument("--model-dir", required=True)
    parser.add_argument("--text-file", required=True)
    parser.add_argument("--output", required=True)
    parser.add_argument("--volume", type=int, default=90)
    parser.add_argument("--length-scale", type=float, default=1.0)
    parser.add_argument("--noise-scale", type=float, default=0.667)
    parser.add_argument("--noise-w-scale", type=float, default=0.8)
    return parser


def synthesize(args: argparse.Namespace) -> Path:
    from piper import PiperVoice, SynthesisConfig
    from piper.download_voices import download_voice

    model_dir = Path(args.model_dir)
    model_dir.mkdir(parents=True, exist_ok=True)
    model_path = model_dir / f"{args.model_id}.onnx"
    config_path = model_dir / f"{args.model_id}.onnx.json"

    if not model_path.exists() or not config_path.exists():
        print(f"stage=download model={args.model_id}", flush=True)
        download_voice(args.model_id, model_dir)

    print(f"stage=load model={args.model_id}", flush=True)
    voice = PiperVoice.load(model_path)

    text = Path(args.text_file).read_text(encoding="utf-8").strip()
    if not text:
        raise RuntimeError("Piper worker received empty text")

    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    syn_config = SynthesisConfig(
        volume=max(0, min(100, int(args.volume))) / 100.0,
        length_scale=float(args.length_scale),
        noise_scale=float(args.noise_scale),
        noise_w_scale=float(args.noise_w_scale),
    )

    print(f"stage=synthesize chars={len(text)}", flush=True)
    with wave.open(str(output), "wb") as wav_file:
        voice.synthesize_wav(
            text,
            wav_file,
            syn_config=syn_config,
        )

    if not output.exists() or output.stat().st_size <= 44:
        raise RuntimeError("Piper worker generated an empty WAV stream")

    print(f"stage=done bytes={output.stat().st_size}", flush=True)
    return output


def main(argv: list[str] | None = None) -> int:
    try:
        args = _parser().parse_args(argv)
        synthesize(args)
        return 0
    except Exception as exc:
        print(
            f"piper-worker-error: {type(exc).__name__}: {exc}",
            file=sys.stderr,
            flush=True,
        )
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
