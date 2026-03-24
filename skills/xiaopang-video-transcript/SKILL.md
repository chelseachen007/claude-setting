---
name: xiaopang-video-transcript
description: 统一视频字幕提取工具，支持 YouTube、Bilibili 等平台。自动识别视频平台，优先获取官方字幕，失败时自动使用 Whisper AI 语音识别生成字幕。Use when user asks to "提取字幕", "视频字幕", "transcript", "subtitle", "get transcript", "download subtitle", "字幕提取", or provides a YouTube/Bilibili video URL and wants the transcript/subtitle text extracted.
version: 2.0.0
metadata:
  openclaw:
    requires:
      anyBins:
        - bun
        - npx
---

# 统一视频字幕提取工具

自动识别视频平台，智能选择最佳字幕获取方式。YouTube 使用 baoyu-youtube-transcript 脚本，支持章节分割和说话人识别。

## 工作流程

1. **平台识别** - 自动识别 YouTube、Bilibili 等平台
2. **官方字幕优先** - 尝试获取官方提供的字幕
3. **Whisper AI 兜底** - 如果没有官方字幕，使用 AI 语音识别生成

## 脚本位置

`{baseDir}` = this SKILL.md's directory path

| Script | Purpose |
|--------|---------|
| `scripts/main.ts` | 主脚本 (统一入口) |
| `scripts/youtube.ts` | YouTube 专用脚本 (来自 baoyu-skills) |
| `scripts/whisper_transcribe.py` | Whisper AI 语音识别 |
| `prompts/speaker-transcript.md` | 说话人识别 prompt 模板 |

## 使用方法

```bash
# 基本用法 - 自动检测平台，优先官方字幕
${BUN_X} {baseDir}/scripts/main.ts <video-url>

# B站视频
${BUN_X} {baseDir}/scripts/main.ts "https://www.bilibili.com/video/BV1xx411c7mD"
${BUN_X} {baseDir}/scripts/main.ts BV1xx411c7mD

# YouTube 视频 (自动使用 youtube.ts 脚本)
${BUN_X} {baseDir}/scripts/main.ts "https://www.youtube.com/watch?v=xxx"

# 强制使用 Whisper AI（跳过官方字幕）
${BUN_X} {baseDir}/scripts/main.ts <url> --whisper

# 指定 Whisper 模型
${BUN_X} {baseDir}/scripts/main.ts <url> --whisper --whisper-model medium

# SRT 格式输出
${BUN_X} {baseDir}/scripts/main.ts <url> --format srt

# JSON 格式（原始数据）
${BUN_X} {baseDir}/scripts/main.ts <url> --format json
```

### YouTube 专用功能

```bash
# 直接使用 YouTube 脚本 (更多功能)
${BUN_X} {baseDir}/scripts/youtube.ts <url>

# 列出可用字幕
${BUN_X} {baseDir}/scripts/youtube.ts <url> --list

# 指定语言优先级
${BUN_X} {baseDir}/scripts/youtube.ts <url> --languages zh,en,ja

# 翻译字幕
${BUN_X} {baseDir}/scripts/youtube.ts <url> --translate zh-Hans

# 章节分割
${BUN_X} {baseDir}/scripts/youtube.ts <url> --chapters

# 说话人识别模式 (输出原始数据供 AI 处理)
${BUN_X} {baseDir}/scripts/youtube.ts <url> --speakers

# 组合使用
${BUN_X} {baseDir}/scripts/youtube.ts <url> --chapters --speakers
```

## 参数说明

### 主脚本 (main.ts)

| 参数 | 描述 | 默认值 |
|------|------|--------|
| `<url>` | 视频 URL 或 ID | 必需 |
| `--format` | 输出格式: text, srt, json | text |
| `--output` `-o` | 输出文件路径 | 自动生成 |
| `--output-dir` | 输出目录 | video-transcript |
| `--no-timestamps` | 不包含时间戳 | |
| `--no-chapters` | 不进行章节分割 (仅 YouTube) | |
| `--speakers` | 说话人识别模式 (仅 YouTube) | |
| `--refresh` | 强制重新获取 | |
| `--whisper` | 强制使用 Whisper AI | |
| `--whisper-model` | Whisper 模型: tiny, base, small, medium, large | small |
| `--language` `-l` | 音频语言 | zh |

