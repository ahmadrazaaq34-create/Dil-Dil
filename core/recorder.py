import io
import wave
import threading
import numpy as np
import sounddevice as sd

class AudioRecorder:
    def __init__(self, sample_rate: int = 16000, channels: int = 1, on_amplitude_callback=None):
        self.sample_rate = sample_rate
        self.channels = channels
        self.on_amplitude_callback = on_amplitude_callback
        self.is_recording = False
        self._stream = None
        self._frames = []
        self._lock = threading.Lock()

    def _audio_callback(self, indata, frames, time_info, status):
        """Called by sounddevice for every new audio block."""
        if not self.is_recording:
            return

        with self._lock:
            self._frames.append(indata.copy())

        # Compute volume level (RMS amplitude) for real-time waveform visualization
        if self.on_amplitude_callback:
            try:
                # Calculate normalized float RMS
                float_data = indata.astype(np.float32) / 32768.0
                rms = np.sqrt(np.mean(float_data**2))
                # Scale smoothly for UI bars (responsive non-linear curve)
                scaled = min(1.0, float(rms) * 8.5)
                self.on_amplitude_callback(scaled)
            except Exception:
                pass

    def start(self):
        """Starts recording audio from default microphone."""
        with self._lock:
            self._frames = []
            self.is_recording = True
        if self._stream:
            try:
                self._stream.stop()
                self._stream.close()
            except Exception:
                pass
            self._stream = None

        try:
            self._stream = sd.InputStream(
                samplerate=self.sample_rate,
                channels=self.channels,
                dtype='int16',
                blocksize=1024,
                callback=self._audio_callback
            )
            self._stream.start()
        except Exception as e:
            self.is_recording = False
            raise RuntimeError(f"Microphone input error: {e}")

    def take_frames(self) -> list:
        """
        Live-streaming read: returns every audio chunk collected so far and
        clears the internal buffer. Used by the SegmentCollector to process
        speech in real time while the user is still holding the hotkey.
        """
        with self._lock:
            frames = self._frames
            self._frames = []
        return frames

    def stop(self) -> bytes:
        """Stops recording and returns the audio as WAV bytes if speech is detected."""
        self.is_recording = False
        if self._stream:
            try:
                self._stream.stop()
                self._stream.close()
            except Exception:
                pass
            self._stream = None

        with self._lock:
            if not self._frames:
                return b""
            audio_data = np.concatenate(self._frames, axis=0)

        # Voice Activity Detection (VAD) / Silence Filter:
        # Only discard if completely dead silence (e.g. muted microphone or zero signal)
        max_amplitude = np.max(np.abs(audio_data))
        float_arr = audio_data.astype(np.float32) / 32768.0
        overall_rms = np.sqrt(np.mean(float_arr**2))

        if max_amplitude < 180 and overall_rms < 0.001:
            return b""

        # Normalize DC offset
        audio_data = audio_data - np.mean(audio_data).astype(np.int16)

        # Write to in-memory WAV buffer
        wav_io = io.BytesIO()
        with wave.open(wav_io, 'wb') as wf:
            wf.setnchannels(self.channels)
            wf.setsampwidth(2) # 16-bit PCM
            wf.setframerate(self.sample_rate)
            wf.writeframes(audio_data.tobytes())

        wav_bytes = wav_io.getvalue()
        wav_io.close()
        return wav_bytes
