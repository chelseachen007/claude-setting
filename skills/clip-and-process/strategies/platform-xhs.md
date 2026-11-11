# 小红书（XHS）提取策略

## 平台特征

- **URL 格式**：`/explore/{noteId}?xsec_token=...&xsec_source=...`
- **短链接**：`xhslink.com/*` → 重定向到完整 URL（需 CDP 解析）
- **反爬极严格**：web_reader / curl / 静态抓取全部失败，必须 CDP 直连用户 Chrome
- **xsec_token 必需**：缺失返回 300031 错误（"当前笔记暂时无法浏览"），已登录也不例外
- **内容类型**：纯文本 / 图文 / 视频 / 混合（视频+补充图），所有类型共存于同一 URL 格式

## URL 预判

XHS URL **无法从 URL 预判内容类型**，必须 CDP 打开后从 DOM 检测。

## 内容类型检测

CDP 打开帖子页面后，检测 DOM 元素判断内容类型：

```javascript
JSON.stringify({
  hasVideo: !!document.querySelector("video"),
  hasImages: !!document.querySelector(".swiper-slide img"),
  imageCount: document.querySelectorAll(".swiper-slide img").length,
})
```

- `hasVideo: true` → **视频类型**（可能同时有图片）
- `hasVideo: false && hasImages: true` → **图文类型**
- `hasVideo: false && hasImages: false` → **纯文本**

## 文本提取（所有类型通用）

```javascript
JSON.stringify({
  title: document.querySelector("#detail-title")?.innerText,
  desc: document.querySelector("#detail-desc")?.innerText,
  author: document.querySelector(".author-wrapper .username, .user-nickname, .nickname")?.innerText,
  likes: document.querySelector(".like-wrapper .count, .engage-bar .like-count")?.innerText,
  url: location.href,
})
```

注意：`#detail-desc` innerText 已包含完整文本，无需点击展开按钮。

## 图文提取

1. 提取图片 URL：`.swiper-slide img`（注意首尾 swiper 可能有重复，通过 src 去重）
2. 滚动触发懒加载：`/scroll` 到底部确保所有图片加载完成
3. 下载图片到 `/tmp/`
4. 用 `mcp__zai-mcp-server__analyze_image` 或 `mcp__4_5v_mcp__analyze_image` 逐张识别
   - Prompt："请完整提取这张图片中的所有中文文字内容，逐字转录，不要遗漏任何文字。表格→Markdown 表格。列表→保留列表结构。"
5. 合并结果，追加到 `### 图片内容（OCR）` 章节

**OCR 核心原则：逐字完整，不做概括、不写摘要。**

**注意**：正文末尾常见"字数限制接图X"，正文延续到图片中，必须做 OCR。

## 视频提取

### 1. 获取视频 URL

```javascript
JSON.stringify({
  videoSrc: document.querySelector("video source, video")?.src,
})
```

### 2. 字幕检测

XHS 没有公开字幕 API，**直接走 Whisper 转录**，无需尝试字幕。

### 3. 下载视频

```bash
curl -sL -o /tmp/xhs_video_{noteId}.mp4 "{videoSrc}"
```

注意：CDN URL 含 sign 和时间戳参数，有时效性，提取后立即下载。

### 4. 转录

调用 `xiaopang-video-transcript` 处理本地文件：

```bash
bun ~/ai/skills/xiaopang-video-transcript/scripts/fetch.ts '/tmp/xhs_video_{noteId}.mp4' --out /tmp/xvt/{job}
```

如果 xiaopang 不支持本地文件，手动走 whisper 流水线：
1. `ffmpeg -i video.mp4 -vn -acodec pcm_s16le -ar 16000 -ac 1 audio.wav`
2. `mlx_whisper audio.wav --language zh --model mlx-community/whisper-large-v3-turbo --output-format txt --output-dir /tmp/`

### 5. 失败降级

视频下载或转录失败时：保存已有文本内容，标注"视频转录失败"，提示用户手动补充。

## 混合内容（视频 + 图片）

视频帖可能同时携带补充图片。处理方式：
1. 视频走转录流程
2. 图片走 OCR 流程
3. 所有素材合并到同一个剪藏文件

## 已知陷阱

- swiper-slide 首尾图片经常重复（同一 src），提取时需通过 src 去重
- 图片 URL 为 CDN 临时链接，含时间戳前缀，可能有时效性
- 正文中的"接图X"表示内容延续到图片中，纯文本提取会丢失内容
- 帖子访问必须带 xsec_token，缺失会返回错误
- XHS 内部 API 需要 X-s/X-t 签名头，直接 fetch 会被拦截

## 输出

- **type 字段**：`type: xhs-post`（不区分子类型）
