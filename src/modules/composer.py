"""Video composition module — generates Remotion project and renders final video."""

import json
import os
import subprocess
from pathlib import Path


class VideoComposer:
    """Composes final video by orchestrating Remotion rendering.

    Takes avatar video, b-roll clips, audio, and captions data,
    writes them into the Remotion project's input props, and triggers a render.
    """

    def __init__(self, remotion_dir: str = None):
        self.remotion_dir = Path(remotion_dir or os.path.join(os.path.dirname(__file__), "../../remotion"))

    def compose(
        self,
        avatar_video: str,
        broll_clips: list[str],
        audio_path: str,
        captions: list[dict] | None = None,
        output_path: str = "output/final.mp4",
        music_path: str | None = None,
        config: dict | None = None,
    ) -> Path:
        """Compose the final video from all assets.

        Args:
            avatar_video: Path to the avatar video (green screen)
            broll_clips: List of paths to b-roll video clips
            audio_path: Path to the narration audio
            captions: Word-level timestamps for animated captions
            output_path: Where to save the final rendered video
            music_path: Optional background music track
            config: Video configuration overrides

        Returns:
            Path to the final rendered video
        """
        cfg = {
            "width": 1080,
            "height": 1920,
            "fps": 30,
            "avatarPosition": "bottom-center",
            "avatarSizeRatio": 0.35,
            "captionStyle": "word-by-word",
            "musicVolume": 0.15,
            "transitionType": "crossfade",
            "transitionDuration": 0.5,
            **(config or {}),
        }

        # Build input props for Remotion
        props = {
            "avatarVideo": os.path.abspath(avatar_video),
            "brollClips": [os.path.abspath(c) for c in broll_clips],
            "audioPath": os.path.abspath(audio_path),
            "captions": captions or [],
            "musicPath": os.path.abspath(music_path) if music_path else None,
            "config": cfg,
        }

        # Write props to Remotion project
        props_path = self.remotion_dir / "public" / "input-props.json"
        props_path.parent.mkdir(parents=True, exist_ok=True)
        props_path.write_text(json.dumps(props, indent=2))

        # Render with Remotion CLI
        output = Path(output_path)
        output.parent.mkdir(parents=True, exist_ok=True)

        render_cmd = [
            "npx", "remotion", "render",
            "src/index.ts",
            "AvatarReelComposition",
            str(output.absolute()),
            "--props", str(props_path.absolute()),
            "--codec", "h264",
            "--image-format", "jpeg",
            "--log", "warn",
        ]

        result = subprocess.run(
            render_cmd,
            cwd=str(self.remotion_dir),
            capture_output=True,
            text=True,
            timeout=600,
        )

        if result.returncode != 0:
            raise RuntimeError(
                f"Remotion render failed (exit {result.returncode}):\n"
                f"stdout: {result.stdout[-500:]}\n"
                f"stderr: {result.stderr[-500:]}"
            )

        return output
