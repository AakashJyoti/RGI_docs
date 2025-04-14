import json
import base64
import wave
import asyncio
import os
from channels.generic.websocket import AsyncWebsocketConsumer
import soundfile as sf

# from pydub import AudioSegment
from .motor_claim_flow import claim_intimation_flow

import struct
import base64
import io
from scipy.io import wavfile
import numpy as np


def create_wav_header(audio_data_length):
    sample_rate = 8000
    bit_depth = 8
    num_channels = 1
    # Create a byte array for the header (standard WAV header length is 44 bytes)
    header = bytearray(44)

    # RIFF chunk descriptor
    header[0:4] = b"RIFF"  # ChunkID
    struct.pack_into("<I", header, 4, 36 + audio_data_length)  # ChunkSize
    header[8:12] = b"WAVE"  # Format

    # fmt sub-chunk
    header[12:16] = b"fmt "  # Subchunk1ID
    struct.pack_into("<I", header, 16, 16)  # Subchunk1Size
    struct.pack_into("<H", header, 20, 1)  # AudioFormat (1 = PCM)
    struct.pack_into("<H", header, 22, num_channels)  # NumChannels
    struct.pack_into("<I", header, 24, sample_rate)  # SampleRate
    struct.pack_into(
        "<I", header, 28, (sample_rate * num_channels * bit_depth) // 8
    )  # ByteRate
    struct.pack_into("<H", header, 32, (num_channels * bit_depth) // 8)  # BlockAlign
    struct.pack_into("<H", header, 34, bit_depth)  # BitsPerSample

    # data sub-chunk
    header[36:40] = b"data"  # Subchunk2ID
    struct.pack_into("<I", header, 40, audio_data_length)  # Subchunk2Size

    return header


def mu_law_to_pcm(mu_law_data):
    """Convert μ-law encoded bytes to 16-bit PCM using NumPy"""
    mu = np.frombuffer(mu_law_data, dtype=np.uint8)
    # μ-law expansion formula
    mu = mu.astype(np.int16)
    sign = 1 - ((mu & 0x80) >> 7) * 2
    magnitude = mu & 0x7F
    exponent = (magnitude >> 4) & 0x07
    mantissa = magnitude & 0x0F
    pcm = sign * ((0x01 << exponent) * (mantissa << 1) + (1 << exponent) + -0x84)
    return pcm.astype(np.int16)


def resample_audio(data, orig_rate, target_rate):
    """Simple resampling using linear interpolation"""
    ratio = target_rate / orig_rate
    n_samples = int(len(data) * ratio)
    x_old = np.linspace(0, 1, len(data))
    x_new = np.linspace(0, 1, n_samples)
    return np.interp(x_new, x_old, data).astype(np.int16)


class AudioDataConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.call_sid = self.scope["url_route"]["kwargs"]["call_sid"]
        self.group_name = f"call_{self.call_sid}"
        self.audio_chunks = []
        self.media_format = None
        self.claim_flow_running = False  # Flag to track claim flow status
        self.stop_event = asyncio.Event()
        self.combined_audio_chunks = None
        await self.channel_layer.group_add(self.group_name, self.channel_name)
        await self.accept()
        print(f"[connect] WebSocket connected for call {self.call_sid}")

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
        required = [
            "stream_sid",
            "call_sid",
            "account_sid",
            "from",
            "to",
            "media_format",
        ]
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
        if (
            "chunk" not in media_data
            or "timestamp" not in media_data
            or "payload" not in media_data
        ):
            await self.send_json({"error": "Missing media event fields"})
            return

        try:
            decoded_chunk = base64.b64decode(media_data["payload"])
            # print(f"[handle_media_event] Decoded chunk size: {len(decoded_chunk)}")
            self.audio_chunks.append(decoded_chunk)

        except Exception:
            await self.send_json({"error": "Invalid Base64 payload"})
            return

        response = {
            "status": "media",
            "chunk": media_data["chunk"],
            "timestamp": media_data["timestamp"],
        }
        await self.send_json(response)

        # Stream audio back while claim flow is running
        # if not self.claim_flow_running:
        #     sample_rate, sampwidth, n_channels = self.extract_wav_params()
        #     filename = f"{self.call_sid}.wav"
        #     await self.stream_audio_back(filename, sample_rate, sampwidth, n_channels)

    async def handle_stop_event(self, data):
        stop_data = data.get("stop", {})
        if (
            "call_sid" not in stop_data
            or "account_sid" not in stop_data
            or "reason" not in stop_data
        ):
            await self.send_json({"error": "Missing fields in stop event"})
            return

        await self.send_json(
            {"status": "stop acknowledged", "reason": stop_data["reason"]}
        )

        # Reassemble audio
        combined_audio = b"".join(self.audio_chunks)

        # Create header with correct data size
        wav_header = create_wav_header(data_size=len(combined_audio))
        wav_data = wav_header + combined_audio

        # 3. Process in memory using file-like objects
        target_sample_rate = 8000
        with io.BytesIO(wav_data) as wav_buffer:
            # Read WAV file from memory
            sample_rate, audio = wavfile.read(wav_buffer)

            # Convert mu-law to PCM if needed (8-bit data assumed to be mu-law)
            if audio.dtype == np.int8:
                # μ-law expansion formula
                mu = audio.astype(np.int16)
                sign = 1 - ((mu & 0x80) >> 7) * 2
                magnitude = mu & 0x7F
                exponent = (magnitude >> 4) & 0x07
                mantissa = magnitude & 0x0F
                audio = sign * (
                    (0x01 << exponent) * (mantissa << 1) + (1 << exponent) + -0x84
                )
                audio = audio.astype(np.int16)

            # Resample if needed (simple example - for better quality use librosa)
            if sample_rate != target_sample_rate:
                # Calculate new length
                new_length = int(len(audio) * target_sample_rate / sample_rate)

                # Create interpolation indices
                x_old = np.linspace(0, len(audio) - 1, len(audio))
                x_new = np.linspace(0, len(audio) - 1, new_length)

                # Linear interpolation
                audio = np.interp(x_new, x_old, audio).astype(np.int16)

            # Write final output to memory first
            with io.BytesIO() as output_buffer:
                wavfile.write(output_buffer, target_sample_rate, audio)

                # Write to final output file
                with open(
                    "D:/reliance/motor_websocket/audio/Bot/call_sid.wav", "wb"
                ) as f:
                    f.write(output_buffer.getvalue())

        # print(combined_audio)
        self.combined_audio_chunks = combined_audio

        # Write WAV file (optional)
        sample_rate, sampwidth, n_channels = self.extract_wav_params()
        sample_rate = 44100
        print(
            f"[handle_stop_event] Writing WAV file with params: {sample_rate}, {sampwidth}, {n_channels}"
        )
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
            mobile_number = data.get("start", {}).get(
                "from", "8697745125"
            )  # Default number
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
            print("stream file name is :", filename)
            with wave.open(filename, "rb") as wf:
                raw_data = wf.readframes(wf.getnframes())

            print("File process complete")
        except Exception as e:
            print(f"Error reading WAV file: {e}")
            return

        # try:
        #     print(f"Reading WAV file: {filename}")
        #     # Load the audio file using pydub
        #     audio = AudioSegment.from_file(filename, format="wav")
        #
        #     # Extract parameters
        #     sample_rate = audio.frame_rate
        #     sampwidth = audio.sample_width
        #     n_channels = audio.channels
        #
        #     # Convert audio to raw PCM data
        #     raw_data = audio.raw_data
        # except Exception as e:
        #     print(f"Error reading WAV file: {e}")
        #     return

        # try:
        #     print("Stream file name is:", filename)
        #     raw_data, sample_rate = sf.read(filename)
        #     with sf.SoundFile(filename) as file:
        #         n_channels = file.channels
        #         subtype = file.subtype
        #         print(subtype)
        #         if subtype == 'PCM_16':
        #             sampwidth = 2
        #         elif subtype in ['U-Law', 'A-Law']:
        #             sampwidth = 1
        #         else:
        #             raise ValueError(f"Unsupported subtype: {subtype}")
        #
        #     print("Sample rate:", sample_rate)
        #     print("Channels:", n_channels)
        #     print("Sample width:", sampwidth, "bytes")
        #     print("File process complete")
        #
        # except Exception as e:
        #     print(f"Error reading WAV file: {e}")

        chunk_duration = 0.02  # 20 ms
        bytes_per_frame = sampwidth * n_channels
        print("Bytes per frame:", bytes_per_frame)
        chunk_size = int(sample_rate * chunk_duration * bytes_per_frame)
        print("Chunk size:", chunk_size)
        chunk_number = 1
        timestamp = 0
        while True:
            chunk = raw_data[
                (chunk_number - 1) * chunk_size : chunk_number * chunk_size
            ]
            if len(chunk) == 0:
                break
            payload = base64.b64encode(chunk).decode("utf-8")
            reverse_media_event = {
                "event": "media",
                "sequence_number": chunk_number,
                "stream_sid": 123,
                "media": {
                    "chunk": chunk_number,
                    "timestamp": str(timestamp),
                    "payload": payload,
                },
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
                "reason": "reverse complete",
            },
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
            n_channels = (
                int(self.media_format.get("channels", 1))
                if "channels" in self.media_format
                else 1
            )
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
                "reason": reason,
            },
        }
        await self.send_json(xfer_event)
        # await self.close()  # Optional: Close WS after transfer

    async def send_json(self, payload):
        await self.send(text_data=json.dumps(payload))
