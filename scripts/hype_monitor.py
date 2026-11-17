#!/usr/bin/env python3
"""
实时直播智能盯盘与爆款切片系统 (Live Stream Hype Monitor & Viral Clipper)
全自动：
1. 后台无损录制直播流 (YouTube / Twitch / Kick)
2. 实时捕获弹幕流并监控聊天速率暴增 (Chat Velocity Spike)
3. 动态触发 30 秒高光片段自动剪辑
4. 使用 Faster-Whisper 自动转录高潮台词
5. 综合计算爆款潜力指数 (Viral Score %)，最终按爆款概率输出排序与发布文案
"""

import sys
import os
import time
import json
import shutil
import argparse
import threading
import subprocess
from pathlib import Path
from typing import List, Dict

import yt_dlp

from utils import parse_url_info, ensure_directory, format_file_size, seconds_to_time
from live_chat_collector import TwitchChatListener, KickChatListener, YouTubeChatListener, ChatMessage
from hype_detector import HypeDetector
from clip_video import clip_video
from viral_scorer import rank_and_report_clips


def resolve_stream_url_and_meta(url: str) -> Dict:
    """解析直播流真实播放地址和元数据"""
    probe_opts = {
        'quiet': True,
        'no_warnings': True,
        'js_runtimes': {'node': {}}
    }
    with yt_dlp.YoutubeDL(probe_opts) as ydl:
        info = ydl.extract_info(url, download=False)
        stream_url = info.get('url')
        if not stream_url and 'formats' in info and info['formats']:
            stream_url = info['formats'][-1].get('url')

        return {
            'title': info.get('title', 'Live Stream'),
            'uploader': info.get('uploader') or info.get('channel') or 'streamer',
            'id': info.get('id', 'stream'),
            'stream_url': stream_url,
            'is_live': info.get('is_live', True)
        }


def start_stream_recorder(stream_url: str, output_file: Path, duration: int) -> subprocess.Popen:
    """启动 FFmpeg 后台无损流录制"""
    ffmpeg_bin = shutil.which("ffmpeg") or "ffmpeg"
    cmd = [
        ffmpeg_bin,
        "-i", stream_url,
        "-c", "copy",
        "-t", str(duration),
        "-y",
        str(output_file)
    ]
    # 后台启动录制进程
    proc = subprocess.Popen(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    return proc


def monitor_live_stream(
    url: str,
    output_dir: str = None,
    watch_duration: int = 600,
    clip_len: float = 30.0,
    spike_multiplier: float = 2.2,
    auto_transcribe: bool = True
) -> Dict:
    """
    全自动盯盘与爆款切片主入口
    """
    url_info = parse_url_info(url)
    if not url_info['valid']:
        raise ValueError(f"不支持的 URL: {url}")

    platform = url_info['platform']
    base_dir = ensure_directory(Path(output_dir) if output_dir else Path.cwd() / "hype-clips" / time.strftime("%Y%m%d_%H%M%S"))
    session_video = base_dir / "full_session.mp4"

    print("=" * 65)
    print("🔥 启动直播流高光与爆款实时监测系统 (Live Hype Monitor)")
    print(f"   目标平台: {platform.upper()}")
    print(f"   URL: {url}")
    print(f"   监控时长: {watch_duration} 秒 ({seconds_to_time(watch_duration)})")
    print(f"   单段剪辑时长: {clip_len} 秒")
    print(f"   高潮判定敏感度: {spike_multiplier}x 弹幕爆发")
    print(f"   输出目录: {base_dir}")
    print("=" * 65)

    print("\n🔍 正在解析直播流与聊天室通道...")
    meta = resolve_stream_url_and_meta(url)
    stream_url = meta.get('stream_url')
    if not stream_url:
        raise RuntimeError("无法提取直播视频流地址")

    print(f"   主播: {meta['uploader']}")
    print(f"   标题: {meta['title']}")

    # 初始化 HypeDetector
    detector = HypeDetector(
        window_seconds=8.0,
        spike_multiplier=spike_multiplier,
        min_velocity=1.2,
        cooldown_seconds=35.0,
        clip_duration=clip_len
    )

    detected_spikes = []

    def on_chat_message(msg: ChatMessage):
        moment = detector.add_message(msg.timestamp, msg.text, msg.author)
        if moment:
            detected_spikes.append(moment)
            kws = ", ".join(moment['top_keywords']) or "弹幕刷屏"
            print(f"\n🚨 [高潮爆发] 触发时间: {seconds_to_time(moment['peak_time'])} | 速率: {moment['velocity']}条/秒 | 关键词: [{kws}]")

    # 启动录制
    print(f"\n📹 启动流录制...")
    start_time = time.time()
    record_proc = start_stream_recorder(stream_url, session_video, watch_duration)

    # 启动对应平台聊天监听器
    chat_listener = None
    if platform == "twitch":
        channel_name = url.split("twitch.tv/")[-1].split("/")[0]
        chat_listener = TwitchChatListener(channel_name, on_chat_message)
    elif platform == "kick":
        channel_name = url.split("kick.com/")[-1].split("/")[0].split("?")[0]
        chat_listener = KickChatListener(channel_name, on_chat_message)
    elif platform == "youtube":
        chat_listener = YouTubeChatListener(meta['id'], on_chat_message)

    chat_thread = None
    if chat_listener:
        chat_thread = threading.Thread(target=chat_listener.start, args=(start_time,), daemon=True)
        chat_thread.start()
        print(f"💬 实时聊天监控连接成功 ({platform.upper()} Chat Engine Active)")

    print(f"\n👀 正在实时盯盘中... (按 Ctrl+C 可提前结算已捕获的高光)")

    try:
        while time.time() - start_time < watch_duration:
            elapsed = time.time() - start_time
            remaining = watch_duration - elapsed
            # 动态刷新控制台状态
            sys.stdout.write(f"\r⏳ 已监控: {seconds_to_time(elapsed)} / {seconds_to_time(watch_duration)} | 捕获高光数: {len(detected_spikes)} 个 | 剩余: {int(remaining)}s ")
            sys.stdout.flush()
            time.sleep(1.0)
    except KeyboardInterrupt:
        print("\n\n⏹️ 接收到用户中断，开始结算已捕获的高光...")
    finally:
        # 停止录制与聊天
        if chat_listener:
            chat_listener.stop()
        if record_proc and record_proc.poll() is None:
            record_proc.terminate()
            try:
                record_proc.wait(timeout=5)
            except Exception:
                record_proc.kill()

    print("\n\n✅ 盯盘录制阶段完成！")
    time.sleep(2.0)  # 等待文件写入刷盘

    if not session_video.exists() or session_video.stat().st_size == 0:
        print("⚠️ 未能录制到完整视频流文件")
        return {"clips": [], "report": None}

    actual_size = session_video.stat().st_size
    print(f"📦 完整录播文件: {session_video.name} ({format_file_size(actual_size)})")
    print(f"🎯 共检测到 {len(detected_spikes)} 段弹幕爆发瞬间！开始智能提取与爆款评估...")

    if not detected_spikes:
        print("ℹ️ 本次监控期间未检测到剧烈弹幕高潮。")
        return {"clips": [], "report": None}

    # 切割并转录每一个高光片段
    candidates = []
    transcribe_func = None
    if auto_transcribe:
        try:
            from transcribe_audio import transcribe_video_or_audio
            transcribe_func = transcribe_video_or_audio
        except Exception:
            pass

    for idx, moment in enumerate(detected_spikes, 1):
        s_time = moment['start_time']
        e_time = moment['end_time']
        kws_tag = "_".join(moment['top_keywords'][:2]) if moment['top_keywords'] else "spike"
        clip_name = f"clip_{idx:02d}_{int(s_time)}s_{kws_tag}.mp4"
        clip_path = base_dir / clip_name

        print(f"\n✂️  [{idx}/{len(detected_spikes)}] 正在剪辑高光: {seconds_to_time(s_time)} -> {seconds_to_time(e_time)}")
        try:
            clip_video(str(session_video), s_time, e_time, str(clip_path))

            # 语音转录
            transcript = ""
            if transcribe_func and clip_path.exists():
                try:
                    srt_out = clip_path.with_suffix(".srt")
                    t_res = transcribe_func(str(clip_path), str(srt_out), model_size="base")
                    with open(srt_out, "r", encoding="utf-8") as f:
                        lines = [l.strip() for l in f.readlines() if l.strip() and not l.strip().isdigit() and "-->" not in l]
                        transcript = " ".join(lines)
                except Exception as te:
                    print(f"   ⚠️ 转录略过: {te}")

            candidates.append({
                "clip_path": str(clip_path),
                "moment": moment,
                "transcript": transcript
            })
        except Exception as ce:
            print(f"   ❌ 剪辑失败: {ce}")

    # 进行爆款潜力计算与排序
    report_file = base_dir / "VIRAL_RANKING_REPORT.md"
    ranked_results = rank_and_report_clips(candidates, str(report_file))

    return {
        "clips": ranked_results,
        "report_path": str(report_file),
        "output_dir": str(base_dir)
    }


def main():
    parser = argparse.ArgumentParser(description="直播流实时盯盘与 30 秒爆款切片系统")
    parser.add_argument("url", help="直播流 URL (YouTube / Twitch / Kick)")
    parser.add_argument("output_dir", nargs="?", default=None, help="输出目录")
    parser.add_argument("--duration", type=int, default=600, help="监控时长(秒)，默认 600 秒 (10 分钟)")
    parser.add_argument("--clip-len", type=float, default=30.0, help="单段剪辑时长(秒)，默认 30 秒")
    parser.add_argument("--sensitivity", type=float, default=2.2, help="高潮判定敏感度(爆发倍数)，默认 2.2")
    parser.add_argument("--no-transcribe", action="store_true", help="跳过自动语音转录")

    args = parser.parse_args()

    try:
        monitor_live_stream(
            url=args.url,
            output_dir=args.output_dir,
            watch_duration=args.duration,
            clip_len=args.clip_len,
            spike_multiplier=args.sensitivity,
            auto_transcribe=not args.no_transcribe
        )
    except Exception as e:
        print(f"\n❌ 错误: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
