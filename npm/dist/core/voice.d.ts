/**
 * Voice Layer — Interface for STT (Whisper) and TTS (Coqui).
 *
 * Assumes a local or remote REST API serving the models.
 */
export interface VoiceConfig {
    whisperEndpoint?: string;
    coquiEndpoint?: string;
    outputDirectory?: string;
}
export declare function configureVoice(cfg: Partial<VoiceConfig>): void;
/**
 * Transcribe an audio file using Whisper.
 * (Placeholder for actual API implementation — normally takes FormData).
 */
export declare function transcribeAudio(audioPath: string): Promise<string>;
/**
 * Synthesize speech using Coqui TTS.
 * Returns the path to the generated audio file.
 */
export declare function synthesizeSpeech(text: string, language?: string): Promise<string>;
//# sourceMappingURL=voice.d.ts.map