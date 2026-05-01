---
name: xiaopang-video-transcript
description: 统一视频字幕提取工具，支持 YouTube、Bilibili、抖音(Douyin) 平台。自动识别视频平台，优先获取官方字幕，失败时自动使用 Whisper AI 语音识别生成字幕。Use when user asks to "提取字幕", "视频字幕", "transcript", "subtitle", "get transcript", "download subtitle", "字幕提取", or provides a video URL and wants the transcript/subtitle text extracted.
version: 3.0.0
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

1. **平台识别** - 自动识别 YouTube、Bilibili、抖音(Douyin) 平台
2. **官方字幕优先** - 尝试获取官方提供的字幕
   - **Bilibili**: 优先通过 CDP（浏览器自动化）获取，利用用户 Chrome 登录态，无需处理 WBI 签名；CDP 不可用时降级到直接 API 调用
   - **YouTube**: 使用 InnerTube API 获取
   - **抖音**: 无官方字幕，直接进入 Whisper AI 流程
3. **Whisper AI 兜底** - 如果没有官方字幕，使用 AI 语音识别生成
4. **转录稿清洗** - 对 Whisper 原始输出进行去重降噪、结构化整理（详见下方"转录稿清洗工作流"）

## 脚本位置

`{baseDir}` = this SKILL.md's directory path

| Script | Purpose |
|--------|---------|
| `scripts/main.ts` | 主脚本 (统一入口) |
| `scripts/youtube.ts` | YouTube 专用脚本 (来自 baoyu-skills) |
| `scripts/whisper_transcribe.py` | Whisper AI 语音识别 |
| `prompts/speaker-transcript.md` | 说话人识别 prompt 模板 |
| `prompts/transcript-cleanup.md` | Whisper 转录稿清洗 prompt 模板（去重、降噪、结构化） |

## 使用方法

```bash
# 基本用法 - 自动检测平台，优先官方字幕
${BUN_X} {baseDir}/scripts/main.ts <video-url>

# B站视频
${BUN_X} {baseDir}/scripts/main.ts "https://www.bilibili.com/video/BV1xx411c7mD"
${BUN_X} {baseDir}/scripts/main.ts BV1xx411c7mD

# YouTube 视频 (自动使用 youtube.ts 脚本)
${BUN_X} {baseDir}/scripts/main.ts "https://www.youtube.com/watch?v=xxx"

# 抖音视频 (自动通过 CDP 提取视频 + Whisper 转写)
${BUN_X} {baseDir}/scripts/main.ts "https://v.douyin.com/xxxxx/"
${BUN_X} {baseDir}/scripts/main.ts "https://www.douyin.com/video/7616962174283484426"

# 强制使用 Whisper AI（跳过官方字幕）
${BUN_X} {baseDir}/scripts/main.ts <url> --whisper

# 指定 Whisper 模型（抖音建议 medium）
${BUN_X} {baseDir}/scripts/main.ts "https://v.douyin.com/xxxxx/" --whisper-model medium

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

## 转录稿清洗工作流

Whisper AI 输出的原始转录稿通常包含大量噪声（重复短语、乱码段、繁体中文）。转录完成后自动执行清洗：

### 触发条件
- **自动触发**：Whisper 转写完成后（抖音视频、无官方字幕时的兜底路径）
- **手动触发**：用户提供已有的 Whisper 转录稿并要求"整理"、"去重"、"清洗"

### 清洗步骤
1. **读取 prompt** — `{baseDir}/prompts/transcript-cleanup.md`
2. **去重降噪** — 移除 ASR 重复片段（连续相同短语保留一次）、倒计时/调试噪声、乱码段
3. **繁转简** — Whisper 对中文视频常输出繁体，统一转换为简体
4. **说话人识别** — 从内容推断主持人/嘉宾，标注 `**姓名:**` 格式
5. **结构化** — 按主题分章节（`### [MM:SS] 标题`），整理为 Q&A 对话格式
6. **输出** — 替换原始转录稿，保留 frontmatter 元数据

