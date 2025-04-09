import azure.cognitiveservices.speech as speechsdk
import base64
import wave
import time


SPEECH_KEY="ea81bafd0787487c808e90e4dd006252"
SPEECH_REGION="centralindia"



# # Initialize speech configuration with your subscription details
# speech_config = speechsdk.SpeechConfig(subscription=SPEECH_KEY, region=SPEECH_REGION)
#
# # Configure silence timeouts
# speech_config.set_property(speechsdk.PropertyId.SpeechServiceConnection_InitialSilenceTimeoutMs, "5000")  # 5 seconds
# speech_config.set_property(speechsdk.PropertyId.SpeechServiceConnection_EndSilenceTimeoutMs, "2000")      # 2 seconds
#
# # Define the audio format
# audio_format = speechsdk.audio.AudioStreamFormat(samples_per_second=16000, bits_per_sample=16, channels=1)
#
# # Create a push audio input stream
# push_stream = speechsdk.audio.PushAudioInputStream(audio_format)
#
# # Create an audio configuration using the push stream
# audio_config = speechsdk.audio.AudioConfig(stream=push_stream)
#
# # Initialize the speech recognizer
# recognizer = speechsdk.SpeechRecognizer(speech_config=speech_config, audio_config=audio_config, language="en-IN")
#
# # Event handler for recognized speech
# def on_recognized(evt):
#     if evt.result.reason == speechsdk.ResultReason.RecognizedSpeech:
#         print(f"Recognized: {evt.result.text}")
#     elif evt.result.reason == speechsdk.ResultReason.NoMatch:
#         print("No speech could be recognized")
#
# # Event handler for session started
# def on_session_started(evt):
#     print("Session started.")
#
# # Event handler for session stopped
# def on_session_stopped(evt):
#     print("Session stopped.")
#     # Stop continuous recognition upon session end
#     recognizer.stop_continuous_recognition()
#
# # Event handler for canceled recognition
# def on_canceled(evt):
#     print(f"Recognition canceled: {evt.result.cancellation_details.reason}")
#
# # Connect event handlers
# recognizer.recognized.connect(on_recognized)
# recognizer.session_started.connect(on_session_started)
# recognizer.session_stopped.connect(on_session_stopped)
# recognizer.canceled.connect(on_canceled)
#
# # Start continuous recognition
# recognizer.start_continuous_recognition()
#
#
#
# filename = "D:\\reliance\\motor_websocket\\audio\Bot\\bot_response.wav"
# sample_rate = 16000
# sampwidth = 2
# n_channels = 1
# with wave.open(filename, "rb") as wf:
#     raw_data = wf.readframes(wf.getnframes())
#
# chunk_duration = 0.02  # 20 ms
# bytes_per_frame = sampwidth * n_channels
# chunk_size = int(sample_rate * chunk_duration * bytes_per_frame)
# chunk_number = 1
# timestamp = 0
# while True:
#     chunk = raw_data[(chunk_number - 1) * chunk_size: chunk_number * chunk_size]
#     push_stream.write(chunk)
#     time.sleep(0.1)  # Simulate real-time audio input
#
# recognizer.stop_continuous_recognition()




# # Simulate pushing audio data into the stream
# # In a real application, replace this with actual audio data being received
# import time
# for _ in range(10):
#     # Replace 'audio_chunk' with actual audio data in bytes
#     audio_chunk = b'\x00' * 3200  # Example: 100ms of silence at 16kHz, 16-bit mono PCM
#     push_stream.write(audio_chunk)
#     time.sleep(0.1)  # Simulate real-time audio input
#
# # Stop recognition when done
# recognizer.stop_continuous_recognition()










import azure.cognitiveservices.speech as speechsdk
import wave
import time

# Initialize speech configuration with your subscription details
speech_config = speechsdk.SpeechConfig(subscription=SPEECH_KEY, region=SPEECH_REGION)

# Configure silence timeouts
speech_config.set_property(speechsdk.PropertyId.SpeechServiceConnection_InitialSilenceTimeoutMs, "2000")  # 5 seconds
speech_config.set_property(speechsdk.PropertyId.SpeechServiceConnection_EndSilenceTimeoutMs, "1000")      # 2 seconds

# Define the audio format
audio_format = speechsdk.audio.AudioStreamFormat(samples_per_second=16000, bits_per_sample=16, channels=1)

# Create a push audio input stream
push_stream = speechsdk.audio.PushAudioInputStream(audio_format)

# Create an audio configuration using the push stream
audio_config = speechsdk.audio.AudioConfig(stream=push_stream)

# Initialize the speech recognizer
recognizer = speechsdk.SpeechRecognizer(speech_config=speech_config, audio_config=audio_config, language="en-AU")

