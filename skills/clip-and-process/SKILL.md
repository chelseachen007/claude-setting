---
name: clip-and-process
description: >
  剪藏工作流唯一入口 + 智能路由器。自动识别内容类型（视频/音频/网页/英文），
  内置网页提取能力（三层降级策略），分发到对应 worker 提取内容，
  自动翻译英文，保存到剪藏，可选深度处理。
  触发词：剪藏、clip、保存链接、保存这篇文章、提取内容、抓取文章、读取网页内容。
  当用户提供 URL、视频链接或本地媒体文件时触发。
---

# Clip and Process — 智能剪藏路由器

## 铁律

1. **绝不编造内容。** 必须从实际来源获取内容。所有提取方式都失败时，立即告知用户手动粘贴，不生成替代内容。
2. **图片一律走 PicGo 上传到 OSS，不落本地附件。** 剪藏的配图不进 `附件/`，见 Step 3.5。用户已知偏好，不需要每次询问。

## 职责

本 skill 是剪藏工作流的**唯一入口和智能路由器**：

1. **识别内容类型** → 路由到正确的 worker 或内联提取
2. **检测语言** → 英文内容自动翻译
3. **保存到剪藏** → 标准化文件格式
4. **可选深度处理** → 调用 clip-process

## 触发条件

- "剪藏" / "clip" + URL
- "保存这个链接/文章"
- "提取内容" / "抓取文章" / "读取网页内容" + URL
- 用户直接发 URL（根据上下文判断）
- 用户发本地媒体文件路径（.mp4/.mp3/.wav/.m4a/.ogg/.flac/.aac/.opus/.m4b）
- 用户发本地文档文件路径（.pdf/.epub/.docx/.pptx/.xlsx）
- 用户发本地图片文件路径（.jpg/.jpeg/.png/.gif/.webp）
- "剪藏并处理" + URL → 全流程（含深度处理）
- "处理剪藏" → 直接调用 clip-process（跳过提取）

## 渐进式加载

策略文件存放在本 skill 的子目录中，按需 Read 加载：

| 文件 | 何时加载 |
|------|---------|
| `strategies/platform-xhs.md` | 小红书 URL |
| `strategies/platform-bilibili.md` | B站 URL |
| `strategies/platform-douyin.md` | 抖音 URL |
| `strategies/platform-youtube.md` | YouTube URL |
| `strategies/platform-twitter.md` | X/Twitter URL |
| `strategies/platform-wechat.md` | 微信公众号 URL（直接 CDP） |
| `strategies/layer1-direct-fetch.md` | 通用网页 URL，尝试直取 |
| `strategies/layer1.5-paywall-bypass.md` | Layer 1 检测到付费墙信号 |
| `strategies/layer2-cdp.md` | Layer 1 失败，需浏览器自动化 |
| `strategies/layer3-cache-mirror.md` | Layer 1 + Layer 2 都失败 |
| `templates/clipping-file.md` | Step 3 保存文件时 |

## Step 0：URL 预处理

**短链接解析**：对短链接（xhslink.com、b23.tv、v.douyin.com、t.cn 等），先用 CDP 打开获取重定向后的完整 URL，再进入 Step 1。

## Step 1：平台识别 + 内容类型路由

### 1.1 平台识别

根据解析后的 URL 识别平台：

| URL 模式 | 平台 | 策略文件 |
|----------|------|---------|
| `xiaohongshu.com`、`xhslink.com` | 小红书 | `platform-xhs.md` |
| `bilibili.com`、`b23.tv`、`BV*` | B站 | `platform-bilibili.md` |
| `douyin.com`、`v.douyin.com` | 抖音 | `platform-douyin.md` |
| `youtube.com`、`youtu.be` | YouTube | `platform-youtube.md` |
| `x.com`、`twitter.com` | X/Twitter | `platform-twitter.md` |
| `mp.weixin.qq.com` | 微信公众号 | `platform-wechat.md`（直接 CDP） |
| `feishu.cn`、`my.feishu.cn` | 飞书 | 内联：lark-mcp（见下方） |
| **其他所有 URL** | 通用网页 | 三层降级（见下方） |

**非 URL 输入**：

| 输入类型 | 路由 |
|----------|------|
| 本地 `.pdf/.epub/.docx/.pptx/.xlsx` | `document-extractor` |
| 本地 `.jpg/.jpeg/.png/.gif/.webp` | 内联：图片 OCR（见下方） |
| 本地 `.mp4/.wav/.m4a/.mp3/.ogg/.flac/.aac/.opus/.m4b` | `xiaopang-video-transcript` |

### 1.2 内容类型预判（URL 级别）