### YouTube 脚本 (youtube.ts)

| 参数 | 描述 | 默认值 |
|------|------|--------|
| `--languages <codes>` | 语言代码，逗号分隔，按优先级排序 | zh,en |
| `--format <fmt>` | 输出格式: text, srt | text |
| `--translate <code>` | 翻译到指定语言 | |
| `--list` | 列出可用字幕 | |
| `--timestamps` | 包含时间戳 | 开启 |
| `--no-timestamps` | 禁用时间戳 | |
| `--chapters` | 章节分割 | 开启 |
| `--no-chapters` | 禁用章节分割 | |
| `--speakers` | 说话人识别模式 | |
| `--exclude-generated` | 排除自动生成字幕 | |
| `--exclude-manually-created` | 排除人工字幕 | |
| `--refresh` | 强制重新获取 | |
| `-o, --output <path>` | 保存到指定文件 | |
| `--output-dir <dir>` | 基础输出目录 | youtube-transcript |

## 说话人识别工作流

当使用 `--speakers` 参数时：

1. 脚本输出原始文件，包含 YAML frontmatter 和 SRT 格式字幕
2. 读取 `{baseDir}/prompts/speaker-transcript.md` prompt 模板
3. 使用 AI 处理原始文件，识别说话人并分割章节
4. 输出最终的字幕文件

## Whisper 模型选择

| 模型 | 速度 | 准确度 | 推荐场景 |
|------|------|--------|----------|
| tiny | 最快 | 一般 | 快速预览 |
| base | 快 | 较好 | 日常使用 |
| small | 中等 | 好 | **推荐** |
| medium | 较慢 | 很好 | 高质量需求 |
| large | 最慢 | 最好 | 最高质量 |

## 输出目录结构

### YouTube (youtube-transcript/)
```
youtube-transcript/
├── .index.json                          # Video ID → 目录映射 (缓存查找)
└── {channel-slug}/{title-full-slug}/
    ├── meta.json                        # 视频元数据 (标题、频道、描述、时长、章节等)
    ├── transcript-raw.json              # 原始字幕片段 (缓存)
    ├── transcript-sentences.json        # 句子分割后的字幕
    ├── imgs/
    │   └── cover.jpg                    # 视频封面
    ├── transcript.md                    # Markdown 字幕
    └── transcript.srt                   # SRT 字幕 (如果指定 --format srt)
```

### Bilibili / Whisper (video-transcript/)
```
video-transcript/
└── {author}/{title}/
    ├── transcript.md        # Markdown 格式
    ├── transcript.srt       # SRT 格式
    ├── transcript.json      # 原始数据
    └── meta.json            # 视频元数据
```

## 缓存机制

YouTube 字幕首次获取时会缓存：
- `meta.json` — 视频元数据、章节、封面路径、语言信息
- `transcript-raw.json` — YouTube API 返回的原始字幕片段
- `transcript-sentences.json` — 按句子分割的字幕
- `imgs/cover.jpg` — 视频封面

后续运行相同视频会使用缓存数据（无需网络请求）。使用 `--refresh` 强制重新获取。如果请求不同语言，缓存会自动刷新。

## 支持的平台

| 平台 | 官方字幕 | Whisper AI | 章节分割 | 说话人识别 |
|------|----------|------------|----------|------------|
| YouTube | ✓ | ✓ | ✓ | ✓ |
| Bilibili | ✓ | ✓ | - | - |

## 依赖

- **bun** - TypeScript 运行时
- **yt-dlp** - 下载音频（Whisper 需要）
- **ffmpeg** - 音频格式转换（Whisper 需要）
- **faster-whisper** - AI 语音识别（首次使用时自动安装）

## 注意事项

- **URL 需要单引号** — zsh 会把 `?` 当作通配符，所以需要用单引号包裹 URL：`'https://www.youtube.com/watch?v=xxx'`
- 官方字幕获取速度快且准确
- Whisper AI 需要下载音频并进行语音识别，耗时较长
- 对于中文视频，默认 `--language zh` 效果最佳
- YouTube 默认启用章节分割（`--chapters`）
