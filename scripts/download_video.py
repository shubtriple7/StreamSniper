#!/usr/bin/env python3
"""
跨平台视频与直播下载工具
支持: YouTube (视频/直播/Shorts), Twitch (直播/VOD/Clips), Kick (直播/VOD/Clips)
具备直播限时捕获、YouTube DVR 回溯、缺少字幕时自动 Whisper 语音转录功能
"""

import sys
import os
import json
import argparse
from pathlib import Path

try:
    import yt_dlp
except ImportError:
    print("❌ Error: yt-dlp not installed")
    print("Please install: pip install yt-dlp")
    sys.exit(1)

from utils import (
    validate_url,
    parse_url_info,
    sanitize_filename,
    format_file_size,
    get_video_duration_display,
    ensure_directory
)


def download_video(
    url: str,
    output_dir: str = None,
    duration: int = None,
    live_from_start: bool = False,
    auto_transcribe: bool = True,
    transcribe_model: str = "base"
) -> dict:
    """
    下载视频或录制直播流，并获取/生成字幕

    Args:
        url: 视频或直播 URL (YouTube, Twitch, Kick)
        output_dir: 输出目录，默认为当前目录
        duration: 直播录制时长（秒）。对于正在进行的直播，若未指定则默认 300 秒 (5分钟)
        live_from_start: YouTube 直播是否从头开始录制 (DVR)
        auto_transcribe: 若无官方字幕，是否使用 Whisper 自动转录
        transcribe_model: Whisper 模型大小 ('tiny', 'base', 'small', 'medium')

    Returns:
        dict: {
            'video_path': 视频文件路径,
            'subtitle_path': 字幕文件路径,
            'title': 标题,
            'duration': 时长（秒）,
            'file_size': 大小（字节）,
            'platform': 平台,
            'is_live': 是否为直播
        }
    """
    url_info = parse_url_info(url)
    if not url_info['valid']:
        raise ValueError(f"Unsupported or invalid URL: {url}")

    if output_dir is None:
        output_dir = Path.cwd()
    else:
        output_dir = Path(output_dir)

    output_dir = ensure_directory(output_dir)

    print(f"🎬 准备下载/捕获...")
    print(f"   URL: {url}")
    print(f"   平台: {url_info['platform'].upper()}")
    print(f"   输出目录: {output_dir}")

    # 预探测视频/直播信息
    probe_opts = {
        'quiet': True,
        'no_warnings': True,
        'skip_download': True,
        'js_runtimes': {'node': {}}
    }

    with yt_dlp.YoutubeDL(probe_opts) as ydl:
        try:
            print("\n📊 正在解析媒体信息...")
            info = ydl.extract_info(url, download=False)
        except Exception as e:
            raise RuntimeError(f"获取媒体信息失败: {e}")

    title = info.get('title', 'Unknown')
    video_id = info.get('id', 'unknown')
    raw_duration = info.get('duration') or 0
    is_live = info.get('is_live', False) or info.get('live_status') == 'is_live'

    print(f"   标题: {title}")
    print(f"   状态: {'🔴 直播中 (Live Stream)' if is_live else '📹 视频/录播 (VOD)'}")
    if raw_duration:
        print(f"   时长: {get_video_duration_display(raw_duration)}")

    # 配置正式下载参数
    ydl_opts = {
        # 优先 1080p，兼顾各类 HLS 流和直链
        'format': 'bestvideo[height<=1080][ext=mp4]+bestaudio[ext=m4a]/best[height<=1080][ext=mp4]/bestvideo+bestaudio/best',
        'merge_output_format': 'mp4',
        'outtmpl': str(output_dir / '%(id)s.%(ext)s'),
        'writesubtitles': True,
        'writeautomaticsub': True,
        'subtitleslangs': ['en'],
        'subtitlesformat': 'vtt/srt/best',
        'writethumbnail': False,
        'quiet': False,
        'no_warnings': False,
        'progress_hooks': [_progress_hook],
        'js_runtimes': {'node': {}}
    }

    # 处理直播流参数
    if is_live:
        if live_from_start:
            print("   ⏩ 启用 live-from-start (从直播开头开始抓取)")
            ydl_opts['live_from_start'] = True

        # 设置直播录制时长
        record_seconds = duration if duration is not None else 300
        print(f"   ⏱️ 直播录制时长限制: {record_seconds} 秒 ({get_video_duration_display(record_seconds)})")
        ydl_opts['external_downloader'] = {'default': 'ffmpeg'}
        ydl_opts['external_downloader_args'] = {'ffmpeg_i': ['-t', str(record_seconds)]}

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            print(f"\n📥 开始下载/录制...")
            download_info = ydl.extract_info(url, download=True)
            video_filename = ydl.prepare_filename(download_info)
            video_path = Path(video_filename)

            # 如果转成了 mp4，确保获取真实存在的文件
            if not video_path.exists():
                mp4_cand = video_path.with_suffix('.mp4')
                if mp4_cand.exists():
                    video_path = mp4_cand

            if not video_path.exists():
                # 模糊匹配以 video_id 开头的视频文件
                candidates = list(output_dir.glob(f"{video_id}.*"))
                candidates = [c for c in candidates if c.suffix.lower() in ['.mp4', '.mkv', '.webm', '.ts']]
                if candidates:
                    video_path = candidates[0]
                else:
                    raise FileNotFoundError(f"Video file not found after download: {video_path}")

            file_size = video_path.stat().st_size if video_path.exists() else 0
            print(f"\n✅ 媒体文件就绪: {video_path.name}")
            print(f"   大小: {format_file_size(file_size)}")

            # 寻找已下载的字幕
            subtitle_path = None
            for ext in ['.en.vtt', '.vtt', '.en.srt', '.srt']:
                sub_cand = video_path.with_suffix(ext)
                if not sub_cand.exists():
                    sub_cand = video_path.parent / f"{video_path.stem}{ext}"
                if sub_cand.exists():
                    subtitle_path = sub_cand
                    break

            if subtitle_path and subtitle_path.exists():
                print(f"✅ 获取到平台字幕: {subtitle_path.name}")
            else:
                print(f"⚠️  未检测到平台字幕 (Twitch / Kick / 无字幕直播)")
                if auto_transcribe:
                    print(f"🎙️  自动启动 Faster-Whisper 语音识别生成字幕...")
                    try:
                        # 动态导入转录模块
                        from transcribe_audio import transcribe_video_or_audio
                        trans_res = transcribe_video_or_audio(
                            str(video_path),
                            model_size=transcribe_model,
                            output_format="srt"
                        )
                        subtitle_path = Path(trans_res['subtitle_path'])
                        print(f"✅ AI 语音转录字幕就绪: {subtitle_path.name}")
                    except Exception as te:
                        print(f"❌ 自动转录失败: {te}")
                        subtitle_path = None

            return {
                'video_path': str(video_path),
                'subtitle_path': str(subtitle_path) if subtitle_path else None,
                'title': title,
                'duration': raw_duration or (duration or 0),
                'file_size': file_size,
                'video_id': video_id,
                'platform': url_info['platform'],
                'is_live': is_live
            }

    except Exception as e:
        print(f"\n❌ 下载/录制失败: {str(e)}")
        raise


