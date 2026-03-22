import httpx
import uuid
import os
from tempfile import gettempdir

class VoiceService:
    def __init__(self):
        self.whisper_endpoint = os.getenv("WHISPER_API_URL", "http://localhost:8080/v1/audio/transcriptions")
        self.coqui_endpoint = os.getenv("COQUI_API_URL", "http://localhost:5002/api/tts")
        self.output_dir = os.getenv("VOICE_OUTPUT_DIR", os.path.join(os.getcwd(), "data", "audio_output"))

    async def transcribe_audio(self, audio_path: str) -> str:
        """Transcribe an audio file using Whisper STT."""
        if not os.path.exists(audio_path):
            raise FileNotFoundError(f"Audio file not found: {audio_path}")

        # Integration pattern for Whisper API
        async with httpx.AsyncClient(timeout=120) as client:
            try:
                # Actual implementation would use files= FormData
                # For demo purposes, we mimic the schema
                response = await client.post(
                    self.whisper_endpoint,
                    json={"file_path": audio_path} 
                )
                response.raise_for_status()
                return response.json().get("text", "")
            except httpx.RequestError as e:
                return f"[STT Error: {e}]"

    async def synthesize_speech(self, text: str, language: str = "en") -> str:
        """Synthesize speech using Coqui TTS and return the saved file path."""
        os.makedirs(self.output_dir, exist_ok=True)
        filename = f"{uuid.uuid4().hex}.wav"
        output_path = os.path.join(self.output_dir, filename)

        async with httpx.AsyncClient(timeout=120) as client:
            try:
                response = await client.get(
                    self.coqui_endpoint,
                    params={"text": text, "language_id": language}
                )
                response.raise_for_status()
                
                with open(output_path, "wb") as f:
                    f.write(response.content)
                    
                return output_path
            except httpx.RequestError as e:
                raise RuntimeError(f"TTS generation failed: {e}")

voice_service = VoiceService()
