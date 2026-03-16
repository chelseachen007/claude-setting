---
name: wechat-article
description: |
  微信公众号文章阅读工具. 使用Camoufox绕过反爬虫机制, 将文章转换为Markdown格式.
  当用户需要阅读微信公众号文章时触发. 关键词: 微信文章、公众号、微信公众号.
version: 1.0.0
metadata:
  openclaw:
    requires:
      bins:
        - python3
        - uv
      emoji: "\U0001F4F0"
      os:
        - darwin
        - linux
---

# 微信公众号文章阅读

你是"微信文章阅读助手"。帮助用户读取微信公众号文章内容。

## 功能特点

- **反检测抓取** — 使用 Camoufox (隐身 Firefox) 绕过微信反爬机制
- **智能页面等待** — 使用 networkidle 替代硬编码的 sleep
- **重试机制** — 页面加载 3 次指数退避重试
- **验证码检测** — 明确识别验证码页面并给出错误提示
- **图片本地化** — 异步并发下载图片到本地
- **代码块保留** — 自动检测编程语言
- **YAML 元数据** — 结构化的 frontmatter

## 环境要求

- Python 3.10+
- uv 包管理器
- Camoufox 浏览器会在首次运行时自动下载

## 使用方法

### 读取单篇文章

```bash
cd ~/.claude/commands/wechat-article && uv run main.py "https://mp.weixin.qq.com/s/ARTICLE_ID"
```

### 批量转换

```bash
cd ~/.claude/commands/wechat-article && uv run main.py -f urls.txt -o ./output -v
```

### CLI 参数

| 参数 | 说明 | 默认值 |
|------|------|--------|
| `urls` | 一个或多个微信文章链接 | - |
| `-f, --file` | 包含 URL 的文本文件 | - |
| `-o, --output` | 输出目录 | ./output |
| `-c, --concurrency` | 图片下载并发数 | 5 |
| `--no-images` | 跳过图片下载 | false |
| `--no-headless` | 显示浏览器窗口 | false |
| `--force` | 覆盖已有输出 | false |
| `--no-frontmatter` | 使用引用块格式元数据 | false |
| `-v, --verbose` | 启用调试日志 | false |

### 处理验证码

如果遇到验证码，使用 `--no-headless` 显示浏览器窗口手动解决：

```bash
cd ~/.claude/commands/wechat-article && uv run main.py --no-headless "https://mp.weixin.qq.com/s/ARTICLE_ID"
```

## 输出结构

```
output/
  <文章标题>/
    <文章标题>.md    # Markdown 文件，含 YAML frontmatter
    images/
      img_001.png
      img_002.jpg
      ...
```

## 输出字段

| 字段 | 说明 |
|------|------|
| title | 文章标题 |
| author | 作者 |
| content | 文章内容 (Markdown) |
| publish_time | 发布时间 |
| source_url | 原文链接 |

## 失败处理

- **验证码/环境异常**: 使用 `--no-headless` 手动解决验证码
- **内容为空**: 微信可能在限流，等几分钟再试
- **图片下载失败**: 失败的图片会保留远程链接，用 `--force` 重新运行

## 限制

- 只支持 `mp.weixin.qq.com` 域名的文章
- 需要能够运行无头浏览器的环境
- 微信可能会阻止自动化访问，Camoufox 有助于规避但非保证成功
