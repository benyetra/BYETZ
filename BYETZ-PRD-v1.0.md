# BYETZ — Product Requirements Document

**Your Personal Clip Feed**

---

| | | | |
|---|---|---|---|
| **Document:** | Product Requirements Document | **Version:** | 1.0 |
| **Author:** | Bennett / BYETZ Team | **Date:** | February 18, 2026 |
| **Status:** | Draft | **Platform:** | iOS (iPhone / iPad) |

---

## 1. Executive Summary

BYETZ is a native iOS application that transforms a user's personal Plex media library into an intelligent, TikTok-style horizontal clip feed. The app automatically identifies and extracts the most memorable 15–30 second moments from movies and TV shows, then serves them in an infinitely scrollable landscape feed that learns from user preferences over time.

Unlike existing clip platforms that rely on user-generated content or licensed snippet libraries, BYETZ operates entirely on the user's own media—turning a personal Plex library into a personalized highlight reel powered by AI-driven scene detection, subtitle analysis, and a collaborative filtering recommendation engine.

---

## 2. Vision and Goals

### 2.1 Product Vision

BYETZ reimagines how people experience their personal media libraries. Instead of choosing a full movie or episode, users open BYETZ for a quick, lean-back experience—like flipping through a highlight reel of their favorite content, discovering forgotten moments from shows they watched years ago, and reliving the best scenes from their collection.

### 2.2 Strategic Goals

- Deliver an effortless, addiction-loop viewing experience for personal media content
- Build an intelligent recommendation engine that demonstrably improves clip relevance over the first 50 interactions
- Achieve sub-3-second clip load times on local network for seamless scrolling
- Process and index a 500-title Plex library within 24 hours of initial setup
- Maintain a clip quality bar where 70%+ of served clips receive positive engagement (like or save)

### 2.3 Success Metrics

| Metric | Target | Measurement |
|---|---|---|
| Avg. Session Duration | > 8 minutes | In-app analytics |
| Like Rate | > 40% of clips viewed | Like/view ratio |
| Clip Load Time | < 3 seconds (LAN) | Performance monitoring |
| Library Processing | < 24 hours / 500 titles | Background job telemetry |
| Recommendation Accuracy | 70%+ positive engagement | Like rate on ML-served clips |
| Retention (D7) | > 60% return rate | Daily active tracking |

---

## 3. User Personas

### 3.1 Primary: The Media Collector

**Profile:** Power Plex user with 200+ titles. Curates their library carefully and has deep nostalgia for their collection. Wants to rediscover content without committing to a full rewatch.

**Behavior:** Opens app during downtime—commute, lunch break, before bed. Watches 10–20 clips per session. Saves clips to share contexts with friends and family.

**Pain Point:** Has hundreds of movies and shows but defaults to rewatching the same 5 titles. Forgets great moments buried in their library.

### 3.2 Secondary: The Casual Browser

**Profile:** Household member who doesn't manage the Plex server but has access. Not interested in choosing what to watch—wants to be served content.

**Behavior:** Opens app for passive entertainment. Relies entirely on the recommendation engine. Rarely saves clips but likes/dislikes frequently.

**Pain Point:** Decision fatigue when browsing a large library. Wants a "just play something good" experience.

---

## 4. Feature Requirements

### 4.1 Onboarding and Plex Authentication

The onboarding flow must feel fast and purposeful—get the user to their first clip in under 2 minutes.

#### 4.1.1 Plex OAuth Integration

| ID | Requirement | Priority | Phase |
|---|---|---|---|
| ON-01 | Plex OAuth 2.0 authentication flow with token storage in iOS Keychain | P0 | MVP |
| ON-02 | Server discovery: auto-detect available Plex servers on user account | P0 | MVP |
| ON-03 | Library selection: display available movie and TV libraries for user to enable | P0 | MVP |
| ON-04 | Connection health indicator showing Plex server reachability status | P1 | MVP |
| ON-05 | Support for multiple Plex servers with library aggregation | P2 | v2 |
| ON-06 | Offline token refresh and re-authentication prompts | P1 | MVP |

