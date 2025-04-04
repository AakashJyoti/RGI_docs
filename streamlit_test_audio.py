# import streamlit as st
#
# st.text("hello world")
# st.success("Welcome to RGI")
#
# # streamlit run streamlit_test.py --server.address 0.0.0.0 --server.port 8501

import streamlit as st
import os
import azure.cognitiveservices.speech as speechsdk
from io import BytesIO
import base64
from dotenv import load_dotenv

load_dotenv()
SPEECH_KEY="ea81bafd0787487c808e90e4dd006252"
SPEECH_REGION="centralindia"
# Azure Cognitive Services credentials
subscription_key = os.getenv("SPEECH_KEY")  # Set your Azure Speech key in environment variables
region = os.getenv("SPEECH_REGION")  # Set your Azure Speech region in environment variables

def speech_to_text():
    """Convert speech to text using Azure Cognitive Services"""
    speech_config = speechsdk.SpeechConfig(subscription=subscription_key, region=region)
    speech_config.speech_recognition_language = "en-US"

    audio_config = speechsdk.audio.AudioConfig(use_default_microphone=True)
    speech_recognizer = speechsdk.SpeechRecognizer(speech_config=speech_config, audio_config=audio_config)

    st.info("Speak into your microphone...")
    speech_recognition_result = speech_recognizer.recognize_once_async().get()

    if speech_recognition_result.reason == speechsdk.ResultReason.RecognizedSpeech:
        st.success("Speech recognized!")
        return speech_recognition_result.text
    elif speech_recognition_result.reason == speechsdk.ResultReason.NoMatch:
        st.error("No speech could be recognized.")
    elif speech_recognition_result.reason == speechsdk.ResultReason.Canceled:
        cancellation_details = speech_recognition_result.cancellation_details
        st.error(f"Speech Recognition canceled: {cancellation_details.reason}")
        if cancellation_details.reason == speechsdk.CancellationReason.Error:
            st.error(f"Error details: {cancellation_details.error_details}")
    return None


def text_to_speech(text):
    """Convert text to speech using Azure Cognitive Services"""
    speech_config = speechsdk.SpeechConfig(subscription=subscription_key, region=region)
    audio_config = speechsdk.audio.AudioOutputConfig(use_default_speaker=True)  # Prevent direct playback

    speech_config.speech_synthesis_voice_name = 'en-IN-ArjunNeural'
    speech_synthesizer = speechsdk.SpeechSynthesizer(speech_config=speech_config, audio_config=audio_config)

    result = speech_synthesizer.speak_text_async(text).get()

    if result.reason == speechsdk.ResultReason.SynthesizingAudioCompleted:
        st.success("Speech synthesized successfully!")

        # ✅ Read audio data directly instead of using save_to_wav_file()
        stream = speechsdk.AudioDataStream(result)
        audio_buffer = BytesIO(stream)
        audio_buffer.seek(0)
        audio_data = stream.read_data(audio_buffer)  # Get raw WAV data

        # ✅ Store in BytesIO
        # audio_buffer = BytesIO(audio_data)
        # audio_buffer.seek(0)  # Move cursor to the start

        return audio_buffer
    elif result.reason == speechsdk.ResultReason.Canceled:
        cancellation_details = result.cancellation_details
        st.error(f"Speech synthesis canceled: {cancellation_details.reason}")
        if cancellation_details.reason == speechsdk.CancellationReason.Error:
            st.error(f"Error details: {cancellation_details.error_details}")

    return None


# Streamlit UI
st.title("🎤 Azure Voice Assistant 🤖")

# Button to start speech-to-text
if st.button("🎤 Start Recording"):
    user_input = speech_to_text()
    if user_input:
        st.subheader("Your Query:")
        st.write(user_input)

        # Generate a response (replace this with your logic)
        response = f"You said: {user_input}"

        st.subheader("Assistant Response:")
        st.write(response)

        # Convert response to speech
        audio_buffer = text_to_speech(response)
        if audio_buffer:
            # Convert audio buffer to base64 for embedding
            audio_base64 = base64.b64encode(audio_buffer.read()).decode('utf-8')
            audio_html = f'''
            <audio controls autoplay>
                <source src="data:audio/wav;base64,{audio_base64}" type="audio/wav">
            </audio>
            '''
            st.markdown(audio_html, unsafe_allow_html=True)
