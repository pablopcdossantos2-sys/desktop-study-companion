from __future__ import annotations

import logging
import queue
import subprocess
import sys
import tempfile
import threading
from dataclasses import dataclass
from pathlib import Path

logger = logging.getLogger("desktop_study_companion.voice.piper")


@dataclass(frozen=True, slots=True)
class _SpeechItem:
    text: str


class PiperNeuralTTS:
    """Non-blocking local neural TTS with crash-isolated Piper synthesis.

    Piper/ONNX synthesis runs in a helper process. A native crash in that
    process therefore cannot terminate the Qt companion itself. Playback uses
    the native Windows winsound API with a real WAV file.
    """

    SYNTHESIS_TIMEOUT_SECONDS = 90

    def __init__(
        self,
        *,
        model_id: str,
        model_dir: str | Path,
        volume: int = 90,
        length_scale: float = 1.0,
        noise_scale: float = 0.667,
        noise_w_scale: float = 0.8,
        fallback=None,
    ) -> None:
        self.model_id = model_id.strip()
        self.model_dir = Path(model_dir)
        self.volume = max(0, min(100, int(volume)))
        self.length_scale = float(length_scale)
        self.noise_scale = float(noise_scale)
        self.noise_w_scale = float(noise_w_scale)
        self.fallback = fallback

        self._queue: queue.Queue[_SpeechItem | None] = queue.Queue()
        self._closed = False
        self._interrupt = threading.Event()
        self._speaking = threading.Event()
        self._thread = threading.Thread(
            target=self._worker,
            name="desktop-study-companion-piper-tts",
            daemon=True,
        )
        self._thread.start()

    def speak(self, text: str) -> None:
        text = text.strip()
        if not text or self._closed:
            return
        logger.info(
            "Queued Piper utterance model=%s chars=%s",
            self.model_id,
            len(text),
        )
        self._queue.put(_SpeechItem(text))

    def _data_dir(self) -> Path:
        # model_dir is data/models/piper.
        return self.model_dir.parent.parent

    def _temp_dir(self) -> Path:
        path = self._data_dir() / "temp"
        path.mkdir(parents=True, exist_ok=True)
        return path

    def _diagnostic_wav_path(self) -> Path:
        return self._temp_dir() / "piper-last.wav"

    def _worker_command(
        self,
        *,
        text_file: Path,
        output: Path,
    ) -> list[str]:
        args = [
            "--model-id",
            self.model_id,
            "--model-dir",
            str(self.model_dir),
            "--text-file",
            str(text_file),
            "--output",
            str(output),
            "--volume",
            str(self.volume),
            "--length-scale",
            str(self.length_scale),
            "--noise-scale",
            str(self.noise_scale),
            "--noise-w-scale",
            str(self.noise_w_scale),
        ]

        if bool(getattr(sys, "frozen", False)):
            return [sys.executable, "--piper-worker", *args]

        return [
            sys.executable,
            "-m",
            "desktop_study_companion.voice.piper_worker",
            *args,
        ]

    def _synthesize_wav_bytes(self, text: str) -> bytes:
        temp_dir = self._temp_dir()
        text_handle = tempfile.NamedTemporaryFile(
            mode="w",
            encoding="utf-8",
            suffix=".txt",
            prefix="piper-",
            dir=temp_dir,
            delete=False,
        )
        text_path = Path(text_handle.name)
        try:
            text_handle.write(text)
            text_handle.close()

            output_handle = tempfile.NamedTemporaryFile(
                suffix=".wav",
                prefix="piper-",
                dir=temp_dir,
                delete=False,
            )
            output_path = Path(output_handle.name)
            output_handle.close()
            output_path.unlink(missing_ok=True)

            command = self._worker_command(
                text_file=text_path,
                output=output_path,
            )
            logger.info(
                "Starting isolated Piper synthesis model=%s",
                self.model_id,
            )
            completed = subprocess.run(
                command,
                capture_output=True,
                text=True,
                encoding="utf-8",
                errors="replace",
                timeout=self.SYNTHESIS_TIMEOUT_SECONDS,
                creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0),
                check=False,
            )

            stdout = (completed.stdout or "").strip()
            stderr = (completed.stderr or "").strip()
            if stdout:
                logger.info("Piper worker: %s", stdout.replace("\n", " | "))

            if completed.returncode != 0:
                logger.error(
                    "Piper worker exited abnormally model=%s returncode=%s stderr=%s",
                    self.model_id,
                    completed.returncode,
                    stderr or "<empty>",
                )
                raise RuntimeError(
                    "o processo isolado do Piper falhou "
                    f"(código {completed.returncode})"
                )

            if stderr:
                logger.warning(
                    "Piper worker stderr model=%s: %s",
                    self.model_id,
                    stderr,
                )

            audio = output_path.read_bytes()
            if len(audio) <= 44:
                raise RuntimeError("Piper worker generated an empty WAV stream")

            self._diagnostic_wav_path().write_bytes(audio)
            logger.info(
                "Piper synthesis completed model=%s wav_bytes=%s isolated=true",
                self.model_id,
                len(audio),
            )
            return audio
        except subprocess.TimeoutExpired as exc:
            logger.error(
                "Piper worker timed out model=%s timeout=%ss",
                self.model_id,
                self.SYNTHESIS_TIMEOUT_SECONDS,
            )
            raise RuntimeError("o processo isolado do Piper excedeu o tempo limite") from exc
        finally:
            try:
                text_handle.close()
            except Exception:
                pass
            text_path.unlink(missing_ok=True)
            if "output_path" in locals():
                output_path.unlink(missing_ok=True)

    def _play_wav_bytes(self, audio: bytes) -> None:
        import winsound

        if self._interrupt.is_set():
            return

        wav_path = self._diagnostic_wav_path()
        wav_path.write_bytes(audio)
        logger.info(
            "Starting native Windows Piper playback model=%s wav_bytes=%s path=%s",
            self.model_id,
            len(audio),
            wav_path,
        )
        winsound.PlaySound(
            str(wav_path),
            winsound.SND_FILENAME | getattr(winsound, "SND_SYNC", 0),
        )
        logger.info(
            "Native Windows Piper playback completed model=%s path=%s",
            self.model_id,
            wav_path,
        )

    def _stop_native_playback(self) -> None:
        try:
            import winsound

            winsound.PlaySound(None, 0)
        except Exception:
            logger.debug("Unable to stop winsound playback", exc_info=True)

    def _speak_item(self, text: str) -> None:
        audio = self._synthesize_wav_bytes(text)
        if self._interrupt.is_set():
            return
        self._play_wav_bytes(audio)

    def _worker(self) -> None:
        while True:
            item = self._queue.get()
            if item is None:
                return
            try:
                self._speaking.set()
                self._interrupt.clear()
                try:
                    self._speak_item(item.text)
                except Exception:
                    logger.exception(
                        "Piper synthesis/playback failed model=%s; using fallback=%s",
                        self.model_id,
                        self.fallback is not None,
                    )
                    if self.fallback is not None and not self._interrupt.is_set():
                        self.fallback.speak(item.text)
            finally:
                self._speaking.clear()
                self._interrupt.clear()
                self._queue.task_done()

    @property
    def is_speaking(self) -> bool:
        fallback_speaking = bool(
            self.fallback is not None
            and getattr(self.fallback, "is_speaking", False)
        )
        return self._speaking.is_set() or fallback_speaking

    def stop(self) -> None:
        if self._closed:
            return
        self._interrupt.set()
        self._stop_native_playback()
        if self.fallback is not None:
            self.fallback.stop()
        while True:
            try:
                item = self._queue.get_nowait()
            except queue.Empty:
                break
            if item is not None:
                self._queue.task_done()

    def close(self) -> None:
        if self._closed:
            return
        self.stop()
        self._closed = True
        self._queue.put(None)
        if self.fallback is not None:
            self.fallback.close()
