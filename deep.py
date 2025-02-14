import streamlit as st
import sounddevice as sd
import numpy as np
from scipy.io.wavfile import write
import os

# Create a "recordings" folder if it doesn't exist
if not os.path.exists("recordings"):
    os.makedirs("recordings")

# Streamlit app title
st.title("Audio Recorder")


# Function to record audio
def record_audio(duration, sample_rate=44100):
    st.write("Recording...")
    recording = sd.rec(
        int(duration * sample_rate), samplerate=sample_rate, channels=2, dtype="int16"
    )
    sd.wait()
    st.write("Recording complete!")
    return recording, sample_rate


# Function to save audio
def save_audio(recording, sample_rate, filename):
    filepath = os.path.join("recordings", filename)
    write(filepath, sample_rate, recording)
    st.write(f"Audio saved as {filepath}")


# Streamlit UI
filename = "recording.wav"

if st.button("Start Recording"):
    if filename.endswith(".wav"):
        recording, sample_rate = record_audio(10)
        save_audio(recording, sample_rate, filename)
    else:
        st.error("Filename must end with .wav")
