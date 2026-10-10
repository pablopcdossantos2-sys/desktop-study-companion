from __future__ import annotations

import tempfile
import threading
import time
import wave
from dataclasses import dataclass
from pathlib import Path


class AudioCaptureError(RuntimeError):
    pass


@dataclass(frozen=True, slots=True)
class InputDevice:
    index: int
    name: str
    channels: int
    default_samplerate: float


def list_input_devices() -> list[InputDevice]:
    import sounddevice as sd

    devices: list[InputDevice] = []
    for index, raw in enumerate(sd.query_devices()):
        channels = int(raw.get("max_input_channels", 0))
        if channels <= 0:
            continue
        devices.append(
            InputDevice(
                index=index,
                name=str(raw.get("name", f"Device {index}")),
                channels=channels,
                default_samplerate=float(
                    raw.get("default_samplerate", 16000.0)
                ),
            )
        )
    return devices


class MicrophoneRecorder:
    def __init__(
        self,
        *,
        output_dir: str | Path,
        device_index: int = -1,
        samplerate: int = 16000,
    ) -> None:
        self.output_dir = Path(output_dir)
        self.device_index = int(device_index)
        self.samplerate = int(samplerate)
        self._lock = threading.Lock()
        self._frames = []
        self._stream = None
        self._started_at = 0.0

    @property
    def recording(self) -> bool:
        return self._stream is not None

    def update_device(self, device_index: int) -> None:
        if self.recording:
            raise AudioCaptureError(
                "cannot change microphone while recording"
            )
        self.device_index = int(device_index)

    def start(self) -> None:
        if self.recording:
            raise AudioCaptureError("microphone is already recording")

        import sounddevice as sd

        with self._lock:
            self._frames = []

        def callback(indata, _frames, _time_info, status):
            if status:
                # Status flags are non-fatal for a short dictation sample.
                pass
            with self._lock:
                self._frames.append(indata.copy())

        kwargs = {
            "samplerate": self.samplerate,
            "channels": 1,
            "dtype": "float32",
            "callback": callback,
        }
        if self.device_index >= 0:
            kwargs["device"] = self.device_index

        try:
            stream = sd.InputStream(**kwargs)
            stream.start()
        except Exception as exc:
            raise AudioCaptureError(
                f"não foi possível abrir o microfone: {exc}"
            ) from exc

        self._stream = stream
        self._started_at = time.monotonic()

    def stop_to_wav(self) -> Path:
        stream = self._stream
        if stream is None:
            raise AudioCaptureError("microphone is not recording")

        self._stream = None
        try:
            stream.stop()
            stream.close()
        finally:
            duration = time.monotonic() - self._started_at

        if duration < 0.25:
            with self._lock:
                self._frames = []
            raise AudioCaptureError("gravação curta demais")

        import numpy as np

        with self._lock:
            frames = self._frames
            self._frames = []

        if not frames:
            raise AudioCaptureError("nenhum áudio foi capturado")

        audio = np.concatenate(frames, axis=0).reshape(-1)
        audio = np.clip(audio, -1.0, 1.0)
        pcm = (audio * 32767.0).astype(np.int16)

        self.output_dir.mkdir(parents=True, exist_ok=True)
        handle = tempfile.NamedTemporaryFile(
            prefix="ptt-",
            suffix=".wav",
            dir=self.output_dir,
            delete=False,
        )
        path = Path(handle.name)
        handle.close()

        try:
            with wave.open(str(path), "wb") as wav:
                wav.setnchannels(1)
                wav.setsampwidth(2)
                wav.setframerate(self.samplerate)
                wav.writeframes(pcm.tobytes())
        except Exception:
            path.unlink(missing_ok=True)
            raise

        return path

    def cancel(self) -> None:
        stream = self._stream
        self._stream = None
        if stream is not None:
            try:
                stream.stop()
            finally:
                stream.close()
        with self._lock:
            self._frames = []
