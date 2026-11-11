# YouTube 提取策略

## 平台特征

- **URL 格式**：`youtube.com/watch?v=*`、`youtu.be/*`、`youtube.com/shorts/*`、`youtube.com/embed/*`
- **反爬中等**：字幕 API 公开可用，yt-dlp 支持良好
- **内容类型**：几乎全是视频（Shorts 也是视频）
- **需要代理**：终端需要手动 export 代理环境变量

## URL 预判

所有 YouTube URL 都是视频类型，无需 DOM 确认。

## 视频提取

### 1. 字幕优先

YouTube 有完善的字幕系统（手动 + 自动生成），优先使用：

```bash
export https_proxy=http://127.0.0.1:7890 http_proxy=http://127.0.0.1:7890 all_proxy=socks5://127.0.0.1:7890
bun ~/ai/skills/xiaopang-video-transcript/scripts/fetch.ts '<URL>' --lang zh --out /tmp/xvt/{job}
```

- `fetch.ts` 内部优先官方/自动字幕，语言顺序 `zh* → en* → all`，无需手写 `zh-CN`
- 统一输出 `segments.json` / `transcript.txt` / `transcript.srt` / `meta.json`

### 2. Whisper 兜底

无字幕时自动降级到 whisper 转录（xiaopang 内置处理）。

### 3. 失败降级

字幕和转录都失败 → 尝试 CDP 打开页面获取标题和描述，标注"视频转录失败"。

## 已知陷阱

- **终端代理**：系统代理只在浏览器生效，终端需手动 export 代理环境变量
- **语言代码**：YouTube 字幕语言代码是 `zh-CN`/`en-US`，不是 `zh`/`en`
- 自动生成字幕质量参差不齐，中文内容可能有较多错误

## 输出

- **type 字段**：`type: video`
