# BYETZ

**Your Personal Clip Feed** — A native iOS app + Python backend that transforms your Plex media library into an intelligent, TikTok-style horizontal clip feed.

BYETZ automatically identifies and extracts the most memorable 15–30 second moments from your movies and TV shows, then serves them in an infinitely scrollable landscape feed that learns from your preferences over time.

---

## Architecture

BYETZ is a two-component system:

| Component | Technology | Purpose |
|-----------|-----------|---------|
| **iOS Client** | Swift 5.9 / SwiftUI | Feed UI, video playback, user interactions |
| **Backend API** | Python 3.12 / FastAPI | REST API, clip generation, recommendations |
| **Clip Engine** | Python / FFmpeg | Media analysis, scene detection, clip extraction |
| **Recommendation Engine** | Python | Personalized feed with collaborative filtering |
| **Database** | PostgreSQL 16 + pgvector | Clips, users, interactions, embeddings |
| **Task Queue** | Celery + Redis | Background clip processing |
| **Deployment** | Docker Compose | Single-command deployment alongside Plex |

---

## Prerequisites

- **Docker** and **Docker Compose** (for backend)
- **Xcode 15+** (for iOS app)
- **Plex Media Server** on your local network
- **FFmpeg 6.x** (included in Docker image)

---

## Quick Start

### 1. Clone the Repository

```bash
git clone https://github.com/benyetra/BYETZ.git
cd BYETZ
```

### 2. Start the Backend

```bash
# Copy and configure environment
cp backend/.env.example backend/.env
# Edit backend/.env with your settings (especially BYETZ_SECRET_KEY)

# Launch all services
docker compose up -d
```

This starts:
- **API server** on `http://localhost:8000`
- **Celery worker** for background clip processing
- **PostgreSQL** on port 5432
- **Redis** on port 6379

### 3. Verify the Backend

```bash
# Health check
curl http://localhost:8000/health

# API docs
open http://localhost:8000/docs
```

### 4. Build the iOS App

```bash
open ios/BYETZ/
# Open in Xcode, select your target device, and build (Cmd+R)
```

> **Note:** Update the `baseURL` in `ios/BYETZ/Services/APIClient.swift` to point to your backend server's IP address on your local network (e.g., `http://192.168.1.100:8000`).

---

## Backend Development (without Docker)

### Setup

```bash
cd backend
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### Run the API Server

```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### Run the Celery Worker

```bash
celery -A app.tasks.celery_app worker --loglevel=info --concurrency=2
```

### Run Tests

```bash
pytest tests/ -v
```

---

## Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `BYETZ_DATABASE_URL` | `postgresql+asyncpg://byetz:byetz@localhost:5432/byetz` | Async database connection |
| `BYETZ_DATABASE_URL_SYNC` | `postgresql://byetz:byetz@localhost:5432/byetz` | Sync database connection (Celery) |
| `BYETZ_REDIS_URL` | `redis://localhost:6379/0` | Redis connection for task queue |
| `BYETZ_CLIP_STORAGE_PATH` | `/data/clips` | Directory for extracted clip files |
| `BYETZ_SECRET_KEY` | `change-me-in-production` | JWT signing key (**change this!**) |
| `BYETZ_PLEX_CLIENT_ID` | `byetz-app` | Plex API client identifier |
| `BYETZ_PLEX_PRODUCT` | `BYETZ` | Plex API product name |

---

## API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/auth/plex` | Authenticate via Plex token |
| `GET` | `/feed?limit=10&offset=0` | Fetch personalized clip feed |
| `GET` | `/clips/{id}/stream` | Stream clip video file |
| `GET` | `/clips/{id}` | Get clip metadata |
| `POST` | `/interactions` | Submit like/dislike/save/skip |
| `GET` | `/profile` | User profile and stats |
| `GET` | `/profile/saved` | Saved clips library |
| `GET` | `/library/status` | Plex library processing status |
| `POST` | `/library/rescan` | Trigger library rescan |
| `PUT` | `/library/toggle` | Enable/disable a library |
| `GET` | `/settings` | Get user settings |
| `PUT` | `/settings` | Update user settings |
| `GET` | `/taste-profile/titles` | Get titles for onboarding |
| `POST` | `/taste-profile/select` | Submit taste profile selections |
| `GET` | `/health` | Health check |

Full interactive API documentation available at `/docs` when the server is running.

---

## How It Works

### Clip Generation Pipeline