#### 4.1.2 Taste Profile Setup

After authentication, users select sample content to seed the recommendation engine. This step is critical for cold-start quality.

| ID | Requirement | Priority | Phase |
|---|---|---|---|
| TP-01 | Display grid of movie/show posters from user's library (pulled via Plex API metadata) | P0 | MVP |
| TP-02 | Require minimum 10 selections before proceeding (with progress indicator) | P0 | MVP |
| TP-03 | Support genre-based quick-select: tap a genre chip to auto-select matching titles | P1 | MVP |
| TP-04 | Store selections as initial positive signals in recommendation engine | P0 | MVP |
| TP-05 | Allow skip with warning that recommendations will be less accurate initially | P1 | v2 |
| TP-06 | Re-run taste profile from settings at any time | P1 | v2 |

### 4.2 Core Clip Feed Experience

The feed is the heart of BYETZ. Every design decision should optimize for smooth, delightful, binge-worthy scrolling.

#### 4.2.1 Feed Layout and Navigation

| ID | Requirement | Priority | Phase |
|---|---|---|---|
| CF-01 | Horizontal, landscape-only video feed with vertical scroll (swipe up/down to advance clips) | P0 | MVP |
| CF-02 | Force landscape orientation when feed is active; lock rotation | P0 | MVP |
| CF-03 | Full-bleed video playback with no chrome visible during playback | P0 | MVP |
| CF-04 | Tap-to-pause/resume with semi-transparent overlay showing clip metadata | P0 | MVP |
| CF-05 | Auto-advance to next clip when current clip finishes | P0 | MVP |
| CF-06 | Progress bar showing clip position (thin, non-intrusive, bottom of screen) | P1 | MVP |
| CF-07 | Double-tap right side to skip forward 5 seconds within a clip | P2 | v2 |
| CF-08 | Swipe left/right for clip info panel (title, movie/show name, timestamp, season/episode) | P1 | MVP |

#### 4.2.2 Clip Specifications

| ID | Requirement | Priority | Phase |
|---|---|---|---|
| CS-01 | Maximum clip duration: 30 seconds. Minimum: 8 seconds. | P0 | MVP |
| CS-02 | All clips rendered in landscape (16:9 or source aspect ratio) | P0 | MVP |
| CS-03 | Target encoding: H.264/AAC in MP4 container with fast-start flag | P0 | MVP |
| CS-04 | Adaptive bitrate: 1080p on WiFi, 720p on cellular | P1 | v2 |
| CS-05 | Clean clip boundaries: start/end on scene changes, not mid-dialogue | P0 | MVP |
| CS-06 | Audio fade-in (0.5s) and fade-out (1.0s) at clip boundaries | P1 | MVP |
| CS-07 | Subtitle overlay option (toggle in settings, default off) | P2 | v2 |

#### 4.2.3 Engagement Actions

| ID | Requirement | Priority | Phase |
|---|---|---|---|
| EA-01 | Like button (right side overlay, heart icon): positive signal to recommendation engine | P0 | MVP |
| EA-02 | Dislike button (right side overlay, X icon): negative signal, immediately skip to next clip | P0 | MVP |
| EA-03 | Save button (right side overlay, bookmark icon): adds clip to user's saved library | P0 | MVP |
| EA-04 | Share button: generate shareable deep link or export clip to camera roll | P2 | v2 |
| EA-05 | Long-press to see clip source details (movie title, timestamp, scene context) | P1 | MVP |
| EA-06 | Haptic feedback on like/dislike/save actions | P1 | MVP |
| EA-07 | "Watch Full Scene" button that opens extended clip (2–5 min) or launches Plex to that timestamp | P2 | v2 |

### 4.3 Clip Generation Engine (Backend Service)

The clip generation engine is a Python-based background service that runs on the same machine as the Plex server (or a companion device on the same network). It is responsible for analyzing media files, identifying clip-worthy moments, extracting clips, and maintaining the clip database.

#### 4.3.1 Media Analysis Pipeline