# Event handler for recognized speech
# def on_recognized(evt):
#     if evt.result.reason == speechsdk.ResultReason.RecognizedSpeech:
#         print(f"Recognized: {evt.result.text}")
#     elif evt.result.reason == speechsdk.ResultReason.NoMatch:
#         print("No speech could be recognized")
def on_recognized(evt):
    if evt.result.reason == speechsdk.ResultReason.RecognizedSpeech:
        if evt.result.text.strip() == "":
            print("Silence detected.")
        else:
            print(f"Recognized: {evt.result.text}")
    elif evt.result.reason == speechsdk.ResultReason.NoMatch:
        print("No speech could be recognized.")


# Event handler for session started
def on_session_started(evt):
    print("Session started.")

# Event handler for session stopped
def on_session_stopped(evt):
    print("Session stopped.")

# Event handler for canceled recognition
def on_canceled(evt):
    print(f"Recognition canceled: {evt.result.cancellation_details.reason}")

# Connect event handlers
recognizer.recognized.connect(on_recognized)
recognizer.session_started.connect(on_session_started)
recognizer.session_stopped.connect(on_session_stopped)
recognizer.canceled.connect(on_canceled)

# Start continuous recognition
recognizer.start_continuous_recognition()

# Audio file path
filename = r"D:\reliance\motor_websocket\audio\Bot\bot_response.wav"

# Open the audio file
with wave.open(filename, "rb") as wf:
    raw_data = wf.readframes(wf.getnframes())

# Define chunk parameters
chunk_duration = 0.02  # 20 ms
sample_rate = 16000
sampwidth = 2
n_channels = 1
bytes_per_frame = sampwidth * n_channels
chunk_size = int(sample_rate * chunk_duration * bytes_per_frame)
total_chunks = len(raw_data) // chunk_size

# Stream audio data in chunks
for chunk_number in range(total_chunks):
    start = chunk_number * chunk_size
    end = start + chunk_size
    chunk = raw_data[start:end]
    push_stream.write(chunk)
    time.sleep(chunk_duration)  # Simulate real-time audio input

# Stop recognition after all data is processed
recognizer.stop_continuous_recognition()

# Close the push stream
push_stream.close()















# import azure.cognitiveservices.speech as speechsdk
# import sounddevice as sd
# import numpy as np
#
# # Replace these with your actual Azure Speech subscription key and region.
# SPEECH_KEY = SPEECH_KEY
# SPEECH_REGION = SPEECH_REGION
#
# # Configure the Azure Speech Service
# speech_config = speechsdk.SpeechConfig(subscription=SPEECH_KEY, region=SPEECH_REGION)
# speech_config.set_property(
#     speechsdk.PropertyId.SpeechServiceConnection_InitialSilenceTimeoutMs, "5000"
# )  # 5 seconds
# speech_config.set_property(
#     speechsdk.PropertyId.SpeechServiceConnection_EndSilenceTimeoutMs, "2000"
# )  # 2 seconds
#
# # Define the audio format for the PushAudioInputStream: 16 kHz, 16-bit, mono.
# audio_format = speechsdk.audio.AudioStreamFormat(
#     samples_per_second=16000, bits_per_sample=16, channels=1
# )
#
# # Create a push stream to feed audio data into the recognizer.
# push_stream = speechsdk.audio.PushAudioInputStream(audio_format)
# audio_config = speechsdk.audio.AudioConfig(stream=push_stream)
#
# # Create the Speech Recognizer.
# speech_recognizer = speechsdk.SpeechRecognizer(
#     speech_config=speech_config, audio_config=audio_config, language="en-IN"
# )
#
# # Event handler for recognized speech.
# def on_recognized(evt):
#     if evt.result.reason == speechsdk.ResultReason.RecognizedSpeech:
#         print("Recognized:", evt.result.text)
#     elif evt.result.reason == speechsdk.ResultReason.NoMatch:
#         print("NoMatch: Speech could not be recognized.")
#
# # Event handler for canceled recognition.
# def on_canceled(evt):
#     print("Recognition canceled:", evt.result.cancellation_details.reason)
#     if evt.result.cancellation_details.reason == speechsdk.CancellationReason.Error:
#         print("Error details:", evt.result.cancellation_details.error_details)
#
# # Connect event handlers.
# speech_recognizer.recognized.connect(on_recognized)
# speech_recognizer.canceled.connect(on_canceled)
#
# # Microphone callback function: this function is called by sounddevice for each audio block.
# def audio_callback(indata, frames, time_info, status):
#     if status:
#         print("Stream status:", status)
#     # Convert the numpy array to bytes (16-bit PCM) and push into the stream.
#     push_stream.write(indata.tobytes())
#
# # Microphone parameters.
# sample_rate = 16000  # Hz
# channels = 1         # Mono audio
#
# print("Starting microphone stream and speech recognition. Press Ctrl+C to stop.")
#
# # Start the Azure recognizer.
# speech_recognizer.start_continuous_recognition()
#
# # Open an input stream from the default microphone using sounddevice.
# with sd.InputStream(samplerate=sample_rate, channels=channels, dtype='int16', callback=audio_callback):
#     try:
#         # Keep the script running to capture audio.
#         while True:
#             sd.sleep(1000)
#     except KeyboardInterrupt:
#         print("Stopping...")
#
# # Stop the recognizer and close the push stream.
# speech_recognizer.stop_continuous_recognition()
# push_stream.close()
# print("Recognition stopped.")













