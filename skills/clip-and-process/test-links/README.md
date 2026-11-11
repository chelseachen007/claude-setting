# 剪藏工作流测试链接

每次 skill 迭代后，用这些链接回归测试各平台提取能力。

## 网页提取（clip-and-process Layer 1 - web_reader）

| 平台 | 测试 URL | 验证要点 |
|------|----------|----------|
| 少数派 | `https://sspai.com/post/73136` | 正文完整提取 |
| 36氪 | `https://36kr.com/p/3194280648358534` | 正文完整提取 |
| 豆瓣 | `https://movie.douban.com/subject/35267208/` | 内容完整 |
| 微博（移动版） | `https://m.weibo.cn/status/5121888782559199` | 正文完整 |
| 简书 | `https://www.jianshu.com/p/6695688ad61f` | 正文完整提取 |
| 知乎 | `https://www.zhihu.com/question/623681208` | 问答内容完整 |
| CSDN | `https://blog.csdn.net/blogdevteam/article/details/126135357` | 正文完整 |
| 掘金 | `https://juejin.cn/post/7584110439933100078` | 正文完整提取 |
| B站专栏 | `https://www.bilibili.com/read/cv28884499` | 正文完整提取 |

## CDP 提取（clip-and-process Layer 2）

| 平台 | 测试 URL | 验证要点 | CDP 提取选择器 |
|------|----------|----------|---------------|
| bestblogs.dev 播客 | `https://www.bestblogs.dev/podcast/2d4c0cf` | 完整转录稿 | `<main>` 元素 |
| 微信公众号 | `https://mp.weixin.qq.com/s/10Fm0x-OPm1dwze9NJTkQA` | 标题+作者+正文 | `#activity-name`, `#js_name`, `#js_content` |
| 小红书 | `https://www.xiaohongshu.com/explore/69ecca88000000001f001b30?xsec_token=ABZJA5howoXHQTPA9oBrQk7XbOxXv7c2nKPa0-h0mgXbM=&xsec_source=pc_user` | 标题+正文+图片 | `.note-content` 或 `.desc` |

## 视频字幕提取（xiaopang-video-transcript）

| 平台 | 测试 URL | 验证要点 | 命令 |
|------|----------|----------|------|
| YouTube | `https://www.youtube.com/watch?v=yfQ3fucECME` | 字幕+段落 | `bun ~/ai/skills/xiaopang-video-transcript/scripts/fetch.ts '<URL>' --out /tmp/xvt/t1` |
| Bilibili | `https://www.bilibili.com/video/BV1xx411c7mD` | 官方字幕→ASR 兜底 | `bun ~/ai/skills/xiaopang-video-transcript/scripts/fetch.ts '<URL>' --out /tmp/xvt/t2` |

## 飞书文档（lark-mcp）

| 类型 | 测试 URL | 验证要点 | API 调用链 |
|------|----------|----------|-----------|
| 飞书 Wiki | `https://eyvwt4pfvp.feishu.cn/wiki/UQM2w7ZfYiEmswkiIQ3cih1xnTb` | 完整文档内容 | `wiki_v2_space_getNode(token, useUAT=true)` → 取 `obj_token` → `docx_v1_document_rawContent(document_id=obj_token)` |

## 注意事项

- **YouTube 必须设置终端代理**：`export https_proxy=http://127.0.0.1:7890 http_proxy=http://127.0.0.1:7890 all_proxy=socks5://127.0.0.1:7890`
- **统一入口**：只有 `fetch.ts`，语言用 `--lang zh`，平台自动识别
- **飞书**：所有 lark-mcp 调用需 `useUAT=true`
- **链接可能失效**：部分链接可能随时间过期（如小红书 xsec_token），需定期更新
- **CDP 前置条件**：需 Chrome 开启 remote debugging，`check-deps.mjs` 通过
