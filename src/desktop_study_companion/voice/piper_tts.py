from __future__ import annotations

import logging
import os
import queue
import shutil
import subprocess
import sys
import tempfile
import threading
from dataclasses import dataclass
from pathlib import Path

logger = logging.getLogger("desktop_study_companion.voice.piper")
_MODEL_PREPARE_LOCK = threading.Lock()


@dataclass(frozen=True, slots=True)
class _SpeechItem:
    text: str
    generation: int


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

        self._queue: queue.Queue[_SpeechItem | None] = queue.Queue(maxsize=8)
        self._closed = False
        self._interrupt = threading.Event()
        self._generation_lock = threading.Lock()
        self._generation = 0
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
        with self._generation_lock:
            item = _SpeechItem(text, self._generation)
        try:
            self._queue.put_nowait(item)
        except queue.Full:
            try:
                dropped = self._queue.get_nowait()
                if dropped is not None:
                    self._queue.task_done()
            except queue.Empty:
                pass
            try:
                self._queue.put_nowait(item)
            except queue.Full:
                logger.warning("Dropping Piper utterance because queue is full")

    def _data_dir(self) -> Path:
        # model_dir is data/models/piper.
        return self.model_dir.parent.parent

    def _temp_dir(self) -> Path:
        path = self._data_dir() / "temp"
        path.mkdir(parents=True, exist_ok=True)
        return path

    def _diagnostic_wav_path(self) -> Path:
        return self._temp_dir() / "piper-last.wav"

    def _worker_prefix(self) -> list[str]:
        if bool(getattr(sys, "frozen", False)):
            return [sys.executable, "--piper-worker"]
        return [
            sys.executable,
            "-m",
            "desktop_study_companion.voice.piper_worker",
        ]

    def _prepare_model_command(self) -> list[str]:
        return [
            *self._worker_prefix(),
            "--model-id",
            self.model_id,
            "--model-dir",
            str(self.model_dir),
            "--prepare-only",
        ]

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

        return [*self._worker_prefix(), *args]

    def _portable_runtime_source(self) -> Path | None:
        if not bool(getattr(sys, "frozen", False)):
            return None
        candidate = Path(sys.executable).resolve().parent / "piper-runtime"
        executable = candidate / "piper.exe"
        data_file = candidate / "espeak-ng-data" / "phontab"
        if executable.is_file() and data_file.is_file():
            return candidate
        logger.warning(
            "Bundled Piper runtime is unavailable executable=%s phontab=%s",
            executable,
            data_file,
        )
        return None

    def _ascii_native_root(self) -> Path:
        candidates = [
            Path(tempfile.gettempdir()) / "DesktopStudyCompanionPiper",
        ]
        windir = os.environ.get("WINDIR", "").strip()
        if windir:
            candidates.append(
                Path(windir) / "Temp" / "DesktopStudyCompanionPiper"
            )

        for candidate in candidates:
            if not str(candidate).isascii():
                continue
            try:
                candidate.mkdir(parents=True, exist_ok=True)
                probe = candidate / ".write-test"
                probe.write_text("ok", encoding="ascii")
                probe.unlink(missing_ok=True)
                return candidate
            except OSError:
                logger.debug(
                    "Piper native cache path is not writable path=%s",
                    candidate,
                    exc_info=True,
                )

        fallback = Path(tempfile.mkdtemp(prefix="dsc-piper-"))
        fallback.mkdir(parents=True, exist_ok=True)
        return fallback

    def _prepare_voice_files(self, *, force: bool = False) -> tuple[Path, Path]:
        model_path = self.model_dir / f"{self.model_id}.onnx"
        config_path = self.model_dir / f"{self.model_id}.onnx.json"
        with _MODEL_PREPARE_LOCK:
            healthy = (
                model_path.is_file()
                and model_path.stat().st_size > 1024
                and config_path.is_file()
                and config_path.stat().st_size > 32
            )
            if healthy and not force:
                return model_path, config_path

            if force:
                model_path.unlink(missing_ok=True)
                config_path.unlink(missing_ok=True)

            completed = subprocess.run(
                self._prepare_model_command(),
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
                logger.info(
                    "Piper model preparation: %s",
                    stdout.replace("\n", " | "),
                )
            if completed.returncode != 0:
                raise RuntimeError(
                    "não foi possível preparar o modelo Piper"
                    + (f": {stderr}" if stderr else "")
                )

            if not model_path.is_file() or not config_path.is_file():
                raise RuntimeError("os arquivos da voz Piper não foram encontrados")
            return model_path, config_path

    def _stage_portable_runtime(self, source: Path) -> Path:
        root = self._ascii_native_root()
        target = root / "runtime"
        exe = target / "piper.exe"
        data_file = target / "espeak-ng-data" / "phontab"
        if not exe.is_file() or not data_file.is_file():
            if target.exists():
                shutil.rmtree(target, ignore_errors=True)
            shutil.copytree(source, target)
        return target

    def _stage_voice_for_native_runtime(
        self,
        model_path: Path,
        config_path: Path,
    ) -> tuple[Path, Path]:
        voice_dir = self._ascii_native_root() / "voices"
        voice_dir.mkdir(parents=True, exist_ok=True)
        staged_model = voice_dir / model_path.name
        staged_config = voice_dir / config_path.name
        if (
            not staged_model.is_file()
            or staged_model.stat().st_size != model_path.stat().st_size
        ):
            shutil.copy2(model_path, staged_model)
        if (
            not staged_config.is_file()
            or staged_config.stat().st_size != config_path.stat().st_size
        ):
            shutil.copy2(config_path, staged_config)
        return staged_model, staged_config

    def _synthesize_with_portable_runtime(
        self,
        text: str,
        runtime_source: Path,
        *,
        retry_model: bool = True,
    ) -> bytes:
        model_path, config_path = self._prepare_voice_files()
        runtime = self._stage_portable_runtime(runtime_source)
        staged_model, staged_config = self._stage_voice_for_native_runtime(
            model_path,
            config_path,
        )
        work_dir = self._ascii_native_root() / "output"
        work_dir.mkdir(parents=True, exist_ok=True)
        output = work_dir / f"{self.model_id}-{threading.get_ident()}.wav"
        output.unlink(missing_ok=True)

        command = [
            str(runtime / "piper.exe"),
            "--model",
            str(staged_model),
            "--config",
            str(staged_config),
            "--output_file",
            str(output),
            "--espeak_data",
            str(runtime / "espeak-ng-data"),
            "--length_scale",
            str(self.length_scale),
            "--noise_scale",
            str(self.noise_scale),
            "--noise_w",
            str(self.noise_w_scale),
        ]
        logger.info(
            "Starting bundled standalone Piper model=%s runtime=%s",
            self.model_id,
            runtime,
        )
        completed = subprocess.run(
            command,
            input=text + "\n",
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            cwd=runtime,
            timeout=self.SYNTHESIS_TIMEOUT_SECONDS,
            creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0),
            check=False,
        )
        stderr = (completed.stderr or "").strip()
        if completed.returncode != 0 or not output.is_file():
            logger.error(
                "Standalone Piper failed model=%s returncode=%s stderr=%s",
                self.model_id,
                completed.returncode,
                stderr or "<empty>",
            )
            if retry_model:
                logger.warning(
                    "Refreshing Piper voice files once after native runtime failure"
                )
                self._prepare_voice_files(force=True)
                staged_model.unlink(missing_ok=True)
                staged_config.unlink(missing_ok=True)
                return self._synthesize_with_portable_runtime(
                    text,
                    runtime_source,
                    retry_model=False,
                )
            raise RuntimeError(
                "o runtime Piper para Windows falhou"
                + (f": {stderr}" if stderr else "")
            )

        audio = output.read_bytes()
        output.unlink(missing_ok=True)
        if len(audio) <= 44:
            raise RuntimeError("o runtime Piper gerou um WAV vazio")
        self._diagnostic_wav_path().write_bytes(audio)
        logger.info(
            "Standalone Piper synthesis completed model=%s wav_bytes=%s",
            self.model_id,
            len(audio),
        )
        return audio

    def _synthesize_wav_bytes(self, text: str) -> bytes:
        runtime_source = self._portable_runtime_source()
        if runtime_source is not None:
            return self._synthesize_with_portable_runtime(
                text,
                runtime_source,
            )
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
                with self._generation_lock:
                    if item.generation != self._generation:
                        continue
                    self._interrupt.clear()
                    self._speaking.set()
                try:
                    self._speak_item(item.text)
                except Exception:
                    logger.exception(
                        "Piper synthesis/playback failed model=%s; using fallback=%s",
                        self.model_id,
                        self.fallback is not None,
                    )
                    with self._generation_lock:
                        current = item.generation == self._generation
                    if (
                        self.fallback is not None
                        and current
                        and not self._interrupt.is_set()
                    ):
                        self.fallback.speak(item.text)
            finally:
                self._speaking.clear()
                with self._generation_lock:
                    if item.generation == self._generation:
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
        with self._generation_lock:
            self._generation += 1
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
        try:
            self._queue.put_nowait(None)
        except queue.Full:
            pass
        self._thread.join(timeout=2.0)
        if self.fallback is not None:
            self.fallback.close()
