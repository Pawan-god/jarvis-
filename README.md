# Jarvis — AI Avatar Video Pipeline

Automated pipeline to generate Instagram Reels / TikTok / YouTube Shorts with an AI talking avatar overlaid on AI-generated b-roll video.

## What It Does

Given a **topic**, the pipeline:

1. **Generates a script** with hook + segments + b-roll prompts (Claude / GPT)
2. **Creates voiceover** with word-level timestamps for captions (ElevenLabs)
3. **Generates AI avatar** video lip-synced to the audio (HeyGen)
4. **Generates cinematic b-roll** clips from prompts (Runway Gen-4 Turbo)
5. **Composes the final video** — avatar PiP on b-roll, animated captions, music (Remotion)

Steps 3 and 4 run **in parallel** to minimize total generation time.

## Architecture

```
Topic → Script (LLM) → Audio (ElevenLabs TTS)
                              ↓                    ↓
                        HeyGen Avatar        Runway B-Roll
                        (parallel)           (parallel)
                              ↓                    ↓
                        Remotion Composition
                        (avatar PiP + captions + music)
                              ↓
                        Final MP4 (1080x1920, 9:16)
```

## Tech Stack

| Component | Provider | Purpose |
|-----------|----------|---------|
| Script Gen | Claude / GPT | Generate video scripts + b-roll prompts |
| TTS | ElevenLabs | Voiceover with word-level timestamps |
| Avatar | HeyGen API | Lip-synced talking avatar video |
| B-Roll | Runway Gen-4 Turbo | Cinematic AI-generated video clips |
| Composition | Remotion | Final video compositing with overlays |

## Quick Start

### 1. Install Dependencies

```bash
# Python dependencies
pip install -r requirements.txt

# Remotion (Node.js)
cd remotion && npm install && cd ..
```

### 2. Set Up API Keys

```bash
cp .env.example .env
# Edit .env with your API keys
```

### 3. Generate a Video

```bash
python main.py --topic "How AI is changing healthcare"

# With options:
python main.py \
  --topic "5 Python tricks you didn't know" \
  --duration 45 \
  --style entertaining \
  --output my_reel.mp4
```

## Configuration

Edit `config.yaml` to customize:

- **Video**: resolution, FPS, target duration
- **Avatar**: position, size, provider settings
- **B-Roll**: clip duration, resolution, model
- **TTS**: voice stability, style settings
- **Composition**: caption style, music volume, transitions

## Project Structure

```
jarvis-/
├── main.py                 # CLI entry point
├── config.yaml             # Pipeline configuration
├── requirements.txt        # Python dependencies
├── .env.example            # API key template
├── src/
│   ├── pipeline.py         # Main orchestrator
│   ├── modules/
│   │   ├── script_generator.py  # LLM script generation
│   │   ├── tts.py               # ElevenLabs TTS
│   │   ├── avatar.py            # HeyGen avatar generation
│   │   ├── broll.py             # Runway b-roll generation
│   │   └── composer.py          # Remotion video composition
│   └── utils/
│       └── file_server.py       # Local HTTP server for API access
├── remotion/
│   ├── package.json
│   ├── src/
│   │   ├── index.ts
│   │   ├── Root.tsx
│   │   └── components/
│   │       ├── AvatarReelComposition.tsx  # Main composition
│   │       └── AnimatedCaptions.tsx       # TikTok-style captions
│   └── public/
└── output/                 # Generated videos
```

## API Costs (Estimated per 60s Reel)

| Service | Cost |
|---------|------|
| Claude/GPT (script) | ~$0.01 |
| ElevenLabs (TTS) | ~$0.05 |
| HeyGen (avatar) | ~$0.50 (1 credit) |
| Runway (6 b-roll clips) | ~$1.50 |
| **Total** | **~$2-4** |

## Content Styles

- `educational` — Informative, fact-driven content
- `entertaining` — Fun, trend-driven, meme-aware
- `motivational` — Inspiring, quote-heavy
- `news` — Breaking news, current events
- `storytelling` — Narrative-driven, emotional arcs

## License

MIT
