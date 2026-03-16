---
name: xiaoyuzhou-podcast
description: |
  小宇宙播客转文字工具. 下载小宇宙播客单集并使用Groq Whisper转录为文字.
  当用户需要将播客转换为文字时触发. 关键词: 小宇宙、播客、podcast、播客转录、音频转文字.
version: 1.0.0
metadata:
  openclaw:
    requires:
      bins:
        - python3
        - uv
        - ffmpeg
      emoji: "\U0001F3A4"
      os:
        - darwin
        - linux
---

# 小宇宙播客转文字

你是"小宇宙播客转录助手"。帮助用户将小宇宙播客单集转换为文字稿。

## 功能特点

- **高质量转录** — 使用 Groq Whisper large-v3 模型
- **自动下载** — 自动解析并下载播客音频
- **Markdown 输出** — 结构化的文字稿，含元数据
- **可选保留音频** — 支持保留下载的音频文件

## 环境要求

- Python 3.10+
- uv 包管理器
- ffmpeg: `brew install ffmpeg`
- Groq API Key (免费)

## 配置 Groq API Key

1. 访问 https://console.groq.com
2. 用 Google/GitHub 账号登录
3. 左侧菜单 → API Keys → Create API Key
4. 设置环境变量:

```bash
export GROQ_API_KEY="gsk_xxxxx"
```

## 使用方法

### 转录播客

```bash
cd ~/.claude/commands/xiaoyuzhou-podcast && uv run scripts/xiaoyuzhou_transcriber.py "https://www.xiaoyuzhoufm.com/episode/EPISODE_ID"
```

### 保存音频文件

```bash
cd ~/.claude/commands/xiaoyuzhou-podcast && uv run scripts/xiaoyuzhou_transcriber.py "https://www.xiaoyuzhoufm.com/episode/EPISODE_ID" --save-audio
```

### 指定输出目录

```bash
cd ~/.claude/commands/xiaoyuzhou-podcast && uv run scripts/xiaoyuzhou_transcriber.py "https://www.xiaoyuzhoufm.com/episode/EPISODE_ID" --output ./output
```

## CLI 参数

| 参数 | 说明 | 默认值 |
|------|------|--------|
| `url` | 小宇宙播客单集链接 | 必填 |
| `--output, -o` | 输出目录 | /tmp |
| `--save-audio` | 保存音频文件 | false |
| `--api-key` | Groq API Key | 从环境变量读取 |

## 输出结构

```
/tmp/
└── EPISODE_ID/
    ├── transcript.md      # Markdown 格式文字稿
    └── audio.mp3          # 下载的音频文件 (--save-audio 时)
```

## 输出字段

| 字段 | 说明 |
|------|------|
| success | 是否成功 |
| episode_id | 单集 ID |
| title | 单集标题 |
| transcript_path | 转录文件路径 |
| audio_path | 音频文件路径 (如有) |

## 免费额度

- Groq API 每小时约 2 小时音频 (7200 秒)
- 超出后等 15 分钟自动恢复
- 日常听几期播客完全够用

## 注意事项

- 转录质量高 (Whisper large-v3)
- 不区分说话人
- 2 小时以上的播客建议分批处理

## 失败处理

- **ffmpeg not found**: 安装 ffmpeg: `brew install ffmpeg`
- **API Key 无效**: 检查 GROQ_API_KEY 环境变量是否正确
- **转录失败**: 检查网络连接，播客链接是否有效
- **音频下载失败**: 某些播客可能有访问限制
