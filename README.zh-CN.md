<div align="center">

# 🎯 StreamSniper

### 跨平台 AI 实时直播盯盘与爆款切片系统
**监听弹幕高潮涌现，自动截取 30 秒爆款切片，全自动语音转录与爆款指数排行榜。**

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![Supported Platforms](https://img.shields.io/badge/平台-YouTube%20%7C%20Twitch%20%7C%20Kick-purple)](#-多平台支持)
[![Transcription](https://img.shields.io/badge/AI%20语音-Faster--Whisper-orange)](https://github.com/SYSTRAN/faster-whisper)

[English](README.md) • 简体中文

</div>

---

## ⚡ 痛点与解决

主播一次直播长达 6 至 10 小时。剪辑师往往需要耗费整晚拖动进度条，去大海捞针寻找那几十秒的爆笑失误、惊天翻盘或情绪破防。

**StreamSniper 彻底终结这个痛点：** 挂机监听直播流，直连 Twitch IRC、Kick Pusher 与 YouTube 实时聊天室，当弹幕喷涌爆发时（`KEKW`, `LMAO`, `W`, `L`, `💀`, `WTF`, `CLIP IT`），自动切出爆发前 15s 至后 15s 的 30 秒黄金切片，利用 Faster-Whisper 转录台词，并根据音频爆发与前 3 秒 Hook 计算 **0-100% 爆款指数 (Viral Score %)** 给出排行榜！

---

## 🌟 核心功能

* 🚀 **三大平台原生支持**：YouTube (视频/Shorts/直播及 DVR 回溯)、Twitch (直播/录播/剪辑)、Kick (直播/录播/剪辑)。
* 🔥 **实时直播盯盘与高光捕获 (Live Hype Hunter)**：
  - 零配置匿名监听 Twitch IRC、Kick Pusher WebSocket 与 YouTube Live Chat。
  - 动态自适应基线（EMA）监控弹幕瞬时喷涌速率 (Messages/sec) 及情绪表情浓度。
  - 爆发时自动无损裁剪 `[Peak - 15s ~ Peak + 15s]` 30 秒片段。
* 📊 **爆款指数排行榜 (Viral Scorer 0-100%)**：
  - 综合弹幕爆发倍数 (35%)、表情浓度 (25%)、音频音量动态 (20%) 与台词 Hook (20%)。
  - 自动输出适合抖音、小红书、TikTok、YouTube Shorts 的推荐标题与热门话题标签。
* 🎙️ **Faster-Whisper 本地离线转录**：针对 Twitch / Kick / 无官方字幕直播流，自动本地秒级生成高质量 SRT 字幕。
* ✂️ **VOD 智能章节拆解**：针对完整录播视频，按语义生成 2-5 分钟精细主题章节，点选剪辑并烧录双语硬字幕。

---

## 🚀 快速上手

### 依赖安装

```bash
git clone https://github.com/shubtriple7/StreamSniper.git
cd StreamSniper
pip install -r requirements.txt
```

### 1. 挂机盯盘直播并自动抓取高光

```bash
# 盯盘 Twitch 直播 15 分钟 (900秒)，每段切片 30 秒
python scripts/hype_monitor.py https://twitch.tv/shroud --duration 900 --clip-len 30

# 盯盘 Kick 直播
python scripts/hype_monitor.py https://kick.com/xqc --duration 1200

# 盯盘 YouTube 直播，设置敏感度为 2.0 倍弹幕暴增
python scripts/hype_monitor.py https://www.youtube.com/live/5qap5aO4i9A --duration 1800 --sensitivity 2.0
```

### 2. 录播/常规视频智能切片与烧录

```bash
# 下载并自动语音转录
python scripts/download_video.py <video_url>

# 剪辑指定片段
python scripts/clip_video.py video.mp4 00:01:30 00:04:15 clip.mp4

# 烧录双语字幕
python scripts/burn_subtitles.py clip.mp4 bilingual.srt final_clip.mp4
```

---

## 📜 开源协议

基于 MIT License 开源。
