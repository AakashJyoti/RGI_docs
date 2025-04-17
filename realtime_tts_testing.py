import os
import azure.cognitiveservices.speech as speechsdk



def text_to_speech_bytes(input_text: str) -> bytes:
    speech_config = speechsdk.SpeechConfig(subscription=SPEECH_KEY,
                                           region=SPEECH_REGION)
    speech_config.speech_synthesis_voice_name = 'en-IN-AartiNeural'

    # No AudioOutputConfig → audio goes into result.audio_data
    synthesizer = speechsdk.SpeechSynthesizer(
        speech_config=speech_config,
        audio_config=None
    )

    result = synthesizer.speak_text_async(input_text).get()

    if result.reason == speechsdk.ResultReason.SynthesizingAudioCompleted:
        return result.audio_data
    else:
        raise RuntimeError(f"Synthesis failed: {result.cancellation_details.reason}")

# 1) Get the bytes
audio_bytes = text_to_speech_bytes("Namaste! Welcome to our claim helpline. Would you prefer to continue in Hindi or English?")
# print(audio_bytes)
# 2) Write them out to disk
with open("test_output.wav", "wb") as f:
    f.write(audio_bytes)

print(f"Wrote test_output.wav ({len(audio_bytes)} bytes)")


from pydub import AudioSegment
import io

# audio_bytes is your WAV payload (headers+PCM data)
buf = io.BytesIO(audio_bytes)
audio = AudioSegment.from_file(buf, format="wav")

raw_data   = audio.raw_data        # PCM bytes
sample_rate = audio.frame_rate     # e.g. 24000
sample_width = audio.sample_width  # bytes per sample, e.g. 2
n_channels   = audio.channels      # e.g. 1 or 2

chunk_duration = 0.02  # 20 ms
bytes_per_frame = sample_width * n_channels
chunk_size = int(sample_rate * chunk_duration * bytes_per_frame)

offset = 0
seq = 1
timestamp = 0
while offset < len(raw_data):
    chunk = raw_data[offset: offset + chunk_size]
    print(seq, chunk)
    offset += chunk_size
    # … base64‑encode & send exactly as before …
    seq += 1
    timestamp += int(chunk_duration * 1000)