| ID | Requirement | Priority | Phase |
|---|---|---|---|
| MA-01 | Extract embedded subtitles (SRT) from all media files via FFmpeg | P0 | MVP |
| MA-02 | Cross-reference dialogue against popular quote databases (IMDb Quotes, OpenSubtitles) | P0 | MVP |
| MA-03 | Scene change detection using FFmpeg scene filter to identify clean boundaries | P0 | MVP |
| MA-04 | Audio energy analysis to detect dramatic peaks, music swells, and comedic timing | P1 | MVP |
| MA-05 | AI scene scoring: send candidate frames to vision model API for clip-worthiness assessment | P2 | v2 |
| MA-06 | Dialogue density analysis: identify rapid-fire dialogue exchanges (comedic/dramatic) | P1 | v2 |
| MA-07 | Music-only moment detection for cinematic/montage sequences | P2 | v2 |

#### 4.3.2 Clip Extraction

| ID | Requirement | Priority | Phase |
|---|---|---|---|
| CE-01 | FFmpeg-based extraction with scene-snapped boundaries and keyframe alignment | P0 | MVP |
| CE-02 | Audio normalization across all clips (-16 LUFS target) | P1 | MVP |
| CE-03 | Fade-in/fade-out audio processing at clip boundaries | P1 | MVP |
| CE-04 | Generate 3 thumbnail candidates per clip for feed preview | P0 | MVP |
| CE-05 | Encode clips as H.264/AAC MP4 with movflags +faststart | P0 | MVP |
| CE-06 | Store clips in organized directory structure: /clips/{media_id}/{clip_id}.mp4 | P0 | MVP |
| CE-07 | Background processing queue with priority (recently added media processed first) | P1 | MVP |
| CE-08 | Target 5–15 clips per movie, 3–8 clips per TV episode | P0 | MVP |

#### 4.3.3 Clip Scoring Algorithm

Each candidate clip receives a composite score from multiple signals. The scoring algorithm determines which clips surface in the feed and in what order.

| Signal | Weight | Description |
|---|---|---|
| Quote Match Score | 35% | Confidence of dialogue match against known popular quotes |
| Audio Energy Score | 20% | Peak audio energy relative to surrounding scenes |
| Scene Composition | 15% | Visual interest from scene change density and framing |
| Dialogue Density | 15% | Rapid exchanges, comedic timing patterns |
| Temporal Position | 10% | Climactic scenes (final 20% of runtime) get a boost |
| AI Vision Score | 5% (v2) | Vision model assessment of visual interest and memorability |

### 4.4 Recommendation Engine

The recommendation engine is the intelligence layer that transforms raw clips into a personalized, ever-improving feed. It operates on three levels: content-based filtering, collaborative signals, and real-time session learning.

#### 4.4.1 Cold Start Strategy

- Seed with taste profile selections: clips from selected titles get maximum initial boost
- Genre affinity matrix: if user selects 5 action movies, boost action clips from unselected titles
- Popular-first fallback: serve highest-scored clips across library until sufficient engagement data
- Decay cold start weight over first 50 interactions as personalization data accumulates

#### 4.4.2 Signal Processing

| ID | Requirement | Priority | Phase |
|---|---|---|---|
| RE-01 | Like: +1.0 weight to clip, +0.3 to same title, +0.1 to same genre/actors | P0 | MVP |
| RE-02 | Dislike: -1.0 weight to clip, -0.2 to same title, -0.05 to same genre | P0 | MVP |
| RE-03 | Save: +1.5 weight (stronger than like, indicates rewatchable) | P0 | MVP |
| RE-04 | Watch completion: +0.5 if watched to end, -0.3 if skipped in first 5s | P0 | MVP |
| RE-05 | Re-watch detection: +0.8 if user watches a saved clip again | P1 | v2 |
| RE-06 | Session momentum: if 3+ consecutive likes from same genre, temporarily boost that genre | P1 | MVP |
| RE-07 | Implicit negative: no engagement after 3 clips from same title signals disinterest | P1 | v2 |

#### 4.4.3 Feed Composition Rules

