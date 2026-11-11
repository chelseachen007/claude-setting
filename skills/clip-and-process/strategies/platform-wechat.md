# 微信公众号（mp.weixin.qq.com）平台策略

## 平台特征

- 反爬极严格，静态抓取（WebFetch / Jina / curl）几乎必然触发「环境异常」验证码
- **直接走 CDP，跳过 Layer 1**
- 内容类型：纯文章（无视频/图文混合），单页完整加载

## CDP 提取流程

### 1. 启动 CDP Proxy

```bash
node "${HOME}/.agents/skills/web-access/scripts/check-deps.mjs"
```

首次调用输出 `proxy: ready` 后，后续复用同一 proxy 实例。

### 2. 打开页面

```bash
curl -s "http://localhost:3456/new?url=<URL>"
```

返回 `{"targetId":"<ID>"}`，后续操作用此 ID。

### 3. 等待加载 + 确认标题

```bash
curl -s "http://localhost:3456/info?target=<ID>"
```

确认 `title` 不为空且不含「环境异常」。若标题异常，等待 2 秒重试一次。

### 4. 提取正文

```bash
curl -s -X POST "http://localhost:3456/eval?target=<ID>" -d 'document.querySelector("#js_content").innerText'
```

CSS 选择器优先级：
1. `#js_content` — 标准微信文章正文容器
2. `.rich_media_content` — 部分老版本模板
3. `article` — 兜底

### 5. 提取元数据

```bash
# 作者/公众号名
curl -s -X POST "http://localhost:3456/eval?target=<ID>" -d 'document.querySelector("#js_name")?.innerText || document.querySelector(".profile_nickname")?.innerText || ""'

# 发布时间（从 script 标签中提取，格式不固定）
curl -s -X POST "http://localhost:3456/eval?target=<ID>" -d 'document.querySelector("#publish_time")?.innerText || ""'
```

### 6. 关闭 tab

```bash
curl -s "http://localhost:3456/close?target=<ID>"
```

## 已知陷阱

- **验证码拦截**：如果 `info` 返回的 title 包含「环境异常」，说明 CDP 未连接到正确的 Chrome 实例（需用户在 Chrome 地址栏打开 `chrome://inspect/#remote-debugging` 并勾选允许远程调试）
- **长文截断**：微信文章可能有「阅读全文」按钮，但 CDP 的 `innerText` 通常能获取完整内容。若内容明显截断（<500字），尝试 `scroll` 到底部后重新提取
- **图片**：正文中的图片 URL 在 `data-src` 属性而非 `src`，如需提取图片，用 `document.querySelectorAll("#js_content img").forEach(i => i.src = i.dataset.src || i.src)` 先激活
