"""Text-to-Speech module using ElevenLabs API."""

import os
from pathlib import Path

import httpx


class TTSGenerator:
    """Generates speech audio from text using ElevenLabs."""

    BASE_URL = "https://api.elevenlabs.io/v1"

    def __init__(self, voice_id: str = None, model: str = None):
        self.api_key = os.getenv("ELEVENLABS_API_KEY")
        if not self.api_key:
            raise ValueError("ELEVENLABS_API_KEY environment variable is required")

        self.voice_id = voice_id or os.getenv("ELEVENLABS_VOICE_ID", "21m00Tcm4TlvDq8ikWAM")  # default: Rachel
        self.model = model or "eleven_multilingual_v2"
        self.headers = {
            "xi-api-key": self.api_key,
            "Content-Type": "application/json",
        }

    async def generate(
        self,
        text: str,
        output_path: str,
        stability: float = 0.5,
        similarity_boost: float = 0.75,
        style: float = 0.5,
    ) -> Path:
        """Generate speech audio from text.

        Args:
            text: The text to convert to speech
            output_path: Where to save the audio file
            stability: Voice stability (0-1). Lower = more expressive
            similarity_boost: Voice similarity (0-1). Higher = closer to original voice
            style: Style exaggeration (0-1). Higher = more stylistic

        Returns:
            Path to the generated audio file
        """
        url = f"{self.BASE_URL}/text-to-speech/{self.voice_id}"

        payload = {
            "text": text,
            "model_id": self.model,
            "voice_settings": {
                "stability": stability,
                "similarity_boost": similarity_boost,
                "style": style,
                "use_speaker_boost": True,
            },
        }

        async with httpx.AsyncClient(timeout=120) as client:
            response = await client.post(url, json=payload, headers=self.headers)
            response.raise_for_status()

            output = Path(output_path)
            output.parent.mkdir(parents=True, exist_ok=True)
            output.write_bytes(response.content)

        return output

    async def generate_with_timestamps(
        self,
        text: str,
        output_path: str,
        stability: float = 0.5,
        similarity_boost: float = 0.75,
    ) -> dict:
        """Generate speech with word-level timestamps for caption sync.

        Returns:
            dict with 'audio_path' and 'alignment' (word timestamps)
        """
        url = f"{self.BASE_URL}/text-to-speech/{self.voice_id}/with-timestamps"

        payload = {
            "text": text,
            "model_id": self.model,
            "voice_settings": {
                "stability": stability,
                "similarity_boost": similarity_boost,
                "use_speaker_boost": True,
            },
        }

        async with httpx.AsyncClient(timeout=120) as client:
            response = await client.post(url, json=payload, headers=self.headers)
            response.raise_for_status()

            data = response.json()

            # Save audio
            import base64
            audio_bytes = base64.b64decode(data["audio_base64"])
            output = Path(output_path)
            output.parent.mkdir(parents=True, exist_ok=True)
            output.write_bytes(audio_bytes)

            return {
                "audio_path": str(output),
                "alignment": data.get("alignment", {}),
            }

    async def list_voices(self) -> list[dict]:
        """List available voices."""
        url = f"{self.BASE_URL}/voices"
        async with httpx.AsyncClient(timeout=30) as client:
            response = await client.get(url, headers=self.headers)
            response.raise_for_status()
            data = response.json()
            return [
                {"voice_id": v["voice_id"], "name": v["name"], "category": v.get("category")}
                for v in data.get("voices", [])
            ]
