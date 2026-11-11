# 抖音（Douyin）提取策略

## 平台特征

- **URL 格式**：`douyin.com/video/{videoId}`（视频）、`douyin.com/note/{noteId}`（图文）
- **短链接**：`v.douyin.com/*` → 重定向到完整 URL
- **反爬严格**：yt-dlp 抖音提取器有 bug（需要 fresh cookies），CDP 是唯一可靠方式
- **内容类型**：视频（主要）、图文笔记

## URL 预判

| URL 模式 | 预判类型 |
|----------|----------|
| `/video/` | 视频 |
| `/note/` | 图文笔记 |
| `v.douyin.com/*` | 需解析短链接后判断 |

## 内容类型检测

CDP 打开后从 DOM 确认：

```javascript
JSON.stringify({
  hasVideo: !!document.querySelector("video"),
  hasImages: !!document.querySelectorAll(".swiper-slide img, .image-item img").length,
})
```

## 视频提取

### 1. 字幕检测

抖音没有公开字幕 API，**直接走 Whisper 转录**。

### 2. 通过 CDP 获取视频 URL

```javascript
JSON.stringify({
  videoUrl: document.querySelector("video")?.currentSrc || document.querySelector("video")?.src || "",
  title: document.title.replace(/ - 抖音$/, "").replace(/ - 抖音精选$/, ""),
  author: document.querySelector('.author-card-user-name')?.textContent
         || document.querySelector('[data-e2e="user-info"] h3')?.textContent || "",
})
```

### 3. 下载视频（必须带 Referer）

```bash
curl -L -o /tmp/douyin_video.mp4 \
  -H "Referer: https://www.douyin.com/" \
  -H "User-Agent: Mozilla/5.0 ..." \
  "{videoUrl}"
```

视频 URL 有时效性，提取后立即下载。

### 4. 转录

```bash
bun ~/ai/skills/xiaopang-video-transcript/scripts/fetch.ts '<抖音URL>' --out /tmp/xvt/{job}
```

xiaopang 已内置抖音处理：CDP 提取 → 下载 → ffmpeg 抽音频 → WhisperKit 转录。

### 5. 失败降级

CDP 提取或转录失败 → 保存标题和描述文本，标注"视频转录失败"。

## 图文提取

抖音图文笔记的处理方式与 XHS 图文类似：
1. 提取图片 URL
2. 下载到 `/tmp/`
3. OCR 逐张识别
4. 合并文本

## 已知陷阱

- 视频下载必须带 `Referer: https://www.douyin.com/`，否则 CDN 拒绝
- yt-dlp 抖音提取器不稳定，不要使用
- 视频 URL 有时效性，提取后需立即下载

## 输出

- **type 字段**：`type: video` 或 `type: article`（图文）
