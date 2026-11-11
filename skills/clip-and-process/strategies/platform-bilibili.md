# Bilibili（B站）提取策略

## 平台特征

- **URL 格式**：`bilibili.com/video/BV*`（视频）、`bilibili.com/read/CV*`（专栏文章）
- **短链接**：`b23.tv/*` → 重定向到完整 URL
- **反爬中等**：视频字幕 API 需登录态或 WBI 签名，CDP 模式可绕过
- **内容类型**：视频（主要）、专栏文章、动态（纯文本/图文）

## URL 预判

| URL 模式 | 预判类型 |
|----------|----------|
| `/video/BV*`、`/video/av*`、`BV*` | 视频 |
| `/read/CV*` | 专栏文章 |
| `b23.tv/*` | 需解析短链接后判断 |

## 视频提取

### 1. 字幕优先（推荐）

B站视频可能有 CC 字幕，优先尝试：

```bash
bun ~/ai/skills/xiaopang-video-transcript/scripts/fetch.ts '<BV号或URL>' --out /tmp/xvt/{job}
```

xiaopang-video-transcript 已内置 B站字幕提取逻辑：
- CDP 优先：利用用户 Chrome 登录态获取字幕（无需 WBI 签名）
- API 降级：直接调 B站 API（可能因签名失败）
- Whisper 兜底：无字幕时自动降级到 whisper 转录

### 2. 内容类型确认

通过 CDP 打开视频页面后确认：

```javascript
JSON.stringify({
  hasVideo: !!document.querySelector("video"),
  title: document.querySelector(".video-title, h1.video-title")?.innerText,
  desc: document.querySelector(".desc-info-text, .basic-desc-info")?.innerText,
  author: document.querySelector(".up-info .username, .up-name")?.innerText,
})
```

### 3. 失败降级

字幕获取失败 → 降级到 whisper 转录
whisper 也失败 → 保存标题和描述文本，标注"视频转录失败"

## 专栏文章提取

CDP 打开专栏页面，提取正文：

```javascript
JSON.stringify({
  title: document.querySelector(".title")?.innerText,
  content: document.querySelector(".article-content")?.innerText,
  author: document.querySelector(".up-name")?.innerText,
})
```

也可尝试 web_reader 直取（专栏反爬较弱）。

## 已知陷阱

- B站视频字幕不是所有视频都有，AI 生成字幕也可能不存在
- WBI 签名机制导致直接 API 调用容易失败，CDP 模式更可靠
- 视频页面信息在 `__INITIAL_STATE__` 全局变量中，CDP eval 可直接读取

## 输出

- **视频 type 字段**：`type: video`
- **文章 type 字段**：`type: article`
