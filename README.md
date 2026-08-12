# AutoClip Local

[![Python](https://img.shields.io/badge/python-3.11%2B-blue)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.115+-green)](https://fastapi.tiangolo.com/)
[![React](https://img.shields.io/badge/React-18.3-cyan)](https://react.dev/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

> 🎬 AI-powered local video clipper that transforms long-form videos into viral-worthy vertical clips.

## Features

- **YouTube & Local Video Ingestion** — accept URLs or direct uploads
- **Whisper Word-level Transcription** — precise timestamps for accurate cutting
- **Ollama LLM Highlight Detection** — find the most engaging moments
- **Auto 9:16 Rendering** — vertical output with automatic subtitles
- **Non-blocking B-roll Overlay** — Pexels integration with graceful fallback
- **Full Offline Operation** — runs entirely on-premise, no cloud dependency

## Tech Stack

| Layer | Technology |
|-------|-----------|
| Backend | FastAPI, SQLAlchemy 2.0, Alembic |
| AI | OpenAI Whisper, Ollama (LLaMA 3.1) |
| Frontend | React, TypeScript, TailwindCSS, Zustand |
| Database | SQLite (async) |
| Media | FFmpeg, MoviePy |

## Quick Start

```bash
git clone https://github.com/rainovrh/autoclip-local.git
cd autoclip-local

# Backend
cd backend
python -m venv venv
source venv/Scripts/activate  # Windows
pip install -r requirements-web.txt
uvicorn app.main:app --reload

# Frontend
cd ../frontend
pnpm install
pnpm dev
```

## Architecture

```
┌─────────────┐     ┌──────────────┐     ┌─────────────┐
│   React     │────▶│   FastAPI    │────▶│  SQLite     │
│  Frontend   │◀────│   Backend    │◀────│  Database   │
└─────────────┘     └──────────────┘     └─────────────┘
                            │
                            ▼
                   ┌────────────────┐
                   │  AI Pipeline   │
                   │ Whisper+Ollama │
                   └────────────────┘
```

## Roadmap

- [x] Database schema & API scaffolding
- [x] Health check & project endpoints
- [ ] YouTube & local video upload
- [ ] Whisper transcription pipeline
- [ ] LLM highlight analysis
- [ ] FFmpeg rendering engine
- [ ] Frontend dashboard
- [ ] B-roll overlay system
- [ ] Subtitle style editor

## License

MIT — see [LICENSE](LICENSE)
