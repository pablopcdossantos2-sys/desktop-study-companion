from __future__ import annotations

import threading
from pathlib import Path


class SpeechRecognitionError(RuntimeError):
    pass


class FasterWhisperSTT:
    """Lazy local Whisper transcription.

    The model is downloaded only when the first transcription is requested.
    """

    def __init__(
        self,
        *,
        model_name: str = "base",
        language: str = "pt",
        device: str = "cpu",
        compute_type: str = "int8",
        download_root: str | Path | None = None,
    ) -> None:
        self.model_name = model_name.strip()
        self.language = language.strip()
        self.device = device.strip()
        self.compute_type = compute_type.strip()
        self.download_root = (
            Path(download_root) if download_root is not None else None
        )
        self._model = None
        self._lock = threading.Lock()

    def _load_model(self):
        if self._model is not None:
            return self._model

        with self._lock:
            if self._model is not None:
                return self._model

            try:
                from faster_whisper import WhisperModel

                kwargs = {
                    "device": self.device,
                    "compute_type": self.compute_type,
                }
                if self.download_root is not None:
                    self.download_root.mkdir(parents=True, exist_ok=True)
                    kwargs["download_root"] = str(self.download_root)

                self._model = WhisperModel(self.model_name, **kwargs)
            except Exception as exc:
                raise SpeechRecognitionError(
                    f"não foi possível carregar o modelo {self.model_name!r}: {exc}"
                ) from exc

        return self._model

    def transcribe_file(self, path: str | Path) -> str:
        model = self._load_model()
        try:
            segments, _info = model.transcribe(
                str(path),
                language=self.language or None,
                beam_size=3,
                vad_filter=True,
                condition_on_previous_text=False,
            )
            text = " ".join(
                segment.text.strip()
                for segment in segments
                if segment.text.strip()
            ).strip()
        except Exception as exc:
            raise SpeechRecognitionError(
                f"falha na transcrição: {exc}"
            ) from exc

        if not text:
            raise SpeechRecognitionError(
                "nenhuma fala reconhecível foi detectada"
            )
        return text
