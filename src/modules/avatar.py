"""AI Avatar video generation module using HeyGen API."""

import asyncio
import os
from pathlib import Path

import httpx


class AvatarGenerator:
    """Generates talking avatar videos using HeyGen API."""

    BASE_URL = "https://api.heygen.com"

    def __init__(self, avatar_id: str = None):
        self.api_key = os.getenv("HEYGEN_API_KEY")
        if not self.api_key:
            raise ValueError("HEYGEN_API_KEY environment variable is required")

        self.avatar_id = avatar_id or os.getenv("HEYGEN_AVATAR_ID")
        self.headers = {
            "X-Api-Key": self.api_key,
            "Content-Type": "application/json",
        }

    async def generate_from_audio(
        self,
        audio_url: str,
        output_path: str,
        aspect_ratio: str = "9:16",
        background: str = "transparent",
    ) -> Path:
        """Generate avatar video from audio file.

        Args:
            audio_url: URL of the audio file (must be publicly accessible)
            output_path: Where to save the generated video
            aspect_ratio: Video aspect ratio ("9:16" for vertical)
            background: Background type ("transparent", "green_screen", or color hex)

        Returns:
            Path to the downloaded avatar video
        """
        # Map aspect ratio to dimensions
        dimensions = {
            "9:16": {"width": 1080, "height": 1920},
            "16:9": {"width": 1920, "height": 1080},
            "1:1": {"width": 1080, "height": 1080},
        }
        dim = dimensions.get(aspect_ratio, dimensions["9:16"])

        # Create video generation request
        payload = {
            "video_inputs": [
                {
                    "character": {
                        "type": "avatar",
                        "avatar_id": self.avatar_id,
                        "avatar_style": "normal",
                    },
                    "voice": {
                        "type": "audio",
                        "audio_url": audio_url,
                    },
                    "background": {
                        "type": "color",
                        "value": "#00FF00" if background == "green_screen" else "#000000",
                    } if background != "transparent" else {
                        "type": "color",
                        "value": "#00FF00",
                    },
                }
            ],
            "dimension": dim,
            "aspect_ratio": None,  # use explicit dimensions instead
        }

        async with httpx.AsyncClient(timeout=600) as client:
            # Submit video generation
            response = await client.post(
                f"{self.BASE_URL}/v2/video/generate",
                json=payload,
                headers=self.headers,
            )
            response.raise_for_status()
            data = response.json()
            video_id = data["data"]["video_id"]

            # Poll for completion
            video_url = await self._poll_video_status(client, video_id)

            # Download the video
            return await self._download_video(client, video_url, output_path)

    async def generate_from_text(
        self,
        text: str,
        voice_id: str = None,
        output_path: str = "output/avatar.mp4",
        aspect_ratio: str = "9:16",
    ) -> Path:
        """Generate avatar video from text (HeyGen handles TTS).

        Use this if you want HeyGen to handle both avatar AND voice.
        For more control over voice, use generate_from_audio() with ElevenLabs audio.
        """
        dimensions = {
            "9:16": {"width": 1080, "height": 1920},
            "16:9": {"width": 1920, "height": 1080},
            "1:1": {"width": 1080, "height": 1080},
        }
        dim = dimensions.get(aspect_ratio, dimensions["9:16"])

        payload = {
            "video_inputs": [
                {
                    "character": {
                        "type": "avatar",
                        "avatar_id": self.avatar_id,
                        "avatar_style": "normal",
                    },
                    "voice": {
                        "type": "text",
                        "input_text": text,
                        "voice_id": voice_id or "en-US-JennyNeural",
                    },
                    "background": {
                        "type": "color",
                        "value": "#00FF00",  # green screen for chroma key
                    },
                }
            ],
            "dimension": dim,
        }

        async with httpx.AsyncClient(timeout=600) as client:
            response = await client.post(
                f"{self.BASE_URL}/v2/video/generate",
                json=payload,
                headers=self.headers,
            )
            response.raise_for_status()
            data = response.json()
            video_id = data["data"]["video_id"]

            video_url = await self._poll_video_status(client, video_id)
            return await self._download_video(client, video_url, output_path)

    async def list_avatars(self) -> list[dict]:
        """List available avatars from your HeyGen account."""
        async with httpx.AsyncClient(timeout=30) as client:
            response = await client.get(
                f"{self.BASE_URL}/v2/avatars",
                headers=self.headers,
            )
            response.raise_for_status()
            data = response.json()
            return [
                {
                    "avatar_id": a["avatar_id"],
                    "avatar_name": a.get("avatar_name", ""),
                    "gender": a.get("gender", ""),
                }
                for a in data.get("data", {}).get("avatars", [])
            ]

    async def _poll_video_status(
        self, client: httpx.AsyncClient, video_id: str, max_wait: int = 600
    ) -> str:
        """Poll HeyGen API until video is ready.

        Returns:
            URL of the completed video
        """
        elapsed = 0
        interval = 10  # check every 10 seconds

        while elapsed < max_wait:
            response = await client.get(
                f"{self.BASE_URL}/v1/video_status.get",
                params={"video_id": video_id},
                headers=self.headers,
            )
            response.raise_for_status()
            data = response.json()

            status = data["data"]["status"]
            if status == "completed":
                return data["data"]["video_url"]
            elif status == "failed":
                error = data["data"].get("error", "Unknown error")
                raise RuntimeError(f"Avatar video generation failed: {error}")

            await asyncio.sleep(interval)
            elapsed += interval

        raise TimeoutError(f"Avatar video generation timed out after {max_wait}s")

    async def _download_video(
        self, client: httpx.AsyncClient, url: str, output_path: str
    ) -> Path:
        """Download video from URL to local path."""
        response = await client.get(url)
        response.raise_for_status()

        output = Path(output_path)
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_bytes(response.content)

        return output