- Never serve 3+ consecutive clips from the same title
- Ensure genre diversity: no more than 40% of any session from one genre
- Recency bias: newly processed clips get a 1.2x boost for the first 48 hours
- Avoid repetition: do not re-serve a disliked clip; delay re-serving liked clips by 7+ days
- Exploration rate: 20% of clips should be from untested titles/genres to prevent filter bubbles
- Time-of-day awareness: lighter/comedic content weighted higher in morning, dramatic content in evening (v2)

#### 4.4.4 Learning and Model Architecture

The recommendation engine uses a hybrid approach combining content-based filtering with a lightweight neural collaborative filtering model.

- Feature vectors per clip: genre, actors, director, decade, clip score components, mood tags
- User embedding: 64-dimensional vector updated after every interaction via online learning
- Clip embedding: 64-dimensional vector derived from content features and aggregate engagement
- Prediction: dot product of user and clip embeddings produces relevance score
- Model retrained nightly on full interaction history; online updates between retrains
- A/B framework: serve 10% of clips from challenger model to continuously evaluate improvements

---

## 5. Technical Architecture

### 5.1 System Overview

BYETZ operates as a two-component system: a native iOS client app and a Python-based backend service that runs alongside (or on) the Plex server. The backend handles all media processing, clip generation, and recommendation computation. The iOS app is a lightweight client that fetches and displays clips.

#### 5.1.1 Architecture Components

| Component | Technology | Responsibility |
|---|---|---|
| iOS Client | Swift / SwiftUI | Feed UI, video playback, user interactions, local caching |
| Backend API | Python / FastAPI | REST API for clips, recommendations, user data |
| Clip Engine | Python / FFmpeg | Media analysis, scene detection, clip extraction |
| Rec Engine | Python / PyTorch | Recommendation model training and inference |
| Database | PostgreSQL | Clips, users, interactions, embeddings, metadata |
| Task Queue | Celery / Redis | Background clip processing jobs |
| Clip Storage | Local filesystem | Extracted clip MP4 files served via API |

#### 5.1.2 Data Flow

1. Plex webhook or polling detects new/updated media in library
2. Clip Engine queues media for analysis: subtitle extraction, scene detection, audio analysis
3. Candidate clips are scored and top N per title are extracted via FFmpeg
4. Clip metadata and embeddings stored in PostgreSQL
5. iOS client requests personalized feed from Backend API
6. Rec Engine computes ranked clip list based on user profile and interaction history
7. Client streams clips directly from Backend API (or proxied from Plex)
8. User interactions (like/dislike/save/skip) sent back to update recommendation model

### 5.2 iOS Client Architecture

- SwiftUI with MVVM architecture and Combine for reactive data binding
- AVFoundation for video playback with AVQueuePlayer for pre-buffering next clips
- URLSession with custom caching layer: pre-fetch next 3 clips, evict clips 5+ positions behind
- Core Data for local persistence of liked/saved clips and offline viewing queue
- Keychain Services for secure Plex token storage
- Forced landscape orientation via Info.plist supported orientations and programmatic lock

### 5.3 API Endpoints

| Method | Endpoint | Description |
|---|---|---|
| POST | /auth/plex | Authenticate via Plex OAuth token exchange |
| GET | /feed?limit=10&offset=0 | Fetch personalized clip feed (paginated) |
| GET | /clips/{id}/stream | Stream clip video file with range support |
| POST | /interactions | Submit like/dislike/save/skip event |
| GET | /profile | User profile, stats, and preferences |
| GET | /saved | Retrieve user's saved clips library |
| GET | /library/status | Plex library sync and processing status |
| PUT | /settings | Update user preferences and settings |
| POST | /library/rescan | Trigger manual library rescan |
| GET | /taste-profile/titles | Fetch library titles for taste profile selection |

### 5.4 Database Schema (Core Tables)

#### clips

