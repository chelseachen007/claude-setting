#!/usr/bin/env python3
# /// script
# requires-python = ">=3.10"
# dependencies = [
#     "groq",
#     "httpx",
#     "beautifulsoup4",
# ]
# ///
"""
小宇宙播客转录工具

下载小宇宙播客单集并使用 Groq Whisper 转录为文字。

使用方法:
    uv run xiaoyuzhou_transcriber.py "https://www.xiaoyuzhoufm.com/episode/EPISODE_ID"
    uv run xiaoyuzhou_transcriber.py "https://www.xiaoyuzhoufm.com/episode/EPISODE_ID" --save-audio --output ./output

环境变量:
    GROQ_API_KEY: Groq API Key (从 https://console.groq.com 获取)
"""

from __future__ import annotations

import argparse
import asyncio
import json
import os
import re
import subprocess
import sys
import tempfile
from datetime import datetime
from pathlib import Path
from typing import Optional

import httpx
from bs4 import BeautifulSoup
from groq import Groq


def get_logger():
    import logging
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(levelname)s - %(message)s"
    )
    return logging.getLogger(__name__)


logger = get_logger()


class XiaoyuzhouTranscriber:
    """小宇宙播客转录器"""

    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or os.environ.get("GROQ_API_KEY")
        if not self.api_key:
            raise ValueError(
                "需要 GROQ_API_KEY 环境变量或 --api-key 参数。\n"
                "从 https://console.groq.com 获取免费 API Key。"
            )
        self.client = Groq(api_key=self.api_key)

    def extract_episode_id(self, url: str) -> str:
        """从 URL 提取 episode ID"""
        match = re.search(r"/episode/([a-zA-Z0-9]+)", url)
        if not match:
            raise ValueError(f"无法从 URL 提取 episode ID: {url}")
        return match.group(1)

    async def get_episode_info(self, url: str) -> dict:
        """获取播客单集信息"""
        headers = {
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        }

        async with httpx.AsyncClient(follow_redirects=True, timeout=30) as client:
            response = await client.get(url, headers=headers)
            response.raise_for_status()

        soup = BeautifulSoup(response.text, "html.parser")

        # 提取标题
        title_tag = soup.find("title")
        title = title_tag.get_text(strip=True) if title_tag else "未知标题"
        # 清理标题（去掉 " - 小宇宙" 后缀）
        title = re.sub(r"\s*[-|]\s*小宇宙\s*$", "", title)

        # 提取音频 URL（从 script 标签中的 JSON）
        audio_url = None
        for script in soup.find_all("script"):
            text = script.string or ""
            if "audioUrl" in text or "audio_url" in text or ".mp3" in text:
                # 尝试提取 mp3 URL
                mp3_match = re.search(r'https://[^\s"\'<>]+\.mp3[^\s"\'<>]*', text)
                if mp3_match:
                    audio_url = mp3_match.group(0).split('"')[0].split("'")[0]
                    break

        # 尝试从 meta 标签获取
        if not audio_url:
            audio_tag = soup.find("meta", property="og:audio")
            if audio_tag and audio_tag.get("content"):
                audio_url = audio_tag["content"]

        # 尝试从 JSON-LD 获取
        if not audio_url:
            for script in soup.find_all("script", type="application/ld+json"):
                try:
                    data = json.loads(script.string)
                    if isinstance(data, dict) and data.get("@type") == "AudioObject":
                        audio_url = data.get("contentUrl")
                        break
                except json.JSONDecodeError:
                    continue

        return {
            "title": title,
            "audio_url": audio_url,
            "episode_id": self.extract_episode_id(url),
            "url": url,
        }

    async def download_audio(
        self, audio_url: str, output_path: Path
    ) -> Path:
        """下载音频文件"""
        output_path.parent.mkdir(parents=True, exist_ok=True)

        logger.info(f"下载音频: {audio_url}")

        async with httpx.AsyncClient(follow_redirects=True, timeout=300) as client:
            response = await client.get(audio_url)
            response.raise_for_status()

            # 确定文件扩展名
            content_type = response.headers.get("content-type", "")
            if "mp3" in content_type or audio_url.endswith(".mp3"):
                ext = ".mp3"
            elif "m4a" in content_type or audio_url.endswith(".m4a"):
                ext = ".m4a"
            elif "wav" in content_type or audio_url.endswith(".wav"):
                ext = ".wav"
            else:
                ext = ".mp3"  # 默认

            audio_path = output_path.with_suffix(ext)

            with open(audio_path, "wb") as f:
                f.write(response.content)

        logger.info(f"音频已保存: {audio_path}")
        return audio_path

    def transcribe_audio(self, audio_path: Path) -> str:
        """使用 Groq Whisper 转录音频"""
        logger.info(f"转录音频: {audio_path}")

        with open(audio_path, "rb") as audio_file:
            transcript = self.client.audio.transcriptions.create(
                file=(audio_path.name, audio_file),
                model="whisper-large-v3",
                language="zh",
                response_format="text",
            )

        logger.info("转录完成")
        return transcript

    def format_transcript(
        self,
        text: str,
        title: str,
        url: str,
        episode_id: str,
    ) -> str:
        """格式化转录结果为 Markdown"""
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        return f"""# {title}

## 元数据

- 来源: [小宇宙]({url})
- Episode ID: {episode_id}
- 转录时间: {now}
- 转录模型: Groq Whisper large-v3

## 转录内容

{text}
"""

    async def transcribe(
        self,
        url: str,
        output_dir: Path,
        save_audio: bool = False,
    ) -> dict:
        """完整转录流程"""
        # 1. 获取播客信息
        logger.info(f"获取播客信息: {url}")
        info = await self.get_episode_info(url)

        if not info["audio_url"]:
            raise ValueError("无法获取音频 URL")

        episode_dir = output_dir / info["episode_id"]
        episode_dir.mkdir(parents=True, exist_ok=True)

        # 2. 下载音频
        audio_path = await self.download_audio(
            info["audio_url"],
            episode_dir / "audio",
        )

        # 3. 转录
        transcript_text = self.transcribe_audio(audio_path)

        # 4. 保存转录结果
        md_content = self.format_transcript(
            transcript_text,
            info["title"],
            url,
            info["episode_id"],
        )

        md_path = episode_dir / "transcript.md"
        md_path.write_text(md_content, encoding="utf-8")
        logger.info(f"转录已保存: {md_path}")

        # 5. 如果不需要保存音频，删除它
        if not save_audio:
            audio_path.unlink(missing_ok=True)
            logger.info("已删除临时音频文件")
        else:
            logger.info(f"音频文件已保留: {audio_path}")

        return {
            "success": True,
            "episode_id": info["episode_id"],
            "title": info["title"],
            "transcript_path": str(md_path),
            "audio_path": str(audio_path) if save_audio else None,
        }