部分平台 URL 可预判内容类型，用于加速路由（CDP 后再确认）：

| 平台 | URL 预判规则 | 备注 |
|------|-------------|------|
| B站 | `/video/` → 视频，`/read/` → 文章 | 可靠 |
| 抖音 | `/video/` → 视频，`/note/` → 图文 | 可靠 |
| YouTube | 所有 URL → 视频 | 可靠 |
| 微信公众号 | 所有 URL → 文章 | 可靠 |
| 小红书 | 无法预判 | CDP 检测 |
| X/Twitter | 无法预判 | CDP 检测 |

### 1.3 加载平台策略 + 提取素材

**有平台策略的 URL**：Read 对应 `strategies/platform-*.md`，按策略文件执行提取。

每个平台策略文件内包含：
- **内容类型检测**：CDP 打开后从 DOM 确认内容类型（纯文本 / 图文 / 视频 / 混合）
- **文本提取**：标题、正文、元数据的 CSS 选择器
- **图文提取**：图片选择器 + OCR 规则
- **视频提取**：视频元素选择器 + 字幕/转录流程
- **已知陷阱**

**提取顺序**：文本 → 图片（OCR）→ 视频（字幕优先 → Whisper 兜底）

**通用网页 URL**（无平台策略）：三层降级提取

1. **Layer 1**：Read `strategies/layer1-direct-fetch.md`，用 web_reader 直取
2. **Layer 1.5**（如检测到付费墙）：Read `strategies/layer1.5-paywall-bypass.md`
3. **Layer 2**（Layer 1 失败）：Read `strategies/layer2-cdp.md`，CDP 浏览器自动化
4. **Layer 3**（Layer 2 也失败）：Read `strategies/layer3-cache-mirror.md`

### 视频转录流程（所有平台通用）

```
检测到视频内容
  ↓
Step A: 平台有字幕 API？（YouTube/B站）
  ├─ 是 → 尝试获取官方字幕（快速、准确）
  │       ├─ 成功 → 使用字幕
  │       └─ 失败 → Step B
  └─ 否 → Step B
  ↓
Step B: Whisper 转录
  ├─ 下载视频（或从 CDP 获取 URL 后下载）
  ├─ ffmpeg 抽音频（`ffmpeg -i video.mp4 -vn -acodec pcm_s16le -ar 16000 -ac 1 audio.wav`）
  └─ mlx_whisper 转录（`mlx_whisper audio.wav --language zh --model mlx-community/whisper-large-v3-turbo --output-format txt --output-dir /tmp/`）
  ↓
Step C: 失败降级
  └─ 保存已有文本内容 + 标注"视频转录失败" + 提示用户手动补充
```

**用户可跳过转录**：如果用户说"不要转录"或"只要文本"，跳过 Step A/B。

### 飞书文档提取

检测到 `feishu.cn` / `my.feishu.cn` URL 时，使用 lark-mcp 直接提取：

1. **解析 URL 路径**，判断文档类型：
   - `/docx/` → 飞书文档
   - `/wiki/` → 飞书 Wiki
   - `/base/` → 飞书多维表格
2. **提取内容**：
   - 飞书文档：`mcp__lark-mcp__docx_v1_document_rawContent`（path.document_id = URL 中 docx 后的 token，useUAT=true）
   - 飞书 Wiki：先 `mcp__lark-mcp__wiki_v2_space_getNode`（params.token = wiki token, useUAT=true）获取 `obj_token`，再调 `docx_v1_document_rawContent`
   - 多维表格：`mcp__lark-mcp__bitable_v1_appTableField_list` 获取字段定义 + `mcp__lark-mcp__bitable_v1_appTableRecord_search` 获取记录，格式化为 Markdown 表格
3. **元数据**：标题从文档属性或 URL 推断，`source: 飞书文档/飞书Wiki/飞书多维表格`

### 文档文件提取

检测到本地 `.pdf/.epub/.docx/.pptx/.xlsx` 文件时，调用 `document-extractor` skill：

```bash
python3 -m markitdown "{文件路径}"
```

对于 PDF：如果 markitdown 输出文字很少（<200 字，疑似扫描件），触发 OCR 兜底：
- 用 `mcp__4_5v_mcp__analyze_image` 逐页分析图片提取文字

### 图片文字提取

适用于所有需要从图片提取文字的场景（本地图片文件、帖子图片、PDF 扫描件等）。

调用 `mcp__zai-mcp-server__analyze_image` 或 `mcp__4_5v_mcp__analyze_image`：
- Prompt："请完整提取这张图片中的所有中文文字内容，逐字转录，不要遗漏任何文字。表格→Markdown 表格。列表→保留列表结构。"

