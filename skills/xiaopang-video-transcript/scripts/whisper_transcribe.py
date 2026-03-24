#!/usr/bin/env python3
"""
Whisper AI 语音识别字幕生成
供 main.ts 调用的独立脚本
"""

import argparse
import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path


def download_audio(url: str, output_path: str) -> str:
    """使用 yt-dlp 下载音频"""
    audio_file = os.path.join(output_path, "audio.m4a")

    cmd = [
        "yt-dlp",
        "-f", "bestaudio[ext=m4a]/bestaudio",
        "-o", audio_file,
        "--no-playlist",
        "--no-warnings",
        url
    ]

    print("下载音频中...", file=sys.stderr)
    result = subprocess.run(cmd, capture_output=True, text=True)

    if result.returncode != 0:
        raise Exception(f"下载音频失败: {result.stderr}")

    return audio_file


def convert_to_wav(audio_file: str, wav_file: str) -> str:
    """转换为 WAV 格式"""
    cmd = [
        "ffmpeg", "-y", "-i", audio_file,
        "-ar", "16000",
        "-ac", "1",
        "-c:a", "pcm_s16le",
        wav_file
    ]

    print("转换音频格式中...", file=sys.stderr)
    result = subprocess.run(cmd, capture_output=True, text=True)

    if result.returncode != 0:
        raise Exception(f"转换音频失败: {result.stderr}")

    return wav_file


def transcribe_with_whisper(audio_file: str, model_name: str = "small", language: str = "zh") -> list:
    """使用 faster-whisper 进行语音识别"""
    try:
        from faster_whisper import WhisperModel
    except ImportError:
        print("正在安装 faster-whisper...", file=sys.stderr)
        subprocess.run([sys.executable, "-m", "pip", "install", "faster-whisper", "-q"])
        from faster_whisper import WhisperModel

    print(f"加载 Whisper 模型 ({model_name})...", file=sys.stderr)
    model = WhisperModel(model_name, device="cpu", compute_type="int8")

    print("语音识别中...", file=sys.stderr)
    segments, info = model.transcribe(audio_file, language=language)

    results = []
    for segment in segments:
        results.append({
            "start": segment.start,
            "end": segment.end,
            "text": segment.text.strip()
        })

    print(f"识别完成，检测语言: {info.language} (概率: {info.language_probability:.2%})", file=sys.stderr)
    return results


def main():
    parser = argparse.ArgumentParser(description="Whisper AI 语音识别")
    parser.add_argument("url", help="视频 URL")
    parser.add_argument("--model", default="small", choices=["tiny", "base", "small", "medium", "large"])
    parser.add_argument("--language", "-l", default="zh")
    parser.add_argument("--output-dir", default=None)
    parser.add_argument("--format", choices=["json", "srt"], default="json")

    args = parser.parse_args()

    # 创建临时目录
    output_dir = args.output_dir or tempfile.mkdtemp()
    os.makedirs(output_dir, exist_ok=True)

    audio_file = None
    wav_file = None

    try:
        # 下载音频
        audio_file = download_audio(args.url, output_dir)

        # 转换格式
        wav_file = os.path.join(output_dir, "audio.wav")
        convert_to_wav(audio_file, wav_file)

        # 语音识别
        segments = transcribe_with_whisper(wav_file, args.model, args.language)

        # 输出到 stdout (JSON 格式)
        print(json.dumps(segments, ensure_ascii=False))

    finally:
        # 清理临时文件
        if audio_file and os.path.exists(audio_file):
            os.remove(audio_file)
        if wav_file and os.path.exists(wav_file):
            os.remove(wav_file)


if __name__ == "__main__":
    main()