def check_ffmpeg():
    """检查 ffmpeg 是否安装"""
    try:
        subprocess.run(
            ["ffmpeg", "-version"],
            capture_output=True,
            check=True,
        )
        return True
    except (subprocess.CalledProcessError, FileNotFoundError):
        return False


async def main():
    parser = argparse.ArgumentParser(
        description="小宇宙播客转录工具",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
    uv run xiaoyuzhou_transcriber.py "https://www.xiaoyuzhoufm.com/episode/abc123"
    uv run xiaoyuzhou_transcriber.py "https://www.xiaoyuzhoufm.com/episode/abc123" --save-audio --output ./output

环境变量:
    GROQ_API_KEY: Groq API Key (从 https://console.groq.com 获取)
        """
    )
    parser.add_argument(
        "url",
        help="小宇宙播客单集链接"
    )
    parser.add_argument(
        "--output", "-o",
        type=Path,
        default=Path("/tmp"),
        help="输出目录 (默认: /tmp)"
    )
    parser.add_argument(
        "--save-audio",
        action="store_true",
        help="保存音频文件"
    )
    parser.add_argument(
        "--api-key",
        help="Groq API Key (也可通过 GROQ_API_KEY 环境变量设置)"
    )

    args = parser.parse_args()

    # 检查 ffmpeg
    if not check_ffmpeg():
        logger.warning(
            "未找到 ffmpeg，某些功能可能受限。"
            "安装: brew install ffmpeg"
        )

    try:
        transcriber = XiaoyuzhouTranscriber(api_key=args.api_key)
        result = await transcriber.transcribe(
            url=args.url,
            output_dir=args.output,
            save_audio=args.save_audio,
        )
        print(json.dumps(result, ensure_ascii=False, indent=2))
    except Exception as e:
        error_result = {
            "success": False,
            "error": str(e),
        }
        print(json.dumps(error_result, ensure_ascii=False, indent=2))
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