**批量图片**（多图帖子等）：逐张提取，通过 src 去重后按图号顺序合并。

**本地图片文件** `.jpg/.jpeg/.png/.gif/.webp`：同样适用此流程。元数据：文件名，`type: image-post`

**OCR 核心原则：逐字完整，不做概括、不写摘要、不删减长文。**

### 提取失败

告知用户失败原因，建议手动粘贴内容。不继续后续步骤。

## Step 2：语言检测与翻译

提取成功后，检测内容语言：

### 英文检测规则

1. **域名启发**（优先）：以下域名大概率是英文内容：
   - `medium.com`、`substack.com`、`*.dev`、`*.io`
   - `github.com`（README/博客）
   - `*.medium.com`、`blog.*`
   - 英文媒体域名（`nytimes.com`、`bbc.com`、`wired.com` 等）

2. **内容采样**（确认）：取前 200 词，英文词占比 > 60% → 确认英文

### 翻译流程

确认英文后，调用 `baoyu-translate` skill 翻译全文。

**双语保存格式**：
```markdown
## 原文

[英文原文内容]

## 译文

[中文翻译内容]
```

非英文内容跳过此步骤。

## Step 3：保存到剪藏

将内容保存到 Obsidian vault 剪藏目录。

**文件路径**：`<Obsidian库>/剪藏/{文件名}.md`

Read `templates/clipping-file.md` 获取完整的 frontmatter 格式和内容结构模板。

## Step 3.5：图片上传（PicGo → OSS）

**剪藏的图片不保存到本地附件目录，一律先转 PNG，再上传到阿里云 OSS，正文里写远程链接。**

留本地副本的话，120 篇剪藏就是几千张图进 vault，`附件/` 会迅速膨胀，Git 同步也扛不住；远程链接只占一行文字。

### 流程

1. **改成有辨识度的文件名**：`{文章短名}-{序号}.png`（如 `fde说明书-01.png`）。PicGo 默认直接用文件名当 OSS key，不重命名的话 `img-01.png` 会互相覆盖。
2. **webp → png**：Obsidian 渲染 webp 不稳定，先转：
   ```bash
   sips -s format png "src.webp" --out "fde说明书-01.png"
   ```
3. **上传**（本 skill 自带 helper，内部用 PicGo.app 内置的 picgo core）：
   ```bash
   node ~/.agents/skills/clip-and-process/helpers/picgo-upload.cjs fde说明书-01.png fde说明书-02.png ...
   ```
   - stdout 每行 `文件名\tURL`，最后一行是 JSON 数组；退出码 0 = 全部成功
   - 首次运行会 `npx @electron/asar` 解开 `PicGo.app`，之后复用 `/tmp/picgo-asar` 缓存
   - 配置读 `~/.picgo/config.json`（当前是阿里云 OSS，桶 `chelsechen-img`）
4. **写进正文**：用带尖括号的链接，避免 URL 里的特殊字符打断 Markdown：
   ```markdown
   ![](<https://chelsechen-img.oss-cn-hangzhou.aliyuncs.com/fde说明书-01.png>)
   ```
5. **清掉本地临时文件**：上传成功后删除本地的 png/webp 与临时目录，不留副本。删除前先核对解析后的绝对路径，只删本次生成的图片。

### 失败处理

- 上传失败（退出码 1、URL 为空）→ **重试一次**；仍失败就保留本地图并在正文标注 `<!-- 图片上传失败：文件名 -->`，明确告诉用户哪几张需要手动补，**不要静默省略图片**。
- 用户明确说「先存本地」时才落 `附件/剪藏/{文章名}/`，并按 `![[附件/...]]` 嵌入。

## Step 4：询问是否深度处理

保存成功后，使用 AskUserQuestion 询问用户：

> 已剪藏到 `剪藏/{文件名}.md`。要深度处理吗？（入库思考 + 常青笔记 + 卡片连接 + 行动项）

**用户选择"是"** → 继续 Step 5（入库思考）→ Step 6（深度处理）

**用户选择"否"** → 返回简要报告，结束。

**用户说"剪藏并处理"** → 直接跳到 Step 5，不询问。

## Step 5：入库思考（强制）

**这一步是强制的，不能跳过。不完成不入库。**

使用 AskUserQuestion 工具向用户提问：

> 你已经看过这篇文章并决定剪藏，说明它触动了你。请回答：
>
> 1. **最打动你的一点是什么？**（一个具体的点，不是"都挺好的"）
> 2. **跟你当下在思考/做的事情有什么关系？**（或者：为什么是现在剪藏它？）

