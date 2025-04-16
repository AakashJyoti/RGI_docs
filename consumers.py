# import json
# import base64
# import wave
# import asyncio
# import os
# from channels.generic.websocket import AsyncWebsocketConsumer
# import soundfile as sf
# # from pydub import AudioSegment
# from .motor_claim_flow import claim_intimation_flow
#
#
#
# class AudioDataConsumer(AsyncWebsocketConsumer):
#     async def connect(self):
#         self.call_sid = self.scope['url_route']['kwargs']['call_sid']
#         self.group_name = f"call_{self.call_sid}"
#         self.audio_chunks = []
#         self.media_format = None
#         self.claim_flow_running = False  # Flag to track claim flow status
#         self.stop_event = asyncio.Event()
#         self.combined_audio_chunks = None
#         await self.channel_layer.group_add(self.group_name, self.channel_name)
#         await self.accept()
#         print(f"[connect] WebSocket connected for call {self.call_sid}")
#
#     async def disconnect(self, close_code):
#         await self.channel_layer.group_discard(self.group_name, self.channel_name)
#         print(f"[disconnect] WebSocket disconnected for call {self.call_sid}")
#
#     async def receive(self, text_data=None, bytes_data=None):
#         if text_data:
#             try:
#                 data = json.loads(text_data)
#             except json.JSONDecodeError:
#                 await self.send_json({"error": "Invalid JSON"})
#                 return
#
#             event = data.get("event")
#             # print(f"[receive] Received event: {event}")
#
#             if event == "start":
#                 print("[receive] Received start event.")
#                 # await self.handle_start_event(data)
#                 # Start claim flow in the background
#                 asyncio.create_task(self.start_claim_flow(data, websocket_class=self))
#             elif event == "media":
#                 await self.handle_media_event(data)
#             elif event == "stop":
#                 await self.handle_stop_event(data)
#             else:
#                 await self.send_json({"error": f"Unknown event: {event}"})
#         else:
#             await self.send_json({"error": "Binary data not supported."})
#
#     # async def handle_start_event(self, data):
#     #     print("Start Event Called")
#     #     start_data = data.get("start", {})
#     #     required = ["stream_sid", "call_sid", "account_sid", "from", "to", "media_format"]
#     #     missing = [r for r in required if r not in start_data]
#     #     if missing:
#     #         await self.send_json({"error": f"Missing fields in start event: {missing}"})
#     #         return
#     #
#     #     self.media_format = start_data["media_format"]
#     #     # await self.send_json({"status": "start acknowledged", "stream_sid": start_data["stream_sid"]})
#
#     async def handle_start_event(self, data):
#         start_data = data.get("start", {})
#         required = ["stream_sid", "call_sid", "account_sid", "from", "to", "media_format"]
#         missing = [r for r in required if r not in start_data]
#         if missing:
#             await self.send_json({"error": f"Missing fields in start event: {missing}"})
#             return
#
#         self.media_format = start_data["media_format"]
#         # filename = "C:\\Users\\abhik\\Documents\\rgi_motor_websocket_test\\bot_strat_resp_2.wav"
#         # base_path = os.path.dirname(os.path.abspath(__file__))  # Get the current script's directory
#         # parent_directory = os.path.dirname(base_path)  # Go up one directory
#         # output_file = os.path.join(parent_directory, "audio", "Bot", "bot_response.wav")
#         #
#         # sample_rate, sampwidth, n_channels = self.extract_wav_params()
#         #
#         # await self.stream_audio_back(output_file, sample_rate, sampwidth, n_channels)
#
#     async def handle_media_event(self, data):
#         media_data = data.get("media", {})
#         if "chunk" not in media_data or "timestamp" not in media_data or "payload" not in media_data:
#             await self.send_json({"error": "Missing media event fields"})
#             return
#
#         try:
#             decoded_chunk = base64.b64decode(media_data["payload"])
#             # print(f"[handle_media_event] Decoded chunk size: {len(decoded_chunk)}")
#             self.audio_chunks.append(decoded_chunk)
#
#         except Exception:
#             await self.send_json({"error": "Invalid Base64 payload"})
#             return
#
#         response = {
#             "status": "media",
#             "chunk": media_data["chunk"],
#             "timestamp": media_data["timestamp"]
#         }
#         await self.send_json(response)
#
#         # Stream audio back while claim flow is running
#         # if not self.claim_flow_running:
#         #     sample_rate, sampwidth, n_channels = self.extract_wav_params()
#         #     filename = f"{self.call_sid}.wav"
#         #     await self.stream_audio_back(filename, sample_rate, sampwidth, n_channels)
#
#     async def handle_stop_event(self, data):
#         stop_data = data.get("stop", {})
#         if "call_sid" not in stop_data or "account_sid" not in stop_data or "reason" not in stop_data:
#             await self.send_json({"error": "Missing fields in stop event"})
#             return
#
#         await self.send_json({"status": "stop acknowledged", "reason": stop_data["reason"]})
#
#         # Reassemble audio
#         combined_audio = b"".join(self.audio_chunks)
#
#         # print(combined_audio)
#         self.combined_audio_chunks = combined_audio
#         print(type(combined_audio))
#         ctx.call("gg", combined_audio, "D:/reliance/motor_websocket/audio/Bot/call_sid.wav")
#
#         # Write WAV file (optional)
#         sample_rate, sampwidth, n_channels = self.extract_wav_params()
#         sample_rate=44100
#         print(f"[handle_stop_event] Writing WAV file with params: {sample_rate}, {sampwidth}, {n_channels}")
#         print(f"[handle_stop_event] Media format: {self.media_format}")  # Add this lin
#         filename = f"{self.call_sid}.wav"
#         try:
#             with wave.open(filename, "wb") as wf:
#                 wf.setnchannels(n_channels)
#                 wf.setsampwidth(sampwidth)
#                 wf.setframerate(sample_rate)
#                 wf.writeframes(combined_audio)
#             print(f"[handle_stop_event] Wrote WAV file: {filename}")
#         except Exception as e:
#             print(f"Error writing WAV file: {e}")
#
#         # # Finally, close the WebSocket
#         # await self.close()
#         # Signal the claim flow that the stop event has been received
#         self.stop_event.set()
#         print("[handle_stop_event] Stop event received and processed.")
#         self.audio_chunks = []  # Clear the audio chunks for the next segment
#         self.stop_event.clear()  # Reset the stop event for the next segment
#
#
#     async def start_claim_flow(self, data, websocket_class):
#         self.claim_flow_running = True
#         try:
#             mobile_number = data.get("start", {}).get("from", "8697745125")  # Default number
#             result = await claim_intimation_flow(mobile_number, websocket_class)
#             await self.send_json({"event": "claim_flow_complete", "result": result})
#
#         except Exception as e:
#             print(f"Error in claim flow: {e}")
#             await self.send_json({"event": "claim_flow_error", "error": str(e)})
#         finally:
#             self.claim_flow_running = False
#             # Close the WebSocket connection after the flow completes
#             print("[start_claim_flow] Claim flow completed. Closing WebSocket.")
#             await self.close()
#
#     async def stream_audio_back(self, filename, sample_rate, sampwidth, n_channels):
#         """
#         Read the WAV file, chunk it into ~20ms segments, and send each chunk
#         with the SAME 'media' event structure.
#         """
#         print("calling stream audio")
#         try:
#             print("stream file name is :",filename)
#             with wave.open(filename, "rb") as wf:
#                 raw_data = wf.readframes(wf.getnframes())
#
#             print("File process complete")
#         except Exception as e:
#             print(f"Error reading WAV file: {e}")
#             return
#
#         chunk_duration = 0.02  # 20 ms
#         bytes_per_frame = sampwidth * n_channels
#         print("Bytes per frame:", bytes_per_frame)
#         chunk_size = int(sample_rate * chunk_duration * bytes_per_frame)
#         print("Chunk size:", chunk_size)
#         chunk_number = 1
#         timestamp = 0
#         while True:
#             chunk = raw_data[(chunk_number - 1) * chunk_size: chunk_number * chunk_size]
#             if len(chunk) == 0:
#                 break
#             payload = base64.b64encode(chunk).decode("utf-8")
#             reverse_media_event = {
#                 "event": "media",
#                 "sequence_number": chunk_number,
#                 "stream_sid":123,
#                 "media": {
#                     "chunk": chunk_number,
#                     "timestamp": str(timestamp),
#                     "payload": payload
#                 }
#             }
#             await self.send_json(reverse_media_event)
#             # print(f"[stream_audio_back] Sent media: chunk={chunk_number}, ts={timestamp}")
#             await asyncio.sleep(chunk_duration)
#             chunk_number += 1
#             timestamp += int(chunk_duration * 1000)
#
#         # Optionally send a 'stop' event to indicate no more reverse data
#         # so the client knows to finalize.
#         reverse_stop_event = {
#             "event": "stop",
#             "sequence_number": chunk_number,
#             "stream_sid": self.call_sid,
#             "stop": {
#                 "call_sid": self.call_sid,
#                 "account_sid": "server",
#                 "reason": "reverse complete"
#             }
#         }
#         await self.send_json(reverse_stop_event)
#         print("[stream_audio_back] Sent final stop event for reverse")
#
#     # def extract_wav_params(self):
#     #     """
#     #     Extract parameters from self.media_format. Adjust for your scenario.
#     #     """
#     #     if self.media_format:
#     #         sample_rate = int(self.media_format.get("sample_rate", 16000))
#     #         bit_rate = int(self.media_format.get("bit_rate", "16"))
#     #         sampwidth = 1 if bit_rate == 8 else 2
#     #         n_channels = int(self.media_format.get("channels", 1)) if "channels" in self.media_format else 1
#     #     else:
#     #         sample_rate = 16000
#     #         sampwidth = 2
#     #         n_channels = 1
#     #     return sample_rate, sampwidth, n_channels
#     def extract_wav_params(self):
#         """
#         Extract parameters from self.media_format. Adjust for your scenario.
#         """
#         if self.media_format:
#             print("If media format is called..")
#             sample_rate = int(self.media_format.get("sample_rate", 16000))
#             bit_rate = int(self.media_format.get("bit_rate", "16"))
#             sampwidth = 1 if bit_rate == 8 else 2
#             n_channels = int(self.media_format.get("channels", 1)) if "channels" in self.media_format else 1
#         else:
#             print("Else media format is called..")
#             sample_rate = 16000
#             sampwidth = 2
#             n_channels = 1
#
#         print(sample_rate, sampwidth, n_channels)
#         return sample_rate, sampwidth, n_channels
#
#     async def transfer_to_agent(self, reason):
#         xfer_event = {
#             "event": "xfer",
#             "sequence_number": 10,
#             "stream_sid": self.call_sid,
#             "xfer": {
#                 "call_sid": self.call_sid,
#                 "account_sid": "YOUR_ACCOUNT",
#                 "reason": reason
#             }
#         }
#         await self.send_json(xfer_event)
#         # await self.close()  # Optional: Close WS after transfer
#
#
#     async def send_json(self, payload):
#         await self.send(text_data=json.dumps(payload))






















