# Tab-It

A web app that lets users upload songs and get easy-to-read guitar tab. Built on libraries and models from Meta Research and Spotify's Audio Intelligence Lab, the pipeline picks out the guitar from multi-track songs, processes the audio into musical notes, intelligently places them on the guitar neck, and displays the result as readable tab.

## Table of Contents

- [Inspiration](#inspiration)
- [How It's Built](#how-its-built)
- [What's Next](#whats-next)
- [Architecture](#architecture)
- [Tab JSON Format](#tab-json-format)
- [Getting Started](#getting-started)
  - [Prerequisites](#prerequisites)
  - [Development](#development)
  - [Production](#production)
  - [Compose File Structure](#compose-file-structure)
  - [Docker Compose Usage](#docker-compose-usage)
  - [Docker Build Best Practices](#docker-build-best-practices)
- [Running without Docker](#running-without-docker)
- [Updating Dependencies](#updating-dependencies)
- [Screenshots](#screenshots)

## Inspiration

What inspired us to create Tab-it is our mutual interest in playing guitar. We realized that learning songs by ear is incredibly difficult for beginners, and finding accurate tabs for niche or new songs is often impossible. We wanted to build a tool that could listen to any song and give us a starting point to learn it immediately.

## How It's Built

**The Backend:** We used Python for the heavy lifting. We utilized Meta's audio-separator library (powered by the Demucs model) to perform high-quality stem separation, which is then converted to MIDI by Basic Pitch from Spotify's Audio Intelligence Lab, then using the computer-aided musicology library music21 we transform this into well-organized musical notes, which are then run through a custom fretting algorithm to place the notes on the guitar neck. This pipeline was connected via Flask endpoints (one for audio separation, and one for the rest of the pipeline and file uploading from the frontend).

**The Frontend:** Built with React and TypeScript. We used a component-based architecture to handle the file upload and tab display. The frontend receives a JSON object from the backend containing every note in the song, our React script maps those into a 6-string grid, and renders it as a clean text block. This lets the user visually see what string and fret to play.

## What's Next

Tab-it works. We developed a complete, modular pipeline that takes in songs and provides guitar tab you can read and play along to. Since this project is of personal interest to us both, we intend to continue working on it. While the pipeline outputs readable tabs, along the way notes can be dropped, added or shifted. With some model tweaking, fine-tuning, and potentially employing custom algorithms, we think this could be mitigated — allowing for very easy playing.

There are many factors to consider when placing notes onto the fretboard efficiently, and identifying chord patterns, hand shapes, and positions are all key to producing helpful tab. This is a very large area to be explored, and is a pretty pivotal part of our product, so more research and development will be put into this.

We intend to add database storage to allow the storage and retrieval of tabs, so users can build a library, and share their tabs with others. Other integrations could also be added, such as allowing users to record their own playing for feedback, or to get the tabs for their improvisations and solos. Re-examining the scalability, cost, and hosting of the product is also on the roadmap.

## Architecture

| Service | Tech | Description |
|---|---|---|
| **frontend** | React + TypeScript (Vite) | File upload UI and tab renderer |
| **backend** | Python / Flask | Audio-to-tab pipeline (Basic Pitch, music21, custom fretting) |
| **auto-separator** | Python / Flask + Demucs | Isolates the guitar stem from a full mix |

## Tab JSON Format

The backend returns a JSON object describing the fretting for the entire song. The frontend consumes this to render tab:

```json
{
  "notes": [
    {
      "duration": 0.5,
      "strings": [2, 3],
      "frets": [5, 7],
      "time": 0.0
    },
    {
      "duration": 0.25,
      "strings": [1],
      "frets": [3],
      "time": 0.5
    }
  ]
}
```

| Field | Type | Description |
|---|---|---|
| `duration` | `number` | How long the note/chord rings (in beats) |
| `strings` | `number[]` | Which guitar strings are played (1 = high e, 6 = low E) |
| `frets` | `number[]` | Corresponding fret for each string |
| `time` | `number` | When the note/chord starts (in beats) |

Each entry in `notes` represents a single moment — if multiple strings are played at the same time they share one entry with parallel `strings` and `frets` arrays.

## Getting Started

### Prerequisites

- [Docker & Docker Compose](https://docs.docker.com/get-docker/)
- [Node.js 20+](https://nodejs.org/) (for local frontend dev)

### Development

The two Python services run in Docker; the frontend runs natively on the host for instant Hot Module Replacement (HMR).

```bash
# Start backends
docker compose -f compose.yaml -f compose.dev.yaml up --build

# Start frontend
cd frontend/tab-it-frontend
npm install
npm run dev
```

| URL | Service |
|---|---|
| `http://localhost:5173` | Frontend (Vite) |
| `http://localhost:5000` | Backend |
| `http://localhost:5001` | Auto-separator |

The backend services bind-mount local code into their container, and Flask runs in debug mode. So you can save a file and it auto-reloads.

### Production

All three services run in Docker. The frontend is built and served via nginx.

```bash
docker compose -f compose.yaml -f compose.prod.yaml up --build
```

| URL | Service |
|---|---|
| `http://localhost:3000` | Frontend (nginx) |
| `http://localhost:5000` | Backend (gunicorn) |
| `http://localhost:5001` | Auto-separator (gunicorn) |

### Compose file structure

| File | Purpose |
|---|---|
| `compose.yaml` | Base config shared by dev and prod (build contexts, env vars, service dependencies) |
| `compose.dev.yaml` | Dev overrides — volume mounts, Flask debug mode, dev server commands |
| `compose.prod.yaml` | Prod overrides — adds the frontend service, exposes ports, uses Dockerfile defaults (gunicorn / nginx) |

### Docker Compose usage

#### Rebuilding a single service

A full `--build` rebuilds every service. If you only changed one service's Dockerfile or dependencies, you can target just that service:

```bash
# Rebuild and restart only the backend
docker compose -f compose.yaml -f compose.dev.yaml up --build backend

# Rebuild and restart only the auto-separator
docker compose -f compose.yaml -f compose.dev.yaml up --build auto-separator
```

The other service(s) will keep running untouched.

#### Docker build best practices

Since the images may contain heavy ML libraries, to keep development fast when adding new dependencies, **install new packages live for quick testing.** Instead of rebuilding, install directly in the running container:

```bash
# Install into the running backend container
docker compose -f compose.yaml -f compose.dev.yaml exec backend pip install <package>

# Install into the running auto-separator container
docker compose -f compose.yaml -f compose.dev.yaml exec auto-separator pip install <package>
```

This is instant but temporary — the package disappears when the container is recreated. Once you're happy with it, add it to `requirements.txt` and do a proper `--build`.

**Rebuild only the service you changed.** If you updated `backend/requirements.txt`, run `up --build backend` instead of `up --build` so you don't rebuild the auto-separator for no reason (and vice versa).

## Running without Docker

If you want to run the services directly on your machine instead of Docker:

### Backend (`/backend`)

```bash
pip install -r backend/requirements.txt
cd backend
python app.py
```

### Auto-separator (`/auto-seperator`)

```bash
# PyTorch must be installed first from the official CPU index
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cpu

# FFmpeg is required (restart your terminal after install)
winget install Gyan.FFmpeg

pip install -r auto-seperator/requirements.txt
cd auto-seperator
python audio_splitter.py
```

### Frontend (`/frontend/tab-it-frontend`)

```bash
cd frontend/tab-it-frontend
npm install
npm run dev
```

## Updating Dependencies

### Python (backend / auto-separator)

After adding or upgrading a package, freeze the new state into `requirements.txt`:

```bash
pip install some-new-package
pip freeze > requirements.txt
```

If you're using Docker, rebuild the images so the container picks up the changes:

```bash
docker compose -f compose.yaml -f compose.dev.yaml up --build
```

### Frontend

```bash
cd frontend/tab-it-frontend
npm install some-new-package
```

`package-lock.json` updates automatically. If you're running the prod compose, rebuild to pick up the change:

```bash
docker compose -f compose.yaml -f compose.prod.yaml up --build
```

## Screenshots

<img width="700" alt="dashboard" src="https://github.com/user-attachments/assets/5f404b83-9be6-4262-a7fa-10717e0b6288" />
<img width="700" alt="tab_display" src="https://github.com/user-attachments/assets/20e84c96-dd06-493d-83e0-978f503525ce" />
<img width="700" alt="tab_edit" src="https://github.com/user-attachments/assets/c10adc4e-44fb-4d82-9712-e3ed3faa857d" />
