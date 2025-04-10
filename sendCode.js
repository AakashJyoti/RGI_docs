const fs = require("fs");
const WaveFile = require("wavefile").WaveFile;

const chunks = process.argv[2]; 
const outputPath = process.argv[3];

function createWavHeader({
  sampleRate = 8000,
  bitDepth = 8,
  numChannels = 1,
  audioDataLength,
}) {
  const header = Buffer.alloc(44); // Standard WAV header length

  // RIFF chunk descriptor
  header.write("RIFF", 0); // ChunkID
  header.writeUInt32LE(36 + audioDataLength, 4); // ChunkSize
  header.write("WAVE", 8); // Format

  // fmt sub-chunk
  header.write("fmt ", 12); // Subchunk1ID
  header.writeUInt32LE(16, 16); // Subchunk1Size
  header.writeUInt16LE(1, 20); // AudioFormat (1 = PCM)
  header.writeUInt16LE(numChannels, 22); // NumChannels
  header.writeUInt32LE(sampleRate, 24); // SampleRate
  header.writeUInt32LE((sampleRate * numChannels * bitDepth) / 8, 28); // ByteRate
  header.writeUInt16LE((numChannels * bitDepth) / 8, 32); // BlockAlign
  header.writeUInt16LE(bitDepth, 34); // BitsPerSample

  // data sub-chunk
  header.write("data", 36); // Subchunk2ID
  header.writeUInt32LE(audioDataLength, 40); // Subchunk2Size

  return header;
}

const newData = Buffer.concat(chunks);

const wavHeader = createWavHeader({
  audioDataLength: newData.length,
});

// Replace the original audioData in the buffer
const newBuffer = Buffer.concat([wavHeader, newData]);

const wav = new WaveFile();
wav.fromBuffer(newBuffer);

// Convert from mu-law to PCM
wav.fromMuLaw();

// Resample to 16000 Hz if needed
if (wav.fmt.sampleRate !== 8000) {
  wav.toSampleRate(8000);
}

// Write the converted file
fs.writeFileSync(outputPath, wav.toBuffer());
