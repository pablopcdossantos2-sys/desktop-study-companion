from __future__ import annotations

import io
import logging
import queue
import threading
import wave
from dataclasses import dataclass
from pathlib import Path

logger = logging.getLogger("desktop_study_companion.voice.piper")


@dataclass(frozen=True, slots=True)
class _SpeechItem:
    text: str


class PiperNeuralTTS:
    """Non-blocking local neural TTS using Piper with Windows WAV playback.

    Piper performs synthesis locally. Playback uses the native Windows
    winsound API instead of PortAudio/sounddevice because real-world testing
    showed that a valid Piper model could synthesize without producing audible
    output through the previous RawOutputStream path.
    """

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
        self._voice = None
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

    def _ensure_voice(self):
        if self._voice is not None:
            return self._voice

        from piper import PiperVoice
        from piper.download_voices import download_voice

        self.model_dir.mkdir(parents=True, exist_ok=True)
        model_path = self.model_dir / f"{self.model_id}.onnx"
        config_path = self.model_dir / f"{self.model_id}.onnx.json"

        if not model_path.exists() or not config_path.exists():
            logger.info(
                "Downloading Piper voice model=%s directory=%s",
                self.model_id,
                self.model_dir,
            )
            download_voice(self.model_id, self.model_dir)
            logger.info("Piper voice download completed model=%s", self.model_id)

        logger.info("Loading Piper voice model=%s", model_path)
        self._voice = PiperVoice.load(model_path)
        logger.info("Piper voice loaded model=%s", self.model_id)
        return self._voice

    def _synthesize_wav_bytes(self, text: str) -> bytes:
        from piper import SynthesisConfig

        voice = self._ensure_voice()
        syn_config = SynthesisConfig(
            volume=self.volume / 100.0,
            length_scale=self.length_scale,
            noise_scale=self.noise_scale,
            noise_w_scale=self.noise_w_scale,
        )

        wav_buffer = io.BytesIO()
        with wave.open(wav_buffer, "wb") as wav_file:
            voice.synthesize_wav(
                text,
                wav_file,
                syn_config=syn_config,
            )

        audio = wav_buffer.getvalue()
        if len(audio) <= 44:
            raise RuntimeError("Piper generated an empty WAV stream")

        logger.info(
            "Piper synthesis completed model=%s wav_bytes=%s",
            self.model_id,
            len(audio),
        )
        return audio

    def _play_wav_bytes(self, audio: bytes) -> None:
        import winsound

        if self._interrupt.is_set():
            return

        logger.info(
            "Starting native Windows Piper playback model=%s wav_bytes=%s",
            self.model_id,
            len(audio),
        )
        # PlaySound blocks here, but this class already owns a dedicated worker
        # thread. SND_MEMORY lets Windows handle the WAV using the user's normal
        # system output device without a separate PortAudio output stream.
        winsound.PlaySound(audio, winsound.SND_MEMORY)
        logger.info("Native Windows Piper playback completed model=%s", self.model_id)

    def _stop_native_playback(self) -> None:
        try:
            import winsound

            # Passing None stops the currently playing waveform sound.
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
