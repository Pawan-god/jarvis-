#!/usr/bin/env python3
"""AI Avatar Video Pipeline — Generate Instagram Reels with AI avatars and b-roll.

Usage:
    python main.py --topic "How AI is changing healthcare"
    python main.py --topic "5 Python tricks you didn't know" --duration 45 --style entertaining
    python main.py --topic "The future of space travel" --duration 90 --style motivational
"""

import asyncio

import click
from dotenv import load_dotenv

load_dotenv()


@click.command()
@click.option("--topic", required=True, help="Video topic or idea")
@click.option("--duration", default=60, help="Target video duration in seconds (default: 60)")
@click.option("--style", default="educational", type=click.Choice([
    "educational", "entertaining", "motivational", "news", "storytelling"
]), help="Content style")
@click.option("--config", default="config.yaml", help="Path to config file")
@click.option("--output", default=None, help="Output filename (auto-generated if not set)")
def main(topic: str, duration: int, style: str, config: str, output: str):
    """Generate an AI avatar video reel from a topic."""
    from src.pipeline import Pipeline, load_config

    cfg = load_config(config)
    pipeline = Pipeline(config=cfg)

    result = asyncio.run(pipeline.run(
        topic=topic,
        duration=duration,
        style=style,
        output_name=output,
    ))

    click.echo(f"\nDone! Video saved to: {result}")


if __name__ == "__main__":
    main()