1. **Library Scan** — Connects to your Plex server and discovers media
2. **Subtitle Extraction** — Pulls embedded subtitles via FFmpeg
3. **Quote Matching** — Cross-references dialogue against popular quote databases
4. **Scene Detection** — Identifies clean scene boundaries for clip start/end points
5. **Audio Analysis** — Detects dramatic peaks and music swells
6. **Clip Scoring** — Ranks candidates using a weighted composite score:

| Signal | Weight |
|--------|--------|
| Quote Match | 35% |
| Audio Energy | 20% |
| Scene Composition | 15% |
| Dialogue Density | 15% |
| Temporal Position | 10% |

7. **Extraction** — Top clips extracted as H.264/AAC MP4 with audio normalization (-16 LUFS) and fade-in/out

### Recommendation Engine

- **Cold Start**: Seeded from taste profile selections + genre affinity
- **Personalization**: Learns from likes (+1.0), dislikes (-1.0), saves (+1.5), and watch completion (+0.5)
- **Feed Rules**: No 3+ consecutive clips from same title, max 40% genre ratio, 20% exploration rate
- **Decay**: Cold start weight decays over first 50 interactions

---

## iOS App Screens

| Screen | Description |
|--------|-------------|
| **Splash** | BYETZ logo with connection status |
| **Plex Auth** | Token-based Plex authentication |
| **Taste Profile** | Select 10+ titles to seed recommendations |
| **Feed** | Full-screen landscape clip feed with swipe navigation |
| **Profile** | Stats, saved clips grid |
| **Library** | Library management with processing progress |
| **Settings** | Preferences, quality, notifications |

### Gestures

| Gesture | Action |
|---------|--------|
| Swipe Up | Next clip |
| Swipe Down | Previous clip |
| Tap Center | Pause/resume |
| Swipe Left | Open clip info panel |
| Tap Like/Dislike/Save | Record interaction (with haptic) |

---

## Project Structure

```
BYETZ/
├── backend/
│   ├── app/
│   │   ├── main.py              # FastAPI application
│   │   ├── config.py            # Pydantic settings
│   │   ├── database.py          # SQLAlchemy async setup
│   │   ├── models/              # Database models
│   │   │   ├── user.py          # User, UserEmbedding, TasteSelection, UserSettings
│   │   │   ├── clip.py          # Clip, MediaItem, PlexLibrary
│   │   │   └── interaction.py   # Interaction model
│   │   ├── schemas/             # Pydantic request/response schemas
│   │   ├── routers/             # API route handlers
│   │   ├── services/            # Business logic
│   │   │   ├── auth.py          # JWT authentication
│   │   │   ├── plex.py          # Plex API integration
│   │   │   ├── clip_engine.py   # FFmpeg clip extraction
│   │   │   ├── scoring.py       # Clip quality scoring
│   │   │   ├── recommendation.py # Feed personalization
│   │   │   ├── interaction.py   # User engagement processing
│   │   │   ├── profile.py       # User profile management
│   │   │   ├── library.py       # Plex library management
│   │   │   └── taste_profile.py # Onboarding taste setup
│   │   └── tasks/               # Celery background tasks
│   │       ├── celery_app.py    # Celery configuration
│   │       └── clip_processing.py # Media processing tasks
│   ├── tests/                   # Test suite (36 tests)
│   ├── Dockerfile
│   └── requirements.txt
├── ios/
│   └── BYETZ/
│       ├── BYETZApp.swift        # App entry point
│       ├── ContentView.swift     # Root navigation
│       ├── Models/               # Data models (Clip, User, Interaction, Library)
│       ├── Views/                # SwiftUI views
│       │   ├── MainTabView.swift
│       │   ├── Onboarding/       # PlexAuthView, TasteProfileView
│       │   ├── Feed/             # FeedView, VideoPlayerView
│       │   ├── Profile/          # ProfileView
│       │   ├── Library/          # LibraryManagerView
│       │   └── Settings/         # SettingsView
│       ├── ViewModels/           # MVVM view models
│       ├── Services/             # APIClient, KeychainService, AuthManager
│       └── Utilities/            # HapticManager, OrientationManager
├── docker-compose.yml
└── BYETZ-PRD-v1.0.md
```

---

## Testing

```bash
cd backend
source venv/bin/activate
pytest tests/ -v
```

**36 tests** covering:
- Authentication (JWT token creation/validation)
- Clip engine (SRT parsing, candidate identification)
- Clip scoring (composite scores, temporal position, dialogue density, embeddings)
- Recommendation engine (feed composition rules, genre diversity)
- Configuration validation

---

## License

This project is for personal use. All clip content is sourced from the user's own Plex media library and never leaves the local network.
