#!/usr/bin/env python3
"""
使用 faster-whisper 从视频或音频中提取字幕
适用于没有官方字幕的视频、直播流切片（Twitch / Kick / YouTube Live）
"""

import sys
import os
import shutil
import subprocess
import tempfile
from pathlib import Path
from typing import Optional, List, Dict

try:
    from faster_whisper import WhisperModel
except ImportError:
    print("❌ faster-whisper not installed. Please run: pip install faster-whisper")
    sys.exit(1)


def format_timestamp_srt(seconds: float) -> str:
    """转换为 SRT 时间戳格式 (HH:MM:SS,mmm)"""
    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    secs = seconds % 60
    return f"{hours:02d}:{minutes:02d}:{secs:06.3f}".replace('.', ',')


def format_timestamp_vtt(seconds: float) -> str:
    """转换为 VTT 时间戳格式 (HH:MM:SS.mmm)"""
    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    secs = seconds % 60
    return f"{hours:02d}:{minutes:02d}:{secs:06.3f}"


def extract_audio(video_path: Path, temp_dir: Path) -> Path:
    """使用 FFmpeg 提取 16kHz 单声道音频"""
    audio_path = temp_dir / "extracted_audio.wav"
    ffmpeg_bin = shutil.which("ffmpeg") or "ffmpeg"
    
    cmd = [
        ffmpeg_bin,
        "-i", str(video_path),
        "-vn",
        "-acodec", "pcm_s16le",
        "-ar", "16000",
        "-ac", "1",
        "-y",
        str(audio_path)
    ]
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        raise RuntimeError(f"FFmpeg audio extraction failed:\n{result.stderr}")
    return audio_path


def transcribe_video_or_audio(
    media_path: str,
    output_path: Optional[str] = None,
    model_size: str = "base",
    language: Optional[str] = None,
    output_format: str = "srt"
) -> Dict:
    """
    转录音视频为字幕文件
    
    Args:
        media_path: 媒体文件路径
        output_path: 输出字幕文件路径
        model_size: Whisper 模型大小 ('tiny', 'base', 'small', 'medium')
        language: 指定语言代码 (如 'en', 'zh')，None 为自动检测
        output_format: 'srt' 或 'vtt'
        
    Returns:
        Dict: {'subtitle_path': str, 'language': str, 'segments_count': int}
    """
    media_path = Path(media_path)
    if not media_path.exists():
        raise FileNotFoundError(f"Media file not found: {media_path}")

    if output_path is None:
        ext = ".vtt" if output_format.lower() == "vtt" else ".srt"
        output_path = media_path.with_suffix(ext)
    else:
        output_path = Path(output_path)

    output_path.parent.mkdir(parents=True, exist_ok=True)

    print(f"🎙️  开始语音转录 (Faster-Whisper)...")
    print(f"   输入文件: {media_path.name}")
    print(f"   模型: {model_size}")
    print(f"   语言: {language or '自动检测'}")

    with tempfile.TemporaryDirectory(prefix="whisper_audio_") as temp_dir:
        temp_dir_path = Path(temp_dir)
        is_video = media_path.suffix.lower() in [".mp4", ".mkv", ".webm", ".ts", ".flv", ".mov", ".avi"]
        if is_video:
            print("   正在提取音轨...")
            audio_file = extract_audio(media_path, temp_dir_path)
        else:
            audio_file = media_path

        print(f"   加载模型 [{model_size}]...")
        model = WhisperModel(model_size, device="cpu", compute_type="int8")

        print("   正在识别语音内容...")
        segments_generator, info = model.transcribe(
            str(audio_file),
            beam_size=5,
            language=language
        )

        detected_lang = info.language
        lang_prob = info.language_probability
        print(f"   识别语言: {detected_lang} (置信度: {lang_prob:.2%})")

        segments = list(segments_generator)
        print(f"   识别段落数: {len(segments)}")

        # 写入字幕文件
        is_vtt = output_path.suffix.lower() == ".vtt" or output_format.lower() == "vtt"
        with open(output_path, "w", encoding="utf-8") as f:
            if is_vtt:
                f.write("WEBVTT\n\n")
                for i, seg in enumerate(segments, 1):
                    start_str = format_timestamp_vtt(seg.start)
                    end_str = format_timestamp_vtt(seg.end)
                    text = seg.text.strip()
                    f.write(f"{start_str} --> {end_str}\n{text}\n\n")
            else:
                for i, seg in enumerate(segments, 1):
                    start_str = format_timestamp_srt(seg.start)
                    end_str = format_timestamp_srt(seg.end)
                    text = seg.text.strip()
                    f.write(f"{i}\n{start_str} --> {end_str}\n{text}\n\n")

    print(f"✅ 字幕生成完成: {output_path}")
    return {
        "subtitle_path": str(output_path),
        "language": detected_lang,
        "segments_count": len(segments)
    }


def main():
    if len(sys.argv) < 2:
        print("Usage: python transcribe_audio.py <media_file> [output_file] [model_size] [language]")
        print("\nExamples:")
        print("  python transcribe_audio.py clip.mp4")
        print("  python transcribe_audio.py stream.mp4 stream.srt base en")
        sys.exit(1)

    media_file = sys.argv[1]
    output_file = sys.argv[2] if len(sys.argv) > 2 else None
    model = sys.argv[3] if len(sys.argv) > 3 else "base"
    lang = sys.argv[4] if len(sys.argv) > 4 else None

    try:
        result = transcribe_video_or_audio(media_file, output_file, model_size=model, language=lang)
        print(f"\nResult: {result}")
    except Exception as e:
        print(f"\n❌ 转录失败: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
