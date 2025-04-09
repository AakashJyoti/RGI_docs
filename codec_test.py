import struct
from pathlib import Path

def read_chunk_offsets(buffer, target_chunk_id):
    offset = 12  # Skip RIFF header
    while offset < len(buffer):
        chunk_id = buffer[offset:offset+4].decode('ascii')
        chunk_size = struct.unpack('<I', buffer[offset+4:offset+8])[0]
        if chunk_id == target_chunk_id:
            return {
                'start': offset + 8,
                'end': offset + 8 + chunk_size,
                'header_start': offset,
                'header_size': 8 + chunk_size,
            }
        offset += 8 + chunk_size
    raise ValueError(f"{target_chunk_id} chunk not found")

def read_fmt_chunk(buffer):
    offset = 12
    while offset < len(buffer):
        chunk_id = buffer[offset:offset+4].decode('ascii')
        chunk_size = struct.unpack('<I', buffer[offset+4:offset+8])[0]
        if chunk_id == 'fmt ':
            return {
                'start': offset + 8,
                'size': chunk_size,
                'header_start': offset,
                'header_size': 8 + chunk_size,
            }
        offset += 8 + chunk_size
    raise ValueError("fmt chunk not found")

def convert_mu_law_without_reencoding(input_path, output_path):
    input_path = Path(input_path)
    output_path = Path(output_path)

    buffer = input_path.read_bytes()

    fmt = read_fmt_chunk(buffer)
    fmt_data = buffer[fmt['start']:fmt['start'] + fmt['size']]
    audio_format, num_channels = struct.unpack('<HH', fmt_data[:4])
    sample_rate = struct.unpack('<I', fmt_data[4:8])[0]
    bits_per_sample = struct.unpack('<H', fmt_data[14:16])[0]

    if audio_format != 7:
        print("⚠️  Warning: Audio format is not mu-law (expected format code 7)")

    data_chunk = read_chunk_offsets(buffer, 'data')
    audio_data = buffer[data_chunk['start']:data_chunk['end']]

    sample_width = 1  # 8-bit mu-law
    chunk_duration = 0.02  # 20ms
    chunk_size = int(sample_rate * chunk_duration * sample_width)

    chunks = [audio_data[i:i + chunk_size] for i in range(0, len(audio_data), chunk_size)]
    new_data = b''.join(chunks)

    # Assemble new buffer
    new_buffer = bytearray()
    new_buffer.extend(buffer[:data_chunk['start']])
    new_buffer.extend(new_data)
    new_buffer.extend(buffer[data_chunk['end']:])

    # Update 'data' chunk size
    struct.pack_into('<I', new_buffer, data_chunk['header_start'] + 4, len(new_data))

    # Update RIFF chunk size (total file size - 8)
    struct.pack_into('<I', new_buffer, 4, len(new_buffer) - 8)

    output_path.write_bytes(new_buffer)
    print("✅ Output saved with original mu-law codec.")

# Example usage:
convert_mu_law_without_reencoding("testing.wav", "chunks2.wav")







import struct
from pathlib import Path

def read_chunk_offsets(buffer, target_chunk_id):
    offset = 12  # Skip RIFF header
    while offset < len(buffer):
        chunk_id = buffer[offset:offset+4].decode('ascii')
        chunk_size = struct.unpack('<I', buffer[offset+4:offset+8])[0]
        if chunk_id == target_chunk_id:
            return {
                'start': offset + 8,
                'end': offset + 8 + chunk_size,
                'header_start': offset,
                'header_size': 8 + chunk_size,
            }
        offset += 8 + chunk_size
    raise ValueError(f"{target_chunk_id} chunk not found")

def read_fmt_chunk(buffer):
    offset = 12
    while offset < len(buffer):
        chunk_id = buffer[offset:offset+4].decode('ascii')
        chunk_size = struct.unpack('<I', buffer[offset+4:offset+8])[0]
        if chunk_id == 'fmt ':
            return {
                'start': offset + 8,
                'size': chunk_size,
                'header_start': offset,
                'header_size': 8 + chunk_size,
            }
        offset += 8 + chunk_size
    raise ValueError("fmt chunk not found")