| Column | Type | Description |
|---|---|---|
| **id** | UUID (PK) | Unique clip identifier |
| media_id | VARCHAR | Plex rating key for source media |
| title | VARCHAR | Source movie/show title |
| season_episode | VARCHAR | S01E05 format (null for movies) |
| start_time_ms | BIGINT | Clip start position in source media (ms) |
| end_time_ms | BIGINT | Clip end position in source media (ms) |
| duration_ms | INT | Clip duration (8000–30000) |
| file_path | VARCHAR | Path to extracted clip file |
| composite_score | FLOAT | Weighted clip quality score (0–1.0) |
| genre_tags | JSONB | Array of genre tags from source media |
| embedding | VECTOR(64) | Content embedding for recommendation |
| created_at | TIMESTAMP | Clip creation timestamp |

#### interactions

| Column | Type | Description |
|---|---|---|
| **id** | UUID (PK) | Unique interaction ID |
| user_id | UUID (FK) | Reference to users table |
| clip_id | UUID (FK) | Reference to clips table |
| action | ENUM | like, dislike, save, skip, watch_complete |
| watch_duration_ms | INT | How long user watched before action |
| session_id | UUID | Groups interactions in a viewing session |
| created_at | TIMESTAMP | Interaction timestamp |

#### user_embeddings

| Column | Type | Description |
|---|---|---|
| **user_id** | UUID (PK, FK) | Reference to users table |
| embedding | VECTOR(64) | User preference embedding |
| genre_weights | JSONB | Per-genre affinity scores |
| last_retrained | TIMESTAMP | Last full model retrain timestamp |
| interaction_count | INT | Total interactions for cold-start logic |

---

## 6. UX/UI Design Guidelines

### 6.1 Design Principles

- **Content-first:** The video is always the hero. UI elements are minimal overlays that fade after 2 seconds of inactivity.
- **Dark mode default:** Dark backgrounds to maximize video contrast and reduce eye strain during extended viewing.
- **Thumb-friendly:** All interactive elements positioned within natural thumb reach zones for landscape holding.
- **Zero-friction:** No confirmations, no modals during playback. Like/dislike/save are single-tap instant actions.
- **Smooth transitions:** Clips crossfade or use a subtle slide transition. No jarring cuts or loading spinners.

### 6.2 Screen Map

| Screen | Key Elements |
|---|---|
| Splash / Loading | BYETZ logo, Plex connection status animation |
| Plex Auth | Plex OAuth web view, server selection list |
| Taste Profile | Poster grid with multi-select, genre chips, progress bar, continue button |
| Main Feed | Full-screen video, action buttons (right edge), progress bar (bottom), swipe-up to advance |
| Clip Info Panel | Slide-in overlay: title, source, timestamp, cast, genre tags |
| Profile | Avatar, stats row, saved clips grid, liked clips list, collection folders |
| Library Manager | Library list with toggle switches, processing progress bars, exclude list |
| Settings | Plex connection, clip preferences, content filter, notifications, reset options |

### 6.3 Interaction Patterns

| Gesture | Action |
|---|---|
| Swipe Up | Advance to next clip |
| Swipe Down | Return to previous clip |
| Single Tap (center) | Pause/resume playback |
| Double Tap (right) | Skip forward 5 seconds (v2) |
| Swipe Left | Open clip info panel |
| Long Press | Show extended clip details and source info |
| Tap Like/Dislike/Save | Record interaction with haptic feedback |

---

## 7. Performance Requirements

| Metric | Target | Condition |
|---|---|---|
| First clip playback | < 2 seconds | LAN / WiFi |
| Clip-to-clip transition | < 500ms | Pre-buffered |
| Feed API response | < 200ms | 10 clips per request |
| Interaction recording | < 100ms | Async, non-blocking |
| App memory footprint | < 250MB | During playback |
| Clip processing throughput | 1 movie / 10 min | On modern hardware |
| Library initial scan | < 24 hours | 500 titles |
| Recommendation inference | < 50ms | Per feed request |

---

## 8. Development Roadmap

### 8.1 Phase 1: MVP (Weeks 1–8)

Deliver a functional end-to-end experience: Plex auth, clip generation from subtitles and scene detection, basic feed with like/dislike/save, and rule-based recommendations.

