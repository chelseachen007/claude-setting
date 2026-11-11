# Layer 1.5：付费墙绕过

Layer 1 返回内容疑似付费墙时触发。

## 付费墙检测信号

- 中文："会员专享"、"付费内容"、"购买后查看"、"登录后查看全文"、"订阅后继续阅读"、"VIP 专属"
- 英文："paywall"、"subscribe to continue"、"premium content"、"members only"、"sign in to read"
- 内容过短（<300 字）且以"登录"/"订阅"/"购买"结尾

## 绕过级联

按顺序尝试，成功即停：

| 级别 | 方法 | 说明 |
|------|------|------|
| 1 | Jina Reader：`https://r.jina.ai/{URL}` | Jina 内置反付费墙处理 |
| 2 | Googlebot UA 模拟 | 用 curl 加 `-H "User-Agent: Googlebot"` 请求，提取 `<article>` 标签内容 |
| 3 | JSON-LD 提取 | curl 页面 HTML，解析 `<script type="application/ld+json">` 中的 `articleBody` 字段 |
| 4 | AMP 版本 | 将 URL 中的域名后加 `/amp` 或搜索 `{URL} AMP` 获取 AMP 版本 |
| 5 | archive.today | `https://archive.today/newest/{URL}` |
| 6 | Google Cache | WebSearch 搜索 `cache:{URL}` |

## 绕过后验证

提取内容 > 500 字且不含付费墙信号 → 成功，进入内容清洗。

## 验证失败

转入 Layer 2（`layer2-cdp.md`）。
