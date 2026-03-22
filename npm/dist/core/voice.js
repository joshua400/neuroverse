/**
 * Voice Layer — Interface for STT (Whisper) and TTS (Coqui).
 *
 * Assumes a local or remote REST API serving the models.
 */
import axios from "axios";
import { randomUUID } from "node:crypto";
import { join } from "node:path";
import { writeFileSync, existsSync, mkdirSync } from "node:fs";
let config = {
    whisperEndpoint: "http://localhost:8080/v1/audio/transcriptions", // Standard whisper.cpp / API
    coquiEndpoint: "http://localhost:5002/api/tts", // Standard Coqui server
    outputDirectory: join(process.cwd(), "data", "audio_output"),
};
export function configureVoice(cfg) {
    config = { ...config, ...cfg };
}
/**
 * Transcribe an audio file using Whisper.
 * (Placeholder for actual API implementation — normally takes FormData).
 */
export async function transcribeAudio(audioPath) {
    if (!config.whisperEndpoint)
        throw new Error("Whisper endpoint not configured.");
    // Note: For a real implementation, you'd use form-data and passing the file stream.
    // This serves as the integration pattern.
    try {
        const response = await axios.post(config.whisperEndpoint, { file_path: audioPath }, // Adjust based on your Whisper REST API spec
        { headers: { "Content-Type": "application/json" } });
        return response.data.text ?? "Transcription returned empty.";
    }
    catch (e) {
        const error = e;
        return `[STT Error: ${error.message}]`;
    }
}
/**
 * Synthesize speech using Coqui TTS.
 * Returns the path to the generated audio file.
 */
export async function synthesizeSpeech(text, language = "en") {
    if (!config.coquiEndpoint)
        throw new Error("Coqui TTS endpoint not configured.");
    if (!config.outputDirectory)
        throw new Error("Output directory not configured.");
    if (!existsSync(config.outputDirectory)) {
        mkdirSync(config.outputDirectory, { recursive: true });
    }
    const outputPath = join(config.outputDirectory, `${randomUUID()}.wav`);
    try {
        const response = await axios.get(config.coquiEndpoint, {
            params: { text, language_id: language },
            responseType: "arraybuffer", // For downloading binary audio
        });
        writeFileSync(outputPath, response.data);
        return outputPath;
    }
    catch (e) {
        const error = e;
        throw new Error(`TTS generation failed: ${error.message}`);
    }
}
//# sourceMappingURL=voice.js.map