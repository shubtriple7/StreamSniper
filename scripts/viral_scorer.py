#!/usr/bin/env python3
"""
爆款潜力评分与排序引擎 (Viral Scorer)
结合：
1. 弹幕爆发倍率 (Chat Velocity Spike Ratio)
2. 情绪关键词密度 (KEKW / LMAO / W / WTF / 💀)
3. 音频动态峰值 (Audio Energy / Scream Detection via FFmpeg volumedetect)
4. 前 3 秒语音 Hook 与台词转录 (Faster-Whisper)
计算 0-100% 的 Viral Score，并按爆款概率输出排名报告与发帖文案
"""

import sys
import os
import re
import json
import subprocess
from pathlib import Path
from typing import List, Dict, Optional


def analyze_audio_energy(video_path: str) -> Dict[str, float]:
    """使用 FFmpeg volumedetect 检测音量峰值与动态"""
    try:
        cmd = ["ffmpeg", "-i", str(video_path), "-af", "volumedetect", "-f", "null", "-"]
        res = subprocess.run(cmd, capture_output=True, text=True, timeout=15)
        max_vol = -50.0
        mean_vol = -50.0

        for line in res.stderr.splitlines():
            if "max_volume:" in line:
                m = re.search(r"max_volume:\s*([-0-9.]+)\s*dB", line)
                if m:
                    max_vol = float(m.group(1))
            elif "mean_volume:" in line:
                m = re.search(r"mean_volume:\s*([-0-9.]+)\s*dB", line)
                if m:
                    mean_vol = float(m.group(1))

        # 音量越接近 0 dB，代表有大喊大叫、欢呼或激烈爆炸音效
        # 范围通常在 -30 到 0 之间
        energy_score = max(0.0, min(100.0, (max_vol + 30.0) * 3.33))
        return {
            "max_volume_db": max_vol,
            "mean_volume_db": mean_vol,
            "energy_score": round(energy_score, 1)
        }
    except Exception:
        return {"max_volume_db": -25.0, "mean_volume_db": -35.0, "energy_score": 50.0}


def evaluate_speech_hook(transcript_text: str) -> Dict[str, any]:
    """评估台词的前 3 秒 Hook 吸引力与悬念"""
    text = transcript_text.strip().lower()
    hook_score = 50.0
    hook_reasons = []

    if not text:
        return {"hook_score": 30.0, "hook_feature": "无台词/纯反应/游戏原声"}

    # 疑问句 / 悬念 / 冲突
    if any(q in text for q in ["what", "why", "how", "怎么", "为什么", "啥", "谁"]):
        hook_score += 20.0
        hook_reasons.append("强烈疑问/好奇引导")

    # 情绪感叹词
    if any(ex in text for ex in ["bro", "no way", "oh my god", "wtf", "holy", "靠", "卧槽", "不是吧"]):
        hook_score += 25.0
        hook_reasons.append("高能情绪开场")

    # 挑战或承诺
    if any(ch in text for ch in ["watch this", "look", "listen", "看好", "看这个", "我敢说"]):
        hook_score += 15.0
        hook_reasons.append("直接呼吁注意 (Hook)")

    hook_score = min(100.0, hook_score)
    return {
        "hook_score": round(hook_score, 1),
        "hook_feature": " + ".join(hook_reasons) if hook_reasons else "常规语境"
    }


def compute_viral_score(moment_meta: Dict, audio_meta: Dict, speech_meta: Dict) -> Dict:
    """
    加权计算综合爆款概率分数 (0 - 100%)
    权重分配:
    - 弹幕爆发倍率 (35%)
    - 情绪与高光词权重 (25%)
    - 音频能量与尖叫/欢呼 (20%)
    - 台词 Hook 与互动性 (20%)
    """
    # 1. 弹幕爆发分
    spike_ratio = moment_meta.get("score", 1.0) / max(0.1, moment_meta.get("baseline", 1.0))
    # 爆发倍率通常 2x - 10x
    chat_spike_score = min(100.0, (spike_ratio / 5.0) * 100.0)

    # 2. 关键词与表情密度
    kw_count = len(moment_meta.get("top_keywords", []))
    kw_score = min(100.0, kw_count * 20.0 + 20.0)

    # 3. 音频动态
    audio_score = audio_meta.get("energy_score", 50.0)

    # 4. 语音 Hook
    hook_score = speech_meta.get("hook_score", 50.0)

    composite = (
        chat_spike_score * 0.35 +
        kw_score * 0.25 +
        audio_score * 0.20 +
        hook_score * 0.20
    )
    composite = round(min(99.0, max(20.0, composite)), 1)

    if composite >= 85.0:
        tier = "🔥 极高爆款潜质 (Viral Mega-Hit)"
    elif composite >= 70.0:
        tier = "⭐ 高互动高光 (High Engagement)"
    elif composite >= 55.0:
        tier = "👍 精华片段 (Solid Highlight)"
    else:
        tier = "📌 常规切片 (Standard Moment)"

    return {
        "viral_score": composite,
        "tier": tier,
        "chat_spike_score": round(chat_spike_score, 1),
        "kw_score": round(kw_score, 1),
        "audio_score": round(audio_score, 1),
        "hook_score": round(hook_score, 1)
    }


def rank_and_report_clips(clips_data: List[Dict], output_file: Optional[str] = None) -> List[Dict]:
    """
    对候选切片进行综合爆款评分排序并输出报告
    """
    scored_clips = []
    for item in clips_data:
        video_path = item.get("clip_path")
        moment_meta = item.get("moment", {})
        transcript = item.get("transcript", "")

        audio_meta = analyze_audio_energy(video_path) if video_path and os.path.exists(video_path) else {"energy_score": 50.0}
        speech_meta = evaluate_speech_hook(transcript)
        score_res = compute_viral_score(moment_meta, audio_meta, speech_meta)

        item_result = {
            **item,
            **score_res,
            "audio_energy": audio_meta,
            "speech_hook": speech_meta
        }
        scored_clips.append(item_result)

    # 按爆款评分降序排序
    scored_clips.sort(key=lambda x: x["viral_score"], reverse=True)

    # 生成 Markdown 总结
    report_lines = [
        "# 🎬 实时直播高光剪辑 & 爆款潜力排行榜",
        "",
        f"**共捕获高光片段**: {len(scored_clips)} 段",
        "",
        "| 排名 | 爆款指数 | 等级 | 时间段 | 弹幕高光词 | 核心台词 / 反应 | 剪辑文件 |",
        "| :--- | :--- | :--- | :--- | :--- | :--- | :--- |"
    ]

    for rank, clip in enumerate(scored_clips, 1):
        m = clip.get("moment", {})
        time_str = f"{m.get('start_time', 0):.0f}s - {m.get('end_time', 0):.0f}s"
        kws = ", ".join(m.get("top_keywords", [])[:3]) or "弹幕狂涌"
        text_preview = (clip.get("transcript", "")[:35] + "...") if clip.get("transcript") else "音效/反应高潮"
        file_name = Path(clip.get("clip_path", "")).name

        report_lines.append(
            f"| **#{rank}** | **{clip['viral_score']}%** | {clip['tier'].split()[0]} | `{time_str}` | `{kws}` | {text_preview} | `{file_name}` |"
        )

    report_lines.extend([
        "",
        "## 💡 爆款发布建议 (TikTok / YouTube Shorts / Reels)",
        ""
    ])

    for rank, clip in enumerate(scored_clips[:3], 1):
        m = clip.get("moment", {})
        kws = " ".join([f"#{kw}" for kw in m.get("top_keywords", [])[:3]])
        report_lines.extend([
            f"### Top #{rank} (爆款指数: {clip['viral_score']}%)",
            f"- **文件**: `{clip.get('clip_path')}`",
            f"- **推荐标题**: 😱 当主播触发 `{', '.join(m.get('top_keywords', [])[:2])}` 瞬间，弹幕彻底炸了！",
            f"- **推荐标签**: `#streamer #livestream #highlight #clips #fyp {kws}`",
            ""
        ])

    report_text = "\n".join(report_lines)
    if output_file:
        with open(output_file, "w", encoding="utf-8") as f:
            f.write(report_text)
        print(f"📊 爆款排行榜已生成: {output_file}")

    print("\n" + report_text)
    return scored_clips
