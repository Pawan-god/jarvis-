"""Main orchestrator pipeline — ties all modules together into a single flow.

Usage:
    python -m src.pipeline --topic "How AI is changing healthcare" --duration 60
"""

import asyncio
import os
import time
from pathlib import Path

import yaml
from rich.console import Console
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn

from .modules.script_generator import ScriptGenerator, VideoScript
from .modules.tts import TTSGenerator
from .modules.avatar import AvatarGenerator
from .modules.broll import BRollGenerator
from .modules.composer import VideoComposer
from .utils.file_server import LocalFileServer

console = Console()


def load_config(config_path: str = "config.yaml") -> dict:
    """Load pipeline configuration from YAML file."""
    path = Path(config_path)
    if path.exists():
        with open(path) as f:
            return yaml.safe_load(f)
    return {}


class Pipeline:
    """End-to-end AI avatar video generation pipeline.

    Flow:
        1. Generate script + b-roll prompts from topic (LLM)
        2. Generate voiceover audio (ElevenLabs TTS)
        3. Generate avatar video from audio (HeyGen) — runs in parallel with:
        4. Generate b-roll clips from prompts (Runway Gen-4 Turbo)
        5. Compose final video (Remotion): avatar PiP on b-roll + captions + music
    """

    def __init__(self, config: dict = None):
        self.config = config or load_config()
        self.output_dir = Path("output")
        self.output_dir.mkdir(parents=True, exist_ok=True)

    async def run(
        self,
        topic: str,
        duration: int = 60,
        style: str = "educational",
        output_name: str = None,
    ) -> Path:
        """Run the full pipeline to generate a video.

        Args:
            topic: Video topic/idea
            duration: Target duration in seconds
            style: Content style
            output_name: Output filename (auto-generated if None)

        Returns:
            Path to the final rendered video
        """
        run_id = f"{int(time.time())}"
        run_dir = self.output_dir / run_id
        run_dir.mkdir(parents=True, exist_ok=True)

        console.print(Panel(
            f"[bold cyan]AI Avatar Video Pipeline[/bold cyan]\n"
            f"Topic: {topic}\n"
            f"Duration: {duration}s | Style: {style}",
            title="Starting Pipeline",
        ))

        # ──────────────────────────────────────────────
        # Step 1: Generate Script
        # ──────────────────────────────────────────────
        console.print("\n[bold]Step 1/5:[/bold] Generating script...", style="yellow")
        script_gen = ScriptGenerator(
            provider=self.config.get("script", {}).get("provider"),
        )
        script = await script_gen.generate(topic=topic, duration=duration, style=style)
        console.print(f"  Script: [green]{script.title}[/green]")
        console.print(f"  Hook: \"{script.hook}\"")
        console.print(f"  Segments: {len(script.segments)}")

        # Save script for reference
        import json
        (run_dir / "script.json").write_text(json.dumps(script.model_dump(), indent=2))

        # ──────────────────────────────────────────────
        # Step 2: Generate Voiceover Audio
        # ──────────────────────────────────────────────
        console.print("\n[bold]Step 2/5:[/bold] Generating voiceover...", style="yellow")
        tts = TTSGenerator(
            voice_id=self.config.get("tts", {}).get("voice_id"),
            model=self.config.get("tts", {}).get("model"),
        )

        full_narration = " ".join(seg.narration for seg in script.segments)
        tts_result = await tts.generate_with_timestamps(
            text=full_narration,
            output_path=str(run_dir / "narration.mp3"),
            stability=self.config.get("tts", {}).get("stability", 0.5),
            similarity_boost=self.config.get("tts", {}).get("similarity_boost", 0.75),
        )
        audio_path = tts_result["audio_path"]
        captions = self._parse_captions(tts_result.get("alignment", {}))
        console.print(f"  Audio saved: [green]{audio_path}[/green]")
        console.print(f"  Caption words: {len(captions)}")

        # ──────────────────────────────────────────────
        # Step 3 & 4: Avatar + B-Roll (in parallel)
        # ──────────────────────────────────────────────
        console.print("\n[bold]Step 3/5:[/bold] Generating avatar video...", style="yellow")
        console.print("[bold]Step 4/5:[/bold] Generating b-roll clips (parallel)...", style="yellow")

        # Start local file server so HeyGen can access our audio
        file_server = LocalFileServer(directory=str(run_dir))
        base_url = file_server.start()
        audio_url = file_server.get_url(audio_path)

        avatar_gen = AvatarGenerator(
            avatar_id=self.config.get("avatar", {}).get("avatar_id"),
        )
        broll_gen = BRollGenerator()

        broll_prompts = [seg.broll_prompt for seg in script.segments]

        # Run avatar and b-roll generation in parallel
        avatar_task = avatar_gen.generate_from_audio(
            audio_url=audio_url,
            output_path=str(run_dir / "avatar.mp4"),
            aspect_ratio="9:16",
        )
        broll_task = broll_gen.generate_clips_batch(
            prompts=broll_prompts,
            output_dir=str(run_dir / "broll"),
            duration=self.config.get("broll", {}).get("clip_duration", 5),
            aspect_ratio="9:16",
        )

        avatar_path, broll_paths = await asyncio.gather(avatar_task, broll_task)
        file_server.stop()

        console.print(f"  Avatar: [green]{avatar_path}[/green]")
        console.print(f"  B-roll clips: [green]{len(broll_paths)} generated[/green]")

        # ──────────────────────────────────────────────
        # Step 5: Compose Final Video
        # ──────────────────────────────────────────────
        console.print("\n[bold]Step 5/5:[/bold] Composing final video...", style="yellow")
        composer = VideoComposer()

        output_filename = output_name or f"reel_{run_id}.mp4"
        final_path = composer.compose(
            avatar_video=str(avatar_path),
            broll_clips=[str(p) for p in broll_paths],
            audio_path=audio_path,
            captions=captions,
            output_path=str(self.output_dir / output_filename),
            config={
                "avatarPosition": self.config.get("composition", {}).get("avatar_position", "bottom-center"),
                "avatarSizeRatio": self.config.get("avatar", {}).get("size_ratio", 0.35),
                "captionStyle": self.config.get("composition", {}).get("caption_style", "word-by-word"),
                "musicVolume": self.config.get("composition", {}).get("music_volume", 0.15),
            },
        )

        console.print(Panel(
            f"[bold green]Video generated successfully![/bold green]\n"
            f"Output: {final_path}\n"
            f"Run ID: {run_id}",
            title="Pipeline Complete",
        ))

        return final_path

    def _parse_captions(self, alignment: dict) -> list[dict]:
        """Parse ElevenLabs alignment data into caption format.

        ElevenLabs returns:
        {
            "characters": ["H", "e", "l", "l", "o", ...],
            "character_start_times_seconds": [0.0, 0.1, ...],
            "character_end_times_seconds": [0.1, 0.2, ...],
        }

        We convert this to word-level timestamps.
        """
        if not alignment:
            return []

        chars = alignment.get("characters", [])
        starts = alignment.get("character_start_times_seconds", [])
        ends = alignment.get("character_end_times_seconds", [])

        if not chars or len(chars) != len(starts) or len(chars) != len(ends):
            return []

        words = []
        current_word = ""
        word_start = 0.0

        for i, char in enumerate(chars):
            if char == " " and current_word:
                words.append({
                    "word": current_word,
                    "start": word_start,
                    "end": ends[i - 1] if i > 0 else 0.0,
                })
                current_word = ""
            elif char != " ":
                if not current_word:
                    word_start = starts[i]
                current_word += char

        # Don't forget the last word
        if current_word:
            words.append({
                "word": current_word,
                "start": word_start,
                "end": ends[-1] if ends else 0.0,
            })

        return words