# import azure.cognitiveservices.speech as speechsdk
# import sounddevice as sd
# import numpy as np
#
# # Replace with your actual Azure Speech subscription key and region.
# SPEECH_KEY = SPEECH_KEY
# SPEECH_REGION = SPEECH_REGION
#
# # Configure the Azure Speech Service.
# speech_config = speechsdk.SpeechConfig(subscription=SPEECH_KEY, region=SPEECH_REGION)
# speech_config.set_property(speechsdk.PropertyId.SpeechServiceConnection_InitialSilenceTimeoutMs, "5000")  # 5 seconds
# speech_config.set_property(speechsdk.PropertyId.SpeechServiceConnection_EndSilenceTimeoutMs, "2000")      # 2 seconds
#
# # Define the audio format for the PushAudioInputStream: 16 kHz, 16-bit, mono.
# audio_format = speechsdk.audio.AudioStreamFormat(
#     samples_per_second=16000, bits_per_sample=16, channels=1
# )
#
# # Create a push stream to feed audio data into the recognizer.
# push_stream = speechsdk.audio.PushAudioInputStream(audio_format)
# audio_config = speechsdk.audio.AudioConfig(stream=push_stream)
#
# # Create the Speech Recognizer.
# speech_recognizer = speechsdk.SpeechRecognizer(
#     speech_config=speech_config, audio_config=audio_config, language="en-IN"
# )
#
# # Event handler for recognized speech.
# def on_recognized(evt):
#     if evt.result.reason == speechsdk.ResultReason.RecognizedSpeech:
#         text = evt.result.text.strip()
#         if text:
#             print("Recognized:", text)
#         else:
#             # RecognizedSpeech with empty text might indicate silence.
#             print("Silence detected (empty recognition result).")
#     elif evt.result.reason == speechsdk.ResultReason.NoMatch:
#         # NoMatch indicates that the service did not recognize any speech.
#         print("NoMatch event: Silence or unrecognized audio detected.")
#
# # Event handler for canceled recognition.
# def on_canceled(evt):
#     print("Recognition canceled:", evt.result.cancellation_details.reason)
#     if evt.result.cancellation_details.reason == speechsdk.CancellationReason.Error:
#         print("Error details:", evt.result.cancellation_details.error_details)
#
# # Event handler for session started.
# def on_session_started(evt):
#     print("Session started.")
#
# # Event handler for session stopped.
# def on_session_stopped(evt):
#     print("Session stopped.")
#
# # Connect event handlers.
# speech_recognizer.recognized.connect(on_recognized)
# speech_recognizer.canceled.connect(on_canceled)
# speech_recognizer.session_started.connect(on_session_started)
# speech_recognizer.session_stopped.connect(on_session_stopped)
#
# # Microphone callback function called for each audio block.
# def audio_callback(indata, frames, time_info, status):
#     if status:
#         print("Stream status:", status)
#     # Convert the numpy array (16-bit PCM) to bytes and push into the stream.
#     push_stream.write(indata.tobytes())
#
# # Microphone parameters.
# sample_rate = 16000  # Hz
# channels = 1         # Mono audio
#
# print("Starting microphone stream and speech recognition. Press Ctrl+C to stop.")
#
# # Start the Azure recognizer.
# speech_recognizer.start_continuous_recognition()
#
# # Open an input stream from the default microphone using sounddevice.
# with sd.InputStream(samplerate=sample_rate, channels=channels, dtype='int16', callback=audio_callback):
#     try:
#         # Keep the script running to capture audio.
#         while True:
#             sd.sleep(1000)
#     except KeyboardInterrupt:
#         print("Stopping...")
#
# # Stop the recognizer and close the push stream.
# speech_recognizer.stop_continuous_recognition()
# push_stream.close()
# print("Recognition stopped.")
