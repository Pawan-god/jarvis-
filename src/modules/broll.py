"""AI B-Roll video generation module using Runway Gen-4 Turbo API."""

import asyncio
import os
from pathlib import Path

import httpx


class BRollGenerator:
    """Generates cinematic b-roll video clips using Runway ML API."""

    BASE_URL = "https://api.dev.runwayml.com/v1"

    def __init__(self):
        self.api_key = os.getenv("RUNWAY_API_KEY")
        if not self.api_key:
            raise ValueError("RUNWAY_API_KEY environment variable is required")

        self.headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
            "X-Runway-Version": "2024-11-06",
        }

    async def generate_clip(
        self,
        prompt: str,
        output_path: str,
        duration: int = 5,
        aspect_ratio: str = "9:16",
        model: str = "gen4_turbo",
    ) -> Path:
        """Generate a single b-roll video clip from a text prompt.

        Args:
            prompt: Cinematic description of the video to generate
            output_path: Where to save the video clip
            duration: Clip duration in seconds (5 or 10)
            aspect_ratio: Aspect ratio ("9:16", "16:9", "1:1")
            model: Runway model to use

        Returns:
            Path to the downloaded video clip
        """
        payload = {
            "promptText": prompt,
            "model": model,
            "duration": duration,
            "ratio": aspect_ratio.replace(":", ":"),
            "watermark": False,
        }

        async with httpx.AsyncClient(timeout=300) as client:
            # Submit generation task
            response = await client.post(
                f"{self.BASE_URL}/image_to_video",  # Runway uses this endpoint for text-to-video too
                json=payload,
                headers=self.headers,
            )
            response.raise_for_status()
            task_id = response.json()["id"]

            # Poll for completion
            video_url = await self._poll_task(client, task_id)

            # Download
            return await self._download_clip(client, video_url, output_path)

    async def generate_clips_batch(
        self,
        prompts: list[str],
        output_dir: str,
        duration: int = 5,
        aspect_ratio: str = "9:16",
        max_concurrent: int = 3,
    ) -> list[Path]:
        """Generate multiple b-roll clips concurrently.

        Args:
            prompts: List of cinematic prompts
            output_dir: Directory to save clips
            duration: Duration per clip
            aspect_ratio: Aspect ratio for all clips
            max_concurrent: Max simultaneous generations (to avoid rate limits)

        Returns:
            List of paths to generated clips
        """
        semaphore = asyncio.Semaphore(max_concurrent)
        output_dir_path = Path(output_dir)
        output_dir_path.mkdir(parents=True, exist_ok=True)

        async def _generate_one(idx: int, prompt: str) -> Path:
            async with semaphore:
                output_path = str(output_dir_path / f"broll_{idx:03d}.mp4")
                return await self.generate_clip(
                    prompt=prompt,
                    output_path=output_path,
                    duration=duration,
                    aspect_ratio=aspect_ratio,
                )

        tasks = [_generate_one(i, p) for i, p in enumerate(prompts)]
        results = await asyncio.gather(*tasks, return_exceptions=True)

        paths = []
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                print(f"[WARNING] B-roll clip {i} failed: {result}")
            else:
                paths.append(result)

        return paths

    async def _poll_task(
        self, client: httpx.AsyncClient, task_id: str, max_wait: int = 300
    ) -> str:
        """Poll Runway API until generation is complete."""
        elapsed = 0
        interval = 5

        while elapsed < max_wait:
            response = await client.get(
                f"{self.BASE_URL}/tasks/{task_id}",
                headers=self.headers,
            )
            response.raise_for_status()
            data = response.json()

            status = data.get("status")
            if status == "SUCCEEDED":
                output = data.get("output", [])
                if output:
                    return output[0]  # URL of generated video
                raise RuntimeError("Task succeeded but no output URL found")
            elif status in ("FAILED", "CANCELLED"):
                failure = data.get("failure", "Unknown error")
                raise RuntimeError(f"Runway generation failed: {failure}")

            await asyncio.sleep(interval)
            elapsed += interval

        raise TimeoutError(f"Runway generation timed out after {max_wait}s")

    async def _download_clip(
        self, client: httpx.AsyncClient, url: str, output_path: str
    ) -> Path:
        """Download clip from URL."""
        response = await client.get(url)
        response.raise_for_status()

        output = Path(output_path)
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_bytes(response.content)

        return output
