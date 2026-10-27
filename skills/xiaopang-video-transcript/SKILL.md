---
name: xiaopang-video-transcript
description: 视频/播客/本地媒体的字幕与逐字稿抓取。B站走 CDP 拿官方字幕，YouTube 走 yt-dlp，抖音/小红书/小宇宙/喜马拉雅拿媒体源后本地 ASR，本地文件直接转写。输出带时间戳的分段文本；ingest.ts 可直接落成 Obsidian 视频学习笔记。不做内容整理。触发词：提取字幕、视频字幕、转录、transcript、subtitle、逐字稿、扒字幕、把这个视频转成文字、视频转笔记。
---

# 视频字幕抓取

**职责边界：只负责拿到干净的带时间戳文本。** 不总结、不整理、不写笔记、不生成文章。
要整理成中文长稿 → 用 `media-transcriber`。要写进库里 → 由上层决定。

## 什么时候用

用户丢来视频/播客链接或本地音视频，要「文字」这件事本身：
扒字幕、转逐字稿、给上游做整理、做说话人转录的原料。

## 一条命令跑完

```bash
bun ~/ai/skills/xiaopang-video-transcript/scripts/fetch.ts <url-or-path> --out <工作目录>
```

上游按规范给 `--out <工作目录>`。省略时自动落到 `/tmp/xvt/<平台>-<时间戳>/`，实际目录看 `meta.json` 所在位置。

支持：B站 `BV…`/`av…`、YouTube、抖音、小红书、小宇宙、喜马拉雅、任意本地音视频。
输出到 `<工作目录>`：

| 文件 | 内容 |
|---|---|
| `segments.json` | `[{start, end, text}]` —— **权威原文，后续一切以它为准** |
| `transcript.txt` | 纯文本，无时间戳 |
| `transcript.srt` | SRT |
| `meta.json` | 平台/标题/作者/时长/语言/来源（official 或 asr）/尝试过的路线 |

然后按需排版：

```bash
bun scripts/render.ts <工作目录>                    # 段落 + [HH:MM:SS → HH:MM:SS]
bun scripts/render.ts <工作目录> --mode speakers    # 加「说话人 N（待核对）」占位
bun scripts/fix_typos.ts <工作目录>                 # 只修 ASR 产物，官方字幕不动
```

## 路线优先级（已内置，不用手选）

1. **B站** → CDP 走页面上下文，自动带 Cookie 和 WBI 签名拿官方字幕，**免登录免下载**
2. **YouTube** → `yt-dlp --write-subs --write-auto-subs`，语言优先级 `zh* → en* → all`
3. **抖音/小红书/小宇宙/喜马拉雅** → CDP 取 `<video>/<audio>` 真实 src（有时效，取到立刻 curl 下载），再本地 ASR
4. **本地文件** → 直接 ASR
5. 以上主路线失败 → 统一降级到 ASR，并把每次失败原因记进 `meta.json.attempts`

强制走 ASR（比如官方字幕明显缺段）：`--force-asr`。
强制指定平台：`--platform bilibili|youtube|douyin|xiaohongshu|podcast|local`。

## ASR 引擎链

`whisperkit`（CoreML，Apple Silicon 最快）→ `mlx-whisper` → `faster-whisper`。失败自动往下掉，全部失败才报错。
模型路径读 `config.json` 的 `whisperkit_model_path`，可 `--model-path` 覆盖。

### 三个已经踩过的坑（改脚本别改回去）

- **`--report-path` 目录必须事先存在**：不存在时 whisperkit-cli 打一行 `Couldn't save report` 但**退出码仍是 0**，看起来成功实则没产物。脚本已预建目录 + 检查产出文件。
- **WhisperKit 的 segment text 带 `<|startoftranscript|><|zh|><|0.00|>` 之类特殊 token**，必须剥掉。
- **YouTube 自动字幕是滚动式的**，同句会重复两三次。`render.ts` 的 `group()` 负责合并，别在原始 segments 上删。

## 前置依赖（缺哪个补哪个）

| 工具 | 用途 | 装法 |
|---|---|---|
| `bun` | 跑脚本 | 已装 |
| CDP Proxy `127.0.0.1:3456` + 已登录 Chrome | B站/抖音/小红书取数据 | 用 `web-access` skill 起 |
| `yt-dlp` | YouTube 字幕 | `brew install yt-dlp` |
| `ffmpeg` | 抽音频 | `brew install ffmpeg` |
| `whisperkit-cli` | 本地 ASR 主引擎 | `brew install whisperkit-cli` |

缺 CDP 时 B站会直接报「需要 CDP」，不会静默降级到 ASR——**因为官方字幕比 ASR 准得多，静默降级是坏体验**。

## 错别字词典

`config/whisper-typo-fixes.json`，143 条，按类别分组（历史人物/地名/军事/金融/时政等），格式 `[["错", "对"], ...]`。
只作用于 `source=asr` 的产物；官方字幕要修必须显式 `--force`。
**词典是长尾资产**：碰到新的口误/人名错识别就往前加。

## 写进 Obsidian（编排层）

`ingest.ts` 把「抓取 → 排版 → 落库」串成一条命令，产出符合库规范的笔记：

```bash
bun ~/ai/skills/xiaopang-video-transcript/scripts/ingest.ts <url-or-path>
bun scripts/ingest.ts <url> --mode summary      # 留章节骨架待 media-transcriber 填正文
bun scripts/ingest.ts --job <已有工作目录>       # 复用抓取产物，不重跑 ASR
bun scripts/ingest.ts <url> --dry-run           # 只看落点和 frontmatter，不写盘
```

落点 `视频学习/{作者} — {标题}.md`，frontmatter 与库里既有笔记逐字符一致：

```yaml
tags:
title: {作者} — {标题}
date: 2026-10-26
lastmod: 2026-10-26
platform: bilibili
url: https://...
author: {作者}
duration: 28:58
source: official        # 官方/AI 字幕 → official；ASR → whisper（沿用库里旧写法）
```

两条硬规则：

- **同名笔记已存在时拒绝写入**，退出码 3，并打印抓取产物位置。要覆盖必须 `--force`。不静默覆盖是底线——库里那些是人工整理过的。
- **`duration` 短于 1 小时补零成 `07:38`，超过 1 小时写成 `4:12:15`**，跟既有笔记一致。

`--mode raw`（默认）是段落 + 段尾 `[HH:MM:SS → HH:MM:SS]`，段长按库里时间戳分布对齐（主力 8–10 秒）。
`--mode summary` 只出章节骨架和约每 4 分钟的锚点，**正文留给 `media-transcriber`**——抓取层冒充整理层正是这次重构要消灭的问题。

## 交给下游

- 整理成中文长稿 → `media-transcriber`（吃 `segments.json` 或 `transcript.txt`）
- 直接落库 → `ingest.ts`（见上）
- 复杂访谈要分人 → 先 `--mode speakers` 出占位，再由上层依据内容判断，**不要凭空猜身份**

## 边界

- 不承诺说话人识别：本地 ASR 没有 diarization，`speakers` 模式只是按停顿打占位，标注「待核对」。
- 不下载整段视频除非需要 ASR；官方字幕路线只拉字幕。
- 抖音/小红书媒体 URL 有时效且需 Referer，不许缓存复用。
- Cookies、签名地址、鉴权参数不进任何交付文本。