### 典型压缩比
1700 行原始 Whisper 输出 → 300-400 行清洗后的结构化文字稿

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

| 平台 | 官方字幕 | Whisper AI | 章节分割 | 说话人识别 | 备注 |
|------|----------|------------|----------|------------|------|
| YouTube | ✓ | ✓ | ✓ | ✓ | InnerTube API |
| Bilibili | ✓ | ✓ | - | - | CDP 优先 |
| 抖音(Douyin) | - | ✓ | - | - | CDP 提取视频 + Whisper |
| 小宇宙(Xiaoyuzhou) | - | ✓ | - | - | CDP 提取音频 + Whisper |
| 喜马拉雅(Ximalaya) | - | ✓ | - | - | CDP 提取音频 + Whisper |

## 依赖

- **bun** - TypeScript 运行时
- **yt-dlp** - 下载音频（Whisper 需要）
- **ffmpeg** - 音频格式转换（Whisper 需要）
- **faster-whisper** - AI 语音识别（首次使用时自动安装）

## Bilibili 字幕获取策略

采用三级降级策略：

| 优先级 | 方式 | 说明 |
|--------|------|------|
| 1 | CDP 浏览器模式 | 通过 web-access 的 CDP Proxy 在用户 Chrome 中打开视频页面，利用登录态直接调用 player API。**无需处理 WBI 签名和 Cookie** |
| 2 | 直接 API 调用 | 通过 Node.js 直接调用 Bilibili API（可能在签名验证、登录态方面受限） |
| 3 | Whisper AI | 下载音频后使用 AI 语音识别生成字幕 |

CDP 模式需要 Chrome 开启远程调试（`chrome://inspect/#remote-debugging` 勾选 Allow），CDP Proxy 自动运行于 `localhost:3456`。

## 抖音字幕获取策略

抖音没有官方字幕 API，且 yt-dlp 的抖音提取器有 bug（需要 fresh cookies）。采用 CDP 直取方案：

| 步骤 | 方式 | 说明 |
|------|------|------|
| 1 | CDP 打开页面 | 通过 web-access 的 CDP Proxy 在用户 Chrome 中打开抖音页面 |
| 2 | 提取视频 URL | 从 `video.currentSrc` 获取 CDN 地址（有时效性） |
| 3 | 立即下载 | 带 `Referer: https://www.douyin.com/` 头下载视频 |
| 4 | ffmpeg 提取音频 | 转 WAV 16kHz mono |
| 5 | Whisper 转写 | faster-whisper 本地转写（建议 medium 模型） |

**注意**：抖音视频 URL 有时效性（约几分钟），提取后必须立即下载。CDP 模式需要 Chrome 开启远程调试。

## 注意事项

- **URL 需要单引号** — zsh 会把 `?` 当作通配符，所以需要用单引号包裹 URL：`'https://www.youtube.com/watch?v=xxx'`
- 官方字幕获取速度快且准确
- Bilibili 字幕获取优先使用 CDP 模式（需要 Chrome 开启远程调试）
- Whisper AI 需要下载音频并进行语音识别，耗时较长
- 对于中文视频，默认 `--language zh` 效果最佳
- YouTube 默认启用章节分割（`--chapters`）
- **抖音视频需要 CDP** — Chrome 必须开启远程调试，CDP Proxy 运行于 `localhost:3456`
- **抖音视频建议 `--whisper-model medium`** — small 模型对中文口语准确度较低
- **抖音视频耗时长** — CDP 提取 + 下载 + Whisper 转写，27 分钟视频约需 10-15 分钟

## 集成说明

本 skill 可由 `clip-and-process` 自动调用。当用户提供视频/音频 URL 时，路由器会自动识别并调用本 skill 提取文字稿。

**输出格式**：Markdown 文字稿 + 元数据（标题、作者、时长、平台）。路由器会将输出保存到 `剪藏/` 目录。

**本 skill 只负责提取文字稿**，不保存到剪藏、不翻译、不做深度处理。