- Plex OAuth integration and server/library discovery
- Subtitle-based clip identification (quote matching against IMDb/OpenSubtitles)
- Scene change detection for clean clip boundaries
- FFmpeg clip extraction pipeline with audio normalization
- Landscape-only feed with swipe navigation and AVQueuePlayer
- Like/dislike/save actions with rule-based recommendation weighting
- Taste profile onboarding flow
- Basic profile screen with saved clips library
- Library management with enable/disable and processing status

### 8.2 Phase 2: Intelligence (Weeks 9–14)

Upgrade recommendation engine to ML-based, add audio energy analysis, and enhance the profile experience.

- Neural collaborative filtering model (PyTorch) with online learning
- Audio energy analysis for dramatic peak detection
- A/B testing framework for recommendation model comparison
- Custom collections in profile
- Viewing history and engagement analytics dashboard
- Content maturity filtering

### 8.3 Phase 3: Polish (Weeks 15–20)

Add AI vision scoring, sharing capabilities, and advanced personalization features.

- AI vision model integration for scene scoring
- Share clips via deep link or camera roll export
- "Watch Full Scene" integration with Plex deep linking
- Adaptive bitrate streaming for cellular usage
- Time-of-day content mood awareness
- Subtitle overlay option
- Multi-server support

---

## 9. Risks and Mitigations

| Risk | Severity | Mitigation |
|---|---|---|
| Low clip quality from subtitle-only detection | **High** | Layer multiple signals (audio, scene, temporal). Allow user to flag bad clips to improve model. |
| Plex API rate limits or changes | **Medium** | Cache metadata aggressively. Use webhooks over polling where possible. Abstract Plex API behind adapter layer. |
| Storage consumption on server | **Medium** | 720p default encoding. Configurable quality. Auto-cleanup of low-engagement clips after 90 days. |
| Cold start: poor initial recommendations | **High** | Mandatory taste profile. Genre affinity seeding. Popular-first fallback. Fast decay to personalized model. |
| Processing time for large libraries | **Medium** | Priority queue (newest first). Progressive availability. Background processing with status updates. |
| Network dependency for remote Plex | **Low** | Local clip caching on device. Offline saved clips playback. Graceful degradation. |
| Copyright/legal concerns with clip extraction | **Low** | All content from user's own library. Clips never leave local network. No public distribution. |

---

## 10. Appendix

### 10.1 Technology Stack Summary

| Layer | Technology | Rationale |
|---|---|---|
| iOS Client | Swift 5.9 / SwiftUI | Native performance, modern declarative UI |
| Video Playback | AVFoundation / AVQueuePlayer | Native iOS video pipeline, hardware decoding |
| Backend API | Python 3.12 / FastAPI | Async performance, Pydantic validation |
| Media Processing | FFmpeg 6.x | Industry standard, comprehensive codec support |
| Database | PostgreSQL 16 + pgvector | Vector similarity search for embeddings |
| Task Queue | Celery + Redis | Reliable background job processing |
| ML Framework | PyTorch 2.x | Lightweight NCF model, online learning |
| Containerization | Docker Compose | Simple deployment alongside Plex server |

### 10.2 External Data Sources

- **Plex API:** Media metadata, library contents, user authentication
- **IMDb Quotes:** Popular quote database for clip identification scoring
- **OpenSubtitles API:** Subtitle matching and cross-referencing for dialogue identification
- **TMDb API:** Supplementary metadata including genre tags, cast, crew, and content ratings

### 10.3 Glossary

| Term | Definition |
|---|---|
| **Clip** | An 8–30 second extracted segment from a movie or TV episode |
| **Composite Score** | Weighted quality score (0–1.0) combining quote match, audio, scene, and temporal signals |
| **Cold Start** | Period before sufficient user interaction data exists for personalized recommendations |
| **Embedding** | 64-dimensional vector representation of a clip or user for recommendation computation |
| **NCF** | Neural Collaborative Filtering — ML model that predicts user preference from embeddings |
| **Scene Snap** | Adjusting clip boundaries to align with detected scene changes for clean cuts |
| **Taste Profile** | Initial content selections made during onboarding to seed the recommendation engine |
| **Exploration Rate** | Percentage of feed clips from untested content to prevent filter bubbles (20%) |

---

*CONFIDENTIAL — For Internal Use Only*