def convert_mu_law_without_reencoding(combined_audio, output_path):
    output_path = Path(output_path)
    buffer = combined_audio  # Use the combined audio bytes directly

    fmt = read_fmt_chunk(buffer)
    fmt_data = buffer[fmt['start']:fmt['start'] + fmt['size']]
    audio_format, num_channels = struct.unpack('<HH', fmt_data[:4])
    sample_rate = struct.unpack('<I', fmt_data[4:8])[0]
    bits_per_sample = struct.unpack('<H', fmt_data[14:16])[0]

    if audio_format != 7:
        print("⚠️  Warning: Audio format is not mu-law (expected format code 7)")

    data_chunk = read_chunk_offsets(buffer, 'data')
    audio_data = buffer[data_chunk['start']:data_chunk['end']]

    sample_width = 1  # 8-bit mu-law
    chunk_duration = 0.02  # 20ms
    chunk_size = int(sample_rate * chunk_duration * sample_width)

    chunks = [audio_data[i:i + chunk_size] for i in range(0, len(audio_data), chunk_size)]
    new_data = b''.join(chunks)

    # Assemble new buffer
    new_buffer = bytearray()
    new_buffer.extend(buffer[:data_chunk['start']])
    new_buffer.extend(new_data)
    new_buffer.extend(buffer[data_chunk['end']:])

    # Update 'data' chunk size
    struct.pack_into('<I', new_buffer, data_chunk['header_start'] + 4, len(new_data))

    # Update RIFF chunk size (total file size - 8)
    struct.pack_into('<I', new_buffer, 4, len(new_buffer) - 8)

    output_path.write_bytes(new_buffer)
    print("✅ Output saved with original mu-law codec.")


import struct
from pathlib import Path


def create_wav_from_chunks(audio_chunks, output_path, sample_rate, num_channels):
    """
    Create a WAV file directly from pre-chunked 20ms mu-law audio data

    :param audio_chunks: List of 20ms audio byte chunks
    :param output_path: Output file path
    :param sample_rate: Original sample rate (e.g., 8000)
    :param num_channels: Number of channels (e.g., 1 for mono)
    """
    # Combine chunks into single continuous audio stream
    raw_audio = b"".join(audio_chunks)

    # ========================================================================
    # Create WAV headers programmatically (mu-law specific)
    # ========================================================================

    # RIFF header
    riff_header = b'RIFF'
    riff_size = 4 + 24 + 8 + len(raw_audio)  # 4 = "WAVE", 24 = fmt chunk, 8 = data header
    riff_chunk = riff_header + struct.pack('<I', riff_size) + b'WAVE'

    # fmt chunk (mu-law format)
    fmt_header = b'fmt '
    fmt_size = 18  # Standard size for PCM/mu-law
    audio_format = 7  # mu-law codec ID
    bits_per_sample = 8
    bytes_per_second = sample_rate * num_channels * bits_per_sample // 8
    block_align = num_channels * bits_per_sample // 8

    fmt_data = struct.pack(
        '<HHIIHH',
        audio_format,
        num_channels,
        sample_rate,
        bytes_per_second,
        block_align,
        bits_per_sample
    )
    fmt_chunk = fmt_header + struct.pack('<I', fmt_size) + fmt_data

    # data chunk
    data_header = b'data'
    data_size = len(raw_audio)
    data_chunk = data_header + struct.pack('<I', data_size) + raw_audio

    # Combine all chunks
    wav_file = riff_chunk + fmt_chunk + data_chunk

    # Write to file
    output_path = Path(output_path)
    output_path.write_bytes(wav_file)
    print(f"✅ Saved {len(audio_chunks)} chunks ({len(raw_audio)} bytes) to {output_path}")

# Example usage:
# create_wav_from_chunks(
#     audio_chunks=self.audio_chunks,
#     output_path="output.wav",
#     sample_rate=8000,  # Must match your actual sample rate
#     num_channels=1     # Must match your actual channel count
# )