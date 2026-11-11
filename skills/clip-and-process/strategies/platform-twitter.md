# X/Twitter 提取策略

## 平台特征

- **URL 格式**：`x.com/{user}/status/{id}`、`twitter.com/{user}/status/{id}`
- **反爬严格**：web_reader 被 ban（error 1214），Jina 对推文返回空
- **内容类型**：纯文本 / 图文（含图片） / 视频 / 线程（多推文串）

## URL 预判

X/Twitter URL **无法从 URL 预判内容类型**，必须 CDP 打开后从 DOM 检测。

## 内容类型检测

CDP 打开后检测：

```javascript
JSON.stringify({
  hasVideo: !!document.querySelector("video"),
  hasImages: !!document.querySelector("img[alt='图片'], [data-testid='tweetPhoto'] img"),
  isThread: document.querySelectorAll('[data-testid="tweet"]').length > 1,
})
```

## 提取级联（按顺序尝试，成功即停）

### 1. CDP 浏览器（最可靠）

1. 加载 `web-access` skill，检查 CDP 可用性
2. `/new` 打开推文 URL
3. 滚动加载完整线程
4. 提取每条推文容器内容
5. `/close` 关闭 tab

### 2. web_reader（可能被 ban）

`mcp__web_reader__webReader` — 单条推文可能成功（大概率被 ban）。

### 3. Jina Reader（线程可能有效）

`https://r.jina.ai/{URL}` — Jina 内置 Twitter 解析器（推文大概率空，线程可能有效）。

## 文本提取

```javascript
// 提取线程中每条推文
JSON.stringify(
  Array.from(document.querySelectorAll('[data-testid="tweet"]')).map(tweet => ({
    text: tweet.querySelector('[data-testid="tweetText"]')?.innerText || "",
    author: tweet.querySelector('[data-testid="User-Name"]')?.innerText || "",
    time: tweet.querySelector("time")?.getAttribute("datetime") || "",
  }))
)
```

## 图片提取

```javascript
Array.from(document.querySelectorAll('[data-testid="tweetPhoto"] img')).map(img => img.src)
```

下载后 OCR 处理。

## 视频提取

```javascript
document.querySelector("video")?.src || document.querySelector("video source")?.src
```

视频下载后走 whisper 转录。Twitter/X 没有字幕 API。

## 线程内容格式

```markdown
**[@username](profile_url)** · 时间
推文内容

---
**[@username2]** · 时间
回复内容
```

## 全部失败

三种方式都失败时告知用户：
> 无法从该推文提取内容。请手动打开链接，复制正文内容粘贴给我，我会帮你处理。

## 输出

- **type 字段**：`type: article`（统一用 article，内容里标注含图片/视频）