将用户的回答用 Edit 工具写入文件的 `## 入库思考` 章节，格式：

```markdown
> [!thought] YYYY-MM-DD
> **打动点**：[用户的回答 1]
> **当下关联**：[用户的回答 2]
```

**只有完成这一步，才继续深度处理。如果用户跳过，剪藏已保存但不会进行深度处理。**

## Step 6：深度处理

调用 `clip-process` skill 的逻辑执行深度处理：

1. 读取剪藏文件内容，以入库思考为锚点
2. 搜索 `卡片/` 目录中的关联卡片（核心关键词 → 主题扩展 → 验证）
3. 生成常青笔记（1-3 条）、连接（已有卡片 3-12 条 + 可建新卡片 2-6 条）、行动（1-3 条）
4. 用 Edit 工具写入文件对应章节
5. 更新 frontmatter：`状态/未整理` → `状态/已整理`，更新 `lastmod`

## Step 6.3：素材库建议

如果深度处理中发现以下内容，建议用户加入素材库：
- 独特洞察或可引用的金句 → "要不要加入素材库？"
- 与用户经历高度相关的内容 → "这段跟你的经历很像，要记到素材库吗？"

用户同意后，将内容追加到 `private/🎭 小胖素材库.md` 对应分类。

## Step 6.5：深度追问（必选）

深度处理完成后，基于文章核心观点和入库思考，向用户提出 **3 个诱人深思的问题**。

**问题设计原则**：
- 不是考理解，是引申——从文章观点延伸到用户自身情境
- 每个问题都包含一个假设或张力，让人不得不选边站
- 避免泛泛而谈，要尖锐到能触发真实的自我审视
- 可以质疑文章观点，不必全盘认同
- **尽量有一个问题与「已有卡片连接」中的某张卡片产生呼应**，让新旧知识碰撞。但不用强求，宁缺毋滥

**提出问题后**，等待用户回答。用户回答后：
1. 用 Edit 工具将问答写入文件的 `## 闪念` 章节，格式：

```markdown
> [!thought] YYYY-MM-DD 深度追问后的思考
> **Q1：[问题1]**
> **A1：[用户回答]**
> **Q2：[问题2]**
> **A2：[用户回答]**
> **Q3：[问题3]**
> **A3：[用户回答]**
```

2. 对每个回答给出 1-2 句回应——补充视角、指出盲点、或延伸到下一步行动

## Step 7：返回结果

向用户报告完整结果：

```
剪藏完成

内容：[标题]
来源：[平台名]
保存：剪藏/[文件名].md
类型：[文章/视频/图文]
语言：[中文/英文（已翻译）]

深度处理：
  常青笔记：X 条
  已有卡片连接：X 个
  建议新卡片：X 个
  行动项：X 个
```

## 错误处理

| 阶段 | 失败处理 |
|------|---------|
| 类型识别失败 | 询问用户内容类型 |
| 短链接解析失败 | 尝试 CDP 解析，仍失败则告知用户 |
| 内容提取失败 | 告知原因，建议手动粘贴 |
| 视频下载失败 | 保存已有文本 + 标注"视频转录失败" + 提示用户 |
| 视频转录失败 | 保存已有文本 + 标注"视频转录失败" + 提示用户 |
| 翻译失败 | 保存英文原文，标注"翻译失败" |
| 剪藏保存失败 | 检查 vault 路径 |
| 深度处理失败 | 剪藏已保存，提示用户稍后 `/clip-process` |

## 配置

- **Obsidian Vault**：`~/Documents/study/github/Obsidian/`
- **剪藏目录**：`剪藏/`
- **卡片目录**：`卡片/`

## 与其他 Skill 的关系

| Skill | 关系 | 本 skill 调用时机 |
|-------|------|-----------------|
| `xiaopang-video-transcript` | 视频字幕/转录 worker | Step 1：视频/音频 URL + 本地音视频文件 |
| `baoyu-translate` | 翻译 worker | Step 2：检测到英文内容 |
| `clip-process` | 深度处理 worker | Step 6：用户选择深度处理 |
| `web-access` | CDP 浏览器自动化 | Step 0：短链接解析 + Step 1：平台页面访问 + Layer 2 |
| `document-extractor` | 文档格式提取 worker | Step 1：PDF/EPUB/DOCX/PPTX/XLSX 文件 |
| `lark-mcp` | 飞书文档读取 | Step 1：飞书文档/Wiki/多维表格 URL |
| `analyze_image` (MCP) | 图片 OCR | Step 1：帖子图片 + 本地图片文件 + PDF 扫描件 |
