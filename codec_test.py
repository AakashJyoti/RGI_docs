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



# Example usage:
# combined_audio = b"".join(self.audio_chunks)  # Your combined audio bytes
# convert_mu_law_without_reencoding(combined_audio, "chunks2.wav")