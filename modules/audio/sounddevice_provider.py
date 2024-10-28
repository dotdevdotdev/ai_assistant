import sounddevice as sd
import numpy as np
import wave
import io
from typing import Dict, List, Optional, Union
from core.interfaces.audio import AudioInputProvider, AudioConfig


class SoundDeviceProvider(AudioInputProvider):
    def __init__(self, config: dict):
        self._config = config
        self._stream = None
        self._recording = False
        self._processing = False
        self._recorded_frames = []
        self._input_device_id = None
        self._output_device_id = None
        self._playback_stream = None

    def start_stream(self, config: AudioConfig) -> None:
        if self._stream is not None:
            self.stop_stream()

        self._config = config
        self._stream = sd.InputStream(
            samplerate=config.sample_rate,
            channels=config.channels,
            device=config.device_id,
            blocksize=config.chunk_size,
        )
        self._stream.start()

    def read_chunk(self) -> bytes:
        if not self._stream:
            raise RuntimeError("Audio stream not started")

        data, overflowed = self._stream.read(self._config.chunk_size)
        if overflowed:
            print("Audio buffer overflow detected")
        return data.tobytes()

    def stop_stream(self) -> None:
        if self._stream:
            self._stream.stop()
            self._stream.close()
            self._stream = None

    def get_devices(self) -> list[dict]:
        devices = []
        device_list = sd.query_devices()
        for i, device in enumerate(device_list):
            if device["max_input_channels"] > 0:  # Only input devices
                devices.append(
                    {
                        "id": i,
                        "name": device["name"],
                        "channels": device["max_input_channels"],
                        "sample_rate": device["default_samplerate"],
                    }
                )
        return devices

    def play_audio(self, audio_data: Union[bytes, io.BytesIO]) -> None:
        if self._playback_stream is not None:
            self.stop_playback()

        with wave.Wave_read(audio_data) as wf:
            data = np.frombuffer(wf.readframes(wf.getnframes()), dtype=np.int16)
            self._playback_stream = sd.play(
                data, wf.getframerate(), channels=wf.getnchannels()
            )
            sd.wait()  # Wait until file is done playing

    def stop_playback(self) -> None:
        if self._playback_stream:
            sd.stop()
            self._playback_stream = None

    def __del__(self):
        self.stop_stream()
        self.stop_playback()
