"""Script generation module using Claude or GPT to create video scripts with b-roll prompts."""

import json
import os

from pydantic import BaseModel


class SceneSegment(BaseModel):
    """A single segment of the video script."""
    narration: str
    broll_prompt: str
    duration_hint: float  # estimated seconds for this segment


class VideoScript(BaseModel):
    """Complete video script with narration segments and b-roll prompts."""
    title: str
    hook: str  # opening hook line
    segments: list[SceneSegment]
    total_duration: float


SCRIPT_SYSTEM_PROMPT = """You are an expert short-form video scriptwriter for Instagram Reels, TikTok, and YouTube Shorts.

Your job is to create engaging, punchy scripts that:
- Start with a strong hook (first 2-3 seconds are critical)
- Use conversational, energetic tone
- Include natural pauses and emphasis
- Are optimized for 30-90 second videos
- Drive engagement (likes, comments, shares)

For each script, you must also generate b-roll video prompts — these are text descriptions
of cinematic AI-generated video clips that will play BEHIND the talking avatar.

Output your response as valid JSON matching this exact structure:
{
  "title": "Short title for the video",
  "hook": "The opening hook line that grabs attention",
  "segments": [
    {
      "narration": "What the avatar says in this segment",
      "broll_prompt": "Cinematic description for AI video generation. Be specific about camera angles, lighting, movement. Example: 'Aerial drone shot of a futuristic city at sunset, neon lights reflecting off glass buildings, cinematic lighting, slow pan'",
      "duration_hint": 5.0
    }
  ],
  "total_duration": 60.0
}

Rules for b-roll prompts:
- Each prompt should be 1-2 sentences describing a visually stunning scene
- Use cinematic language: "slow motion", "aerial shot", "close-up", "golden hour", etc.
- The b-roll should visually complement what the avatar is saying
- Avoid text or UI elements in b-roll prompts — these will be added in post
- Aim for 5-10 second clips per segment"""


class ScriptGenerator:
    """Generates video scripts with b-roll prompts using LLMs."""

    def __init__(self, provider: str = None, model: str = None):
        self.provider = provider or os.getenv("LLM_PROVIDER", "anthropic")
        self.model = model

        if self.provider == "anthropic":
            import anthropic
            self.client = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))
            self.model = self.model or os.getenv("LLM_MODEL", "claude-sonnet-4-6")
        elif self.provider == "openai":
            import openai
            self.client = openai.OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
            self.model = self.model or os.getenv("LLM_MODEL", "gpt-4o")
        else:
            raise ValueError(f"Unsupported LLM provider: {self.provider}")

    async def generate(self, topic: str, duration: int = 60, style: str = "educational") -> VideoScript:
        """Generate a video script for the given topic.

        Args:
            topic: The subject/topic for the video
            duration: Target video duration in seconds
            style: Content style (educational, entertaining, motivational, news)

        Returns:
            VideoScript with narration segments and b-roll prompts
        """
        user_prompt = (
            f"Create a {duration}-second short-form video script about: {topic}\n\n"
            f"Style: {style}\n"
            f"Target duration: {duration} seconds\n"
            f"Number of segments: {max(3, duration // 10)}\n\n"
            "Remember: Start with a killer hook. Make every word count. "
            "The b-roll prompts should describe visually stunning, cinematic scenes."
        )

        if self.provider == "anthropic":
            response = self.client.messages.create(
                model=self.model,
                max_tokens=2000,
                system=SCRIPT_SYSTEM_PROMPT,
                messages=[{"role": "user", "content": user_prompt}],
            )
            raw_text = response.content[0].text
        else:
            response = self.client.chat.completions.create(
                model=self.model,
                max_tokens=2000,
                messages=[
                    {"role": "system", "content": SCRIPT_SYSTEM_PROMPT},
                    {"role": "user", "content": user_prompt},
                ],
                response_format={"type": "json_object"},
            )
            raw_text = response.choices[0].message.content

        # Parse JSON from response
        try:
            # Handle potential markdown code blocks in response
            if "```json" in raw_text:
                raw_text = raw_text.split("```json")[1].split("```")[0]
            elif "```" in raw_text:
                raw_text = raw_text.split("```")[1].split("```")[0]

            data = json.loads(raw_text.strip())
            return VideoScript(**data)
        except (json.JSONDecodeError, KeyError) as e:
            raise ValueError(f"Failed to parse script from LLM response: {e}\nRaw: {raw_text[:500]}")
