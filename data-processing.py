import numpy as np
from scipy.signal import resample
import wave
import io

# μ-law decoding lookup table (256 values → 16-bit PCM)
# Based on ITU-T G.711 standard
def ulaw_to_pcm16(ulaw_bytes):
    MULAW_MAX = 0x1FFF
    BIAS = 0x84

    ulaw = np.frombuffer(ulaw_bytes, dtype=np.uint8)
    ulaw = ~ulaw  # Bitwise NOT

    sign = ulaw & 0x80
    exponent = (ulaw >> 4) & 0x07
    mantissa = ulaw & 0x0F

    pcm_val = ((mantissa << 4) + 0x08) << exponent
    pcm_val = pcm_val - BIAS

    pcm_val = np.where(sign != 0, -pcm_val, pcm_val)
    return pcm_val.astype(np.int16)

def mulaw_chunks_to_pcm_wav(chunks, output_path=None):
    # 1. Join 20 ms chunks (μ-law, 8 kHz, 160 bytes per chunk)
    ulaw_data = b''.join(chunks)

    # 2. Decode μ-law to 16-bit PCM (still at 8 kHz)
    pcm_8k = ulaw_to_pcm16(ulaw_data)

    # 3. Resample to 16 kHz
    pcm_16k = resample(pcm_8k, int(len(pcm_8k) * 16000 / 8000)).astype(np.int16)

    if output_path:
        # 4. Save to WAV file
        with wave.open(output_path, "wb") as wav_out:
            wav_out.setnchannels(1)
            wav_out.setsampwidth(2)
            wav_out.setframerate(16000)
            wav_out.writeframes(pcm_16k.tobytes())
    else:
        # Return in-memory WAV bytes
        wav_io = io.BytesIO()
        with wave.open(wav_io, "wb") as wav_out:
            wav_out.setnchannels(1)
            wav_out.setsampwidth(2)
            wav_out.setframerate(16000)
            wav_out.writeframes(pcm_16k.tobytes())
        return wav_io.getvalue()


