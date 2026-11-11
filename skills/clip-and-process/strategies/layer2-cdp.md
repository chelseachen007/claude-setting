# Layer 2：浏览器自动化（web-access CDP）

Layer 1 失败时，使用 CDP 浏览器模式访问页面。

## 前置条件

CDP Proxy 由全局 web-access skill 提供，启动脚本：

```bash
node "${HOME}/.agents/skills/web-access/scripts/check-deps.mjs"
```

首次调用输出 `proxy: ready` 后，后续复用同一 proxy 实例（端口 3456）。

## 适用场景

- 需要登录态的内容（知乎、小红书）
- JS 动态渲染的页面（百度百家号、bestblogs.dev）
- 反爬机制较强的平台
- Layer 1 + Layer 1.5 都失败的通用兜底

**注意**：微信公众号（mp.weixin.qq.com）已在平台识别阶段直接路由到 CDP，不经过本层。

## 操作要点

1. 运行 `check-deps.mjs` 确保 CDP Proxy 就绪
2. 创建新 tab：`curl -s "http://localhost:3456/new?url=<URL>"`
3. 确认加载：`curl -s "http://localhost:3456/info?target=<ID>"`
4. 用 `/eval` 提取正文内容（优先 `article`、`.article-content`、`#content`、`<main>` 等语义容器）
5. 如遇"阅读全文"按钮，用 `/click` 点击展开
6. 提取完成后 `/close` 关闭 tab

## bestblogs.dev 特殊处理

Next.js 渲染，Layer 1 只能拿到 meta。CDP 提取 `<main>` 元素可获取完整转录稿/文章内容。

## 提取后清洗

同 Layer 1 清洗规则：去除噪声，保留结构、图片和元数据。