import json
import base64
import wave
import asyncio
import os
from channels.generic.websocket import AsyncWebsocketConsumer
import azure.cognitiveservices.speech as speechsdk

import soundfile as sf
# from pydub import AudioSegment
from .motor_claim_flow import claim_intimation_flow



class AudioDataConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.call_sid = self.scope['url_route']['kwargs']['call_sid']
        self.group_name = f"call_{self.call_sid}"
        self.audio_chunks = []
        self.media_format = None
        self.claim_flow_running = False  # Flag to track claim flow status
        self.stop_event = asyncio.Event()
        self.combined_audio_chunks = None
        await self.channel_layer.group_add(self.group_name, self.channel_name)
        await self.accept()
        print(f"[connect] WebSocket connected for call {self.call_sid}")


        self.final_text_received = None

        # --- Speech SDK integration state ---
        self.current_segment = []  # Accumulates recognized text chunks for the current segment.
        self.final_text = ""       # Holds the final transcript for the current segment.
        self.loop = asyncio.get_running_loop()  # Save the current asyncio event loop.

        # Initialize the Azure Speech recognizer.
        self.init_speech_recognition()

    def init_speech_recognition(self):
        # Replace these values with your actual Azure Speech subscription details.
        # SPEECH_KEY = "<YOUR_SPEECH_KEY>"
        # SPEECH_REGION = "<YOUR_SPEECH_REGION>"
        SPEECH_KEY = "ea81bafd0787487c808e90e4dd006252"
        SPEECH_REGION = "centralindia"

        speech_config = speechsdk.SpeechConfig(subscription=SPEECH_KEY, region=SPEECH_REGION)
        # Configure silence timeouts (in milliseconds). Adjust these values as needed.
        speech_config.set_property(speechsdk.PropertyId.SpeechServiceConnection_InitialSilenceTimeoutMs, "2000")
        speech_config.set_property(speechsdk.PropertyId.SpeechServiceConnection_EndSilenceTimeoutMs, "1000")

        # Define the expected audio format. Here we assume 16 kHz, 16-bit, mono audio.
        audio_format = speechsdk.audio.AudioStreamFormat(
            samples_per_second=16000,
            bits_per_sample=16,
            channels=1
        )

        # Create the push audio input stream.
        self.push_stream = speechsdk.audio.PushAudioInputStream(audio_format)
        audio_config = speechsdk.audio.AudioConfig(stream=self.push_stream)

        # Initialize the speech recognizer.
        self.recognizer = speechsdk.SpeechRecognizer(
            speech_config=speech_config,
            audio_config=audio_config,
            language="en-IN"
        )

        # Register event handlers.
        self.recognizer.recognized.connect(self.on_recognized)
        self.recognizer.session_started.connect(self.on_session_started)
        self.recognizer.session_stopped.connect(self.on_session_stopped)
        self.recognizer.canceled.connect(self.on_canceled)

        # Start continuous recognition.
        self.recognizer.start_continuous_recognition()
        print("[Speech] Continuous recognition started.")

    # --------------- Speech SDK Event Handlers ---------------

    def on_recognized(self, evt):
        """
        This event handler is invoked when the Speech SDK produces a final recognition result.
        When a non-empty result is received, it is accumulated. When an empty result is received
        (which indicates that silence has been detected after some speech), it finalizes the current segment.
        """
        if evt.result.reason == speechsdk.ResultReason.RecognizedSpeech:
            recognized_text = evt.result.text.strip()
            if recognized_text:
                # Append recognized text to the current segment.
                self.current_segment.append(recognized_text)
                print(f"[Speech] Recognized chunk: {recognized_text}")
            else:
                # An empty final result indicates silence. If there's any accumulated text, finalize it.
                if self.current_segment:
                    self.final_text = " ".join(self.current_segment)
                    self.final_text_received = self.final_text
                    print(f"[Speech] Silence detected. Final transcript: {self.final_text}")
                    # Schedule sending the transcript back to the client.
                    # Use run_coroutine_threadsafe because this handler runs on a different thread.
                    asyncio.run_coroutine_threadsafe(self.send_transcript(), self.loop)
                    # Reset the accumulator for the next segment.
                    self.current_segment = []
        elif evt.result.reason == speechsdk.ResultReason.NoMatch:
            print("[Speech] No match for the spoken audio.")

    def on_session_started(self, evt):
        print("[Speech] Session started.")

    def on_session_stopped(self, evt):
        print("[Speech] Session stopped.")

    def on_canceled(self, evt):
        cancellation_details = evt.result.cancellation_details
        print(f"[Speech] Recognition canceled: {cancellation_details.reason}")
        print(f"[Speech] Error details: {cancellation_details.error_details}")

    async def send_transcript(self):
        """
        Called (via run_coroutine_threadsafe) when silence is detected.
        Sends the accumulated transcript to the client (or triggers further processing).
        """
        await self.send_json({"status": "transcript", "transcript": self.final_text})
        # Optionally, you could trigger further processing (e.g., call claim_intimation_flow) here.
        # After sending, clear the final transcript.
        self.final_text = ""

    # --------------- Channels WebSocket Handlers ---------------



    async def disconnect(self, close_code):
        await self.channel_layer.group_discard(self.group_name, self.channel_name)
        print(f"[disconnect] WebSocket disconnected for call {self.call_sid}")

    async def receive(self, text_data=None, bytes_data=None):
        if text_data:
            try:
                data = json.loads(text_data)
            except json.JSONDecodeError:
                await self.send_json({"error": "Invalid JSON"})
                return

            event = data.get("event")
            # print(f"[receive] Received event: {event}")

            if event == "start":
                print("[receive] Received start event.")
                # await self.handle_start_event(data)
                # Start claim flow in the background
                asyncio.create_task(self.start_claim_flow(data, websocket_class=self))
            elif event == "media":
                await self.handle_media_event(data)
            elif event == "stop":
                await self.handle_stop_event(data)
            else:
                await self.send_json({"error": f"Unknown event: {event}"})
        else:
            await self.send_json({"error": "Binary data not supported."})

    # async def handle_start_event(self, data):
    #     print("Start Event Called")
    #     start_data = data.get("start", {})
    #     required = ["stream_sid", "call_sid", "account_sid", "from", "to", "media_format"]
    #     missing = [r for r in required if r not in start_data]
    #     if missing:
    #         await self.send_json({"error": f"Missing fields in start event: {missing}"})
    #         return
    #
    #     self.media_format = start_data["media_format"]
    #     # await self.send_json({"status": "start acknowledged", "stream_sid": start_data["stream_sid"]})

    async def handle_start_event(self, data):
        start_data = data.get("start", {})
        required = ["stream_sid", "call_sid", "account_sid", "from", "to", "media_format"]
        missing = [r for r in required if r not in start_data]
        if missing:
            await self.send_json({"error": f"Missing fields in start event: {missing}"})
            return

        self.media_format = start_data["media_format"]
        # filename = "C:\\Users\\abhik\\Documents\\rgi_motor_websocket_test\\bot_strat_resp_2.wav"
        # base_path = os.path.dirname(os.path.abspath(__file__))  # Get the current script's directory
        # parent_directory = os.path.dirname(base_path)  # Go up one directory
        # output_file = os.path.join(parent_directory, "audio", "Bot", "bot_response.wav")
        #
        # sample_rate, sampwidth, n_channels = self.extract_wav_params()
        #
        # await self.stream_audio_back(output_file, sample_rate, sampwidth, n_channels)

    async def handle_media_event(self, data):
        media_data = data.get("media", {})
        if "chunk" not in media_data or "timestamp" not in media_data or "payload" not in media_data:
            await self.send_json({"error": "Missing media event fields"})
            return

        try:
            decoded_chunk = base64.b64decode(media_data["payload"])
            # print(f"[handle_media_event] Decoded chunk size: {len(decoded_chunk)}")
            self.audio_chunks.append(decoded_chunk)
            self.push_stream.write(decoded_chunk)

        except Exception:
            await self.send_json({"error": "Invalid Base64 payload"})
            return

        response = {
            "status": "media",
            "chunk": media_data["chunk"],
            "timestamp": media_data["timestamp"]
        }
        await self.send_json(response)

        # Stream audio back while claim flow is running
        # if not self.claim_flow_running:
        #     sample_rate, sampwidth, n_channels = self.extract_wav_params()
        #     filename = f"{self.call_sid}.wav"
        #     await self.stream_audio_back(filename, sample_rate, sampwidth, n_channels)

    async def handle_stop_event(self, data):
        stop_data = data.get("stop", {})
        if "call_sid" not in stop_data or "account_sid" not in stop_data or "reason" not in stop_data:
            await self.send_json({"error": "Missing fields in stop event"})
            return

        await self.send_json({"status": "stop acknowledged", "reason": stop_data["reason"]})

        # Reassemble audio
        combined_audio = b"".join(self.audio_chunks)

        # print(combined_audio)
        self.combined_audio_chunks = combined_audio
        print(type(combined_audio))
        # ctx.call("gg", combined_audio, "D:/reliance/motor_websocket/audio/Bot/call_sid.wav")

        # Write WAV file (optional)
        sample_rate, sampwidth, n_channels = self.extract_wav_params()
        sample_rate=44100
        print(f"[handle_stop_event] Writing WAV file with params: {sample_rate}, {sampwidth}, {n_channels}")
        print(f"[handle_stop_event] Media format: {self.media_format}")  # Add this lin
        filename = f"{self.call_sid}.wav"
        try:
            with wave.open(filename, "wb") as wf:
                wf.setnchannels(n_channels)
                wf.setsampwidth(sampwidth)
                wf.setframerate(sample_rate)
                wf.writeframes(combined_audio)
            print(f"[handle_stop_event] Wrote WAV file: {filename}")
        except Exception as e:
            print(f"Error writing WAV file: {e}")

        # # Finally, close the WebSocket
        # await self.close()
        # Signal the claim flow that the stop event has been received
        self.stop_event.set()
        print("[handle_stop_event] Stop event received and processed.")
        self.audio_chunks = []  # Clear the audio chunks for the next segment
        self.stop_event.clear()  # Reset the stop event for the next segment


    async def start_claim_flow(self, data, websocket_class):
        self.claim_flow_running = True
        try:
            mobile_number = data.get("start", {}).get("from", "8697745125")  # Default number
            result = await claim_intimation_flow(mobile_number, websocket_class)
            await self.send_json({"event": "claim_flow_complete", "result": result})

        except Exception as e:
            print(f"Error in claim flow: {e}")
            await self.send_json({"event": "claim_flow_error", "error": str(e)})
        finally:
            self.claim_flow_running = False
            # Close the WebSocket connection after the flow completes
            print("[start_claim_flow] Claim flow completed. Closing WebSocket.")
            await self.close()

    async def stream_audio_back(self, filename, sample_rate, sampwidth, n_channels):
        """
        Read the WAV file, chunk it into ~20ms segments, and send each chunk
        with the SAME 'media' event structure.
        """
        print("calling stream audio")
        try:
            print("stream file name is :",filename)
            with wave.open(filename, "rb") as wf:
                raw_data = wf.readframes(wf.getnframes())

            print("File process complete")
        except Exception as e:
            print(f"Error reading WAV file: {e}")
            return

        chunk_duration = 0.02  # 20 ms
        bytes_per_frame = sampwidth * n_channels
        print("Bytes per frame:", bytes_per_frame)
        chunk_size = int(sample_rate * chunk_duration * bytes_per_frame)
        print("Chunk size:", chunk_size)
        chunk_number = 1
        timestamp = 0
        while True:
            chunk = raw_data[(chunk_number - 1) * chunk_size: chunk_number * chunk_size]
            if len(chunk) == 0:
                break
            payload = base64.b64encode(chunk).decode("utf-8")
            reverse_media_event = {
                "event": "media",
                "sequence_number": chunk_number,
                "stream_sid":123,
                "media": {
                    "chunk": chunk_number,
                    "timestamp": str(timestamp),
                    "payload": payload
                }
            }
            await self.send_json(reverse_media_event)
            # print(f"[stream_audio_back] Sent media: chunk={chunk_number}, ts={timestamp}")
            await asyncio.sleep(chunk_duration)
            chunk_number += 1
            timestamp += int(chunk_duration * 1000)

        # Optionally send a 'stop' event to indicate no more reverse data
        # so the client knows to finalize.
        reverse_stop_event = {
            "event": "stop",
            "sequence_number": chunk_number,
            "stream_sid": self.call_sid,
            "stop": {
                "call_sid": self.call_sid,
                "account_sid": "server",
                "reason": "reverse complete"
            }
        }
        await self.send_json(reverse_stop_event)
        print("[stream_audio_back] Sent final stop event for reverse")

    # def extract_wav_params(self):
    #     """
    #     Extract parameters from self.media_format. Adjust for your scenario.
    #     """
    #     if self.media_format:
    #         sample_rate = int(self.media_format.get("sample_rate", 16000))
    #         bit_rate = int(self.media_format.get("bit_rate", "16"))
    #         sampwidth = 1 if bit_rate == 8 else 2
    #         n_channels = int(self.media_format.get("channels", 1)) if "channels" in self.media_format else 1
    #     else:
    #         sample_rate = 16000
    #         sampwidth = 2
    #         n_channels = 1
    #     return sample_rate, sampwidth, n_channels
    def extract_wav_params(self):
        """
        Extract parameters from self.media_format. Adjust for your scenario.
        """
        if self.media_format:
            print("If media format is called..")
            sample_rate = int(self.media_format.get("sample_rate", 16000))
            bit_rate = int(self.media_format.get("bit_rate", "16"))
            sampwidth = 1 if bit_rate == 8 else 2
            n_channels = int(self.media_format.get("channels", 1)) if "channels" in self.media_format else 1
        else:
            print("Else media format is called..")
            sample_rate = 16000
            sampwidth = 2
            n_channels = 1

        print(sample_rate, sampwidth, n_channels)
        return sample_rate, sampwidth, n_channels

    async def transfer_to_agent(self, reason):
        xfer_event = {
            "event": "xfer",
            "sequence_number": 10,
            "stream_sid": self.call_sid,
            "xfer": {
                "call_sid": self.call_sid,
                "account_sid": "YOUR_ACCOUNT",
                "reason": reason
            }
        }
        await self.send_json(xfer_event)
        # await self.close()  # Optional: Close WS after transfer


    async def send_json(self, payload):
        await self.send(text_data=json.dumps(payload))