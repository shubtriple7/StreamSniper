<div align="center">

# 🎯 StreamSniper

### Autonomous AI Live Stream & Chat Hype Clipper
**Turn Hours of Live Streams into Ranked Viral Shorts & Clips — Completely Automated.**

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![Supported Platforms](https://img.shields.io/badge/Platforms-YouTube%20%7C%20Twitch%20%7C%20Kick-purple)](#-supported-platforms)
[![Transcription](https://img.shields.io/badge/AI%20Audio-Faster--Whisper-orange)](https://github.com/SYSTRAN/faster-whisper)
[![PRs Welcome](https://img.shields.io/badge/PRs-welcome-brightgreen.svg)](https://github.com)

[Key Features](#-key-features) • [How It Works](#-how-it-works) • [Installation](#-installation) • [Quick Start](#-quick-start) • [Viral Scoring](#-viral-scoring-formula) • [Contributing](#-contributing)

</div>

---

## ⚡ The Problem

Streamers broadcast for 6 to 10 hours daily. Editors and clippers spend countless exhausting hours scrubbing through endless VOD timelines just to spot the 30-second funny moments, clutches, fails, or drama.

**StreamSniper solves this:** It watches the stream for you, connects to real-time chat rooms, detects when chat explodes with hype, automatically clips the moment, transcribes the speech, and ranks clips by **Viral Potential (0–100%)**.

---

## 🌟 Key Features

* 🚀 **Multi-Platform Native**: First-class support for **YouTube** (Videos, Shorts, Live with DVR), **Twitch** (Live, VODs, Clips), and **Kick** (Live, VODs, Clips).
* 🔥 **Live Hype Hunter (Real-Time Chat Spikes)**:
  - Hooks directly into live chat rooms via zero-auth **Twitch IRC**, **Kick Pusher WebSockets**, and **YouTube Live Chat**.
  - Calculates rolling **Chat Velocity (messages/second)** and tracks bursts of emotes (`KEKW`, `LMAO`, `W`, `L`, `💀`, `WTF`, `POG`, `CLIP IT`).
  - Auto-cuts **30-second clips** around the peak (`[Peak - 15s to Peak + 15s]`).
* 📊 **Viral Potential Scoring (0–100%)**:
  - Automatically ranks all candidate clips at the end of the stream.
  - Combines chat eruption ratio, emote density, audio scream/cheer energy, and spoken hook strength.
* 🎙️ **Faster-Whisper Auto-Transcription**:
  - Automatically transcribes speech even on platforms without native subtitles (Twitch / Kick / uncaptioned livestreams) using quantized local models (`base` / `tiny`).
* ✂️ **AI Semantic VOD Clipper**:
  - For full videos / past VODs: Analyzes semantic topics and splits content into 2–5 minute self-contained chapters instead of mechanical time cuts.
* 🌐 **Bilingual Subtitles & Hardcoding**:
  - Batch translates subtitles and hardcodes styled bilingual subtitles directly into the video via FFmpeg with `libass`.
* 📱 **Ready-to-Post Content**:
  - Generates optimized social titles, summaries, and hashtags for TikTok, YouTube Shorts, and Instagram Reels.

---

## 🔄 How It Works

```
                     ┌─────────────────────────────────────────────────────────┐
                     │            Live Stream (YouTube / Twitch / Kick)        │
                     └────────────────────────────┬────────────────────────────┘
                                                  │
                 ┌────────────────────────────────┴──────────────────────────────┐
                 ▼                                                               ▼
  [ Background Video Recorder ]                                  [ Real-Time Chat Ingestion ]
  • Stream captured losslessly via FFmpeg                         • Twitch IRC / Kick Pusher / YT Chat
  • Rolling session buffer                                        • Tracks Chat Velocity (msg/s)
                 │                                                • Monitors Hype Emotes & Caps Rate
                 │                                                               │
                 │                                                               ▼
                 │                                                [ Hype Spike Detector (EMA) ]
                 │                                                • Triggers on >2.2x Chat Surges
                 │                                                • Enforces Cooldown Window
                 │                                                               │
                 └───────────────────────────────┬───────────────────────────────┘
                                                 │
                                                 ▼
                               [ Auto 30s Clip Extraction ]
                               [Peak - 15s] ──► Peak ──► [Peak + 15s]
                                                 │
                                                 ▼
                                  [ AI Multimodal Evaluation ]
                       ┌─────────────────────────┴─────────────────────────┐
                       ▼                                                   ▼
            [ Faster-Whisper ASR ]                             [ Audio Peak Dynamics ]
            • Local speech-to-text                             • FFmpeg volumedetect
            • Analyzes first 3s Hook                           • Screaming / Loud reaction check
                       └─────────────────────────┬─────────────────────────┘
                                                 │
                                                 ▼
                               [ Viral Ranking Report (0-100%) ]
                               • Top Ranked Viral Highlights
                               • Auto-generated TikTok / Shorts Captions
```

---

## 💻 Installation

### 1. Prerequisites

- **Python 3.10+**
- **FFmpeg with `libass` support**
  - **Windows**: Included in standard Gyan.dev full builds (`winget install Gyan.FFmpeg`)
  - **macOS**: `brew install ffmpeg-full`
  - **Ubuntu/Debian**: `sudo apt install ffmpeg libass-dev`

### 2. Install StreamSniper

```bash
git clone https://github.com/shubtriple7/StreamSniper.git
cd StreamSniper
pip install -r requirements.txt
```

---

## 🚀 Quick Start

### Mode 1: Live Stream Hype Hunter (Watch & Auto-Clip)

Keep watching a live stream. It monitors chat, detects hype moments, and cuts 30-second clips whenever chat erupts:

```bash
# Monitor a Twitch stream for 15 minutes (900 seconds)
python scripts/hype_monitor.py https://twitch.tv/shroud --duration 900 --clip-len 30

# Monitor a Kick live stream
python scripts/hype_monitor.py https://kick.com/xqc --duration 1200

# Monitor a YouTube live stream with customized sensitivity
python scripts/hype_monitor.py https://www.youtube.com/live/5qap5aO4i9A --duration 1800 --sensitivity 2.0
```

#### Output: `VIRAL_RANKING_REPORT.md`
```markdown
# 🎬 Live Stream Hype Ranking & Viral Report

| Rank | Viral Score | Tier | Time | Hype Keywords | Transcript Hook | Output File |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **#1** | **91.4%** | 🔥 Mega-Hit | `142s - 172s` | `💀, KEKW, CLIP` | "BRO NO WAY WHAT DID HE JUST DO?!" | `clip_01_142s.mp4` |
| **#2** | **78.2%** | ⭐ Highlight | `380s - 410s` | `W, POG, LETSGO` | "WE ACTUALLY CLUTCHED THAT!" | `clip_02_380s.mp4` |
```

---

### Mode 2: VOD & Video Smart Clipper

Download any recorded video or completed livestream VOD, auto-generate fine-grained chapters, translate subtitles, and burn them into clips:

```bash
# Download and auto-transcribe (YouTube / Twitch / Kick)
python scripts/download_video.py https://www.youtube.com/watch?v=dQw4w9WgXcQ

# Slice precise video segment
python scripts/clip_video.py video.mp4 00:01:30 00:04:15 output_clip.mp4

# Burn styled bilingual subtitles
python scripts/burn_subtitles.py output_clip.mp4 bilingual.srt final_clip.mp4
```

---

## 🧠 Viral Scoring Formula

Each clip's **Viral Potential Score (0–100%)** is dynamically calculated using a weighted multi-factor model:

$$\text{ViralScore} = (0.35 \times S_{\text{chat}}) + (0.25 \times K_{\text{emote}}) + (0.20 \times A_{\text{audio}}) + (0.20 \times H_{\text{hook}})$$

* **$S_{\text{chat}}$ (35%) - Chat Velocity Spike**: Magnitude of chat message surge compared to the stream's baseline.
* **$K_{\text{emote}}$ (25%) - Hype Keyword Density**: Frequency of viral reaction markers (`KEKW`, `LMAO`, `W`, `L`, `💀`, `WTF`, `CLIP`).
* **$A_{\text{audio}}$ (20%) - Audio Energy Dynamics**: Peak volume and sudden loud reactions (screams, cheers, drop sounds).
* **$H_{\text{hook}}$ (20%) - Spoken Hook Strength**: Speech transcription analysis for curiosity triggers, questions, and high-energy openers.

---

## 🔌 Use as an AI Skill / Agent Plugin

StreamSniper also acts as a native progressive skill for **Antigravity**, **Claude Code**, and **OpenAI Agents**:

```bash
# Works natively in Antigravity workspaces under:
.agent/skills/streamsniper/
```

Simply ask your AI assistant:
> *"Watch this Twitch stream for 20 minutes, cut the best 30s clips when chat goes crazy, and rank them by viral score."*

---

## 📜 License

Distributed under the MIT License. See [LICENSE](LICENSE) for more information.

---

<div align="center">
⭐ If StreamSniper saves you hours of video editing, consider giving it a star on GitHub!
</div>
