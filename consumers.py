import json
import base64
import wave
import asyncio
from channels.generic.websocket import AsyncWebsocketConsumer
# from .rgi2 import claim_intimation_flow

class AudioDataConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.call_sid = self.scope['url_route']['kwargs']['call_sid']
        self.group_name = f"call_{self.call_sid}"
        self.audio_chunks = []
        self.media_format = None

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
            if event == "start":
                await self.handle_start_event(data)
            elif event == "media":
                await self.handle_media_event(data)
            elif event == "stop":
                await self.handle_stop_event(data)
            elif event == "request_audio":  # ✅ New event for sending audio
                print("[receive] Received request for audio streaming.")
                filename = "bot_response.wav"
                sample_rate, sampwidth, n_channels = self.extract_wav_params()
                await self.stream_audio_back(filename, sample_rate, sampwidth, n_channels)  # Ensure this file exists
                # await self.stream_audio_back(filename)
            # elif event == "start_claim_flow":
            #     print("[receive] Starting claim flow.")
            #     mobile_number = data.get("mobile_number", "8697745125")
            #     result = await claim_intimation_flow(mobile_number)
            #     await self.send_json({"event": "claim_flow_complete", "result": result})


            else:
                await self.send_json({"error": f"Unknown event: {event}"})
        else:
            await self.send_json({"error": "Binary data not supported."})

    async def handle_start_event(self, data):
        start_data = data.get("start", {})
        required = ["stream_sid", "call_sid", "account_sid", "from", "to", "media_format"]
        missing = [r for r in required if r not in start_data]
        if missing:
            await self.send_json({"error": f"Missing fields in start event: {missing}"})
            return

        self.media_format = start_data["media_format"]
        await self.send_json({"status": "start acknowledged", "stream_sid": start_data["stream_sid"]})

    async def handle_media_event(self, data):
        media_data = data.get("media", {})
        if "chunk" not in media_data or "timestamp" not in media_data or "payload" not in media_data:
            await self.send_json({"error": "Missing media event fields"})
            return

        try:
            decoded_chunk = base64.b64decode(media_data["payload"])
            self.audio_chunks.append(decoded_chunk)
        except Exception:
            await self.send_json({"error": "Invalid Base64 payload"})
            return

        response = {
            "status": "media received",
            "chunk": media_data["chunk"],
            "timestamp": media_data["timestamp"]
        }
        await self.send_json(response)

    async def handle_stop_event(self, data):
        stop_data = data.get("stop", {})
        if "call_sid" not in stop_data or "account_sid" not in stop_data or "reason" not in stop_data:
            await self.send_json({"error": "Missing fields in stop event"})
            return

        await self.send_json({"status": "stop acknowledged", "reason": stop_data["reason"]})

        # Reassemble audio
        combined_audio = b"".join(self.audio_chunks)

        # Write WAV file (optional)
        sample_rate, sampwidth, n_channels = self.extract_wav_params()
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

        # Now send it back to the client using the SAME 'media' event structure
        await self.stream_audio_back(filename, sample_rate, sampwidth, n_channels)

        # Finally, close the WebSocket
        await self.close()

    async def stream_audio_back(self, filename, sample_rate, sampwidth, n_channels):
        """
        Read the WAV file, chunk it into ~20ms segments, and send each chunk
        with the SAME 'media' event structure.
        """
        try:
            filename = f"{self.call_sid}.wav"
            with wave.open(filename, "rb") as wf:
                raw_data = wf.readframes(wf.getnframes())
        except Exception as e:
            print(f"Error reading WAV file: {e}")
            return

        # We can optionally send a new "start" event if you want to mirror the original flow
        # For simplicity, we skip that here and just send 'media' directly.

        chunk_duration = 0.02  # 20 ms
        bytes_per_frame = sampwidth * n_channels
        chunk_size = int(sample_rate * chunk_duration * bytes_per_frame)

        chunk_number = 1
        timestamp = 0
        while True:
            chunk = raw_data[(chunk_number - 1) * chunk_size: chunk_number * chunk_size]
            if not chunk:
                break

            payload = base64.b64encode(chunk).decode("utf-8")

            # Here is the key: we reuse the same 'media' event structure
            reverse_media_event = {
                "event": "media",  # same event name
                "sequence_number": chunk_number,
                "stream_sid": self.call_sid,  # same stream/call ID
                "media": {
                    "chunk": chunk_number,
                    "timestamp": str(timestamp),
                    "payload": payload
                }
            }
            await self.send_json(reverse_media_event)
            print(f"[stream_audio_back] Sent media: chunk={chunk_number}, ts={timestamp}")

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

    def extract_wav_params(self):
        """
        Extract parameters from self.media_format. Adjust for your scenario.
        """
        if self.media_format:
            sample_rate = int(self.media_format.get("sample_rate", 16000))
            bit_rate = int(self.media_format.get("bit_rate", "16"))
            sampwidth = 1 if bit_rate == 8 else 2
            n_channels = int(self.media_format.get("channels", 1)) if "channels" in self.media_format else 1
        else:
            sample_rate = 16000
            sampwidth = 2
            n_channels = 1
        return sample_rate, sampwidth, n_channels
    
    async def transfer_to_agent(self, reason):
        await self.send_json({
            "event": "xfer",
            "sequence_number": 10,
            "stream_sid": self.call_sid,
            "xfer": {
                "call_sid": self.call_sid,
                "account_sid": "YOUR_ACCOUNT",
                "reason": reason
            }
        })
        await self.close()  # Optional: Close WS after transfer

    async def send_json(self, payload):
        await self.send(text_data=json.dumps(payload))