def _progress_hook(d):
    """下载进度回调"""
    if d['status'] == 'downloading':
        if 'downloaded_bytes' in d and 'total_bytes' in d and d['total_bytes']:
            percent = d['downloaded_bytes'] / d['total_bytes'] * 100
            downloaded = format_file_size(d['downloaded_bytes'])
            total = format_file_size(d['total_bytes'])
            speed = d.get('speed', 0)
            speed_str = format_file_size(speed) + '/s' if speed else 'N/A'
            bar_length = 30
            filled = int(bar_length * percent / 100)
            bar = '█' * filled + '░' * (bar_length - filled)
            print(f"\r   [{bar}] {percent:.1f}% - {downloaded}/{total} - {speed_str}", end='', flush=True)
        elif 'downloaded_bytes' in d:
            downloaded = format_file_size(d['downloaded_bytes'])
            speed = d.get('speed', 0)
            speed_str = format_file_size(speed) + '/s' if speed else 'N/A'
            print(f"\r   下载/录制中... {downloaded} - {speed_str}", end='', flush=True)
    elif d['status'] == 'finished':
        print()


def main():
    parser = argparse.ArgumentParser(description="下载 YouTube / Twitch / Kick 视频或录制直播片段")
    parser.add_argument("url", help="视频或直播 URL")
    parser.add_argument("output_dir", nargs="?", default=None, help="输出目录 (默认当前目录)")
    parser.add_argument("--duration", type=int, default=None, help="直播录制时长(秒)，默认 300 秒")
    parser.add_argument("--live-from-start", action="store_true", help="YouTube 直播是否从头开始录制")
    parser.add_argument("--no-transcribe", action="store_true", help="缺少字幕时不自动进行语音识别")
    parser.add_argument("--model", default="base", help="Whisper 模型大小 (tiny/base/small/medium)")

    args = parser.parse_args()

    try:
        result = download_video(
            url=args.url,
            output_dir=args.output_dir,
            duration=args.duration,
            live_from_start=args.live_from_start,
            auto_transcribe=not args.no_transcribe,
            transcribe_model=args.model
        )

        print("\n" + "="*60)
        print("结果 (JSON):")
        print(json.dumps(result, indent=2, ensure_ascii=False))

    except Exception as e:
        print(f"\n❌ 错误: {str(e)}")
        sys.exit(1)


if __name__ == "__main__":
    main()
