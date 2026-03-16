---
name: web-search
description: |
  全网语义搜索工具. 使用Exa AI进行高质量语义搜索, 获取代码上下文, 读取网页内容.
  当用户需要搜索互联网信息、查找代码示例或进行网络研究时触发. 关键词: 搜索、上网搜、搜一下、web search、搜索网页.
version: 1.0.0
metadata:
  openclaw:
    requires:
      bins:
        - python3
        - uv
      emoji: "\U0001F50D"
      os:
        - darwin
        - linux
---

# 网页搜索 (Exa AI)

你是"网络搜索助手"。帮助用户进行语义搜索、查找代码示例、读取网页内容。

## 功能特点

- **语义搜索** — 使用 Exa AI 进行高质量语义搜索（非关键词匹配）
- **代码上下文** — 优先搜索技术网站获取代码示例
- **相似网页** — 查找与给定 URL 相似的网页
- **网页阅读** — 使用 Jina Reader 读取任意网页内容
- **PDF 阅读** — 读取在线 PDF 文件

## 环境要求

- Python 3.10+
- uv 包管理器
- Exa API Key (搜索功能需要，read 功能不需要)

## 配置 Exa API Key

Exa 搜索需要 API Key（有免费额度）：

```bash
# 1. 访问 https://exa.ai 注册账号获取 API Key
# 2. 配置环境变量
export EXA_API_KEY="your-exa-api-key"
```

**注意**：`read` 命令使用 Jina Reader，无需 API Key 即可使用。

## 使用方法

### 语义搜索

```bash
cd ~/.claude/commands/web-search && uv run scripts/web_search.py search --query "Python async best practices" --limit 10
```

### 代码上下文搜索

```bash
cd ~/.claude/commands/web-search && uv run scripts/web_search.py code --query "FastAPI dependency injection" --limit 10
```

### 查找相似网页

```bash
cd ~/.claude/commands/web-search && uv run scripts/web_search.py similar --url "https://example.com/article" --limit 5
```

### 读取网页内容

```bash
cd ~/.claude/commands/web-search && uv run scripts/web_search.py read --url "https://example.com/article"
```

### 读取 PDF

```bash
cd ~/.claude/commands/web-search && uv run scripts/web_search.py read --url "https://example.com/doc.pdf"
```

### 获取多个网页内容

```bash
cd ~/.claude/commands/web-search && uv run scripts/web_search.py contents --urls "https://a.com" "https://b.com" --max-chars 2000
```

## CLI 命令

| 命令 | 说明 | 参数 |
|------|------|------|
| `search` | 语义搜索 | `--query`, `--limit`, `--include`, `--exclude` |
| `code` | 代码搜索 | `--query`, `--limit`, `--tokens` |
| `similar` | 相似网页 | `--url`, `--limit` |
| `contents` | 获取内容 | `--urls`, `--max-chars` |
| `read` | 读取网页 | `--url`, `--format` |

## 搜索参数

| 参数 | 说明 | 默认值 |
|------|------|--------|
| `--query, -q` | 搜索关键词 | 必填 |
| `--limit, -l` | 返回结果数量 | 10 |
| `--include, -i` | 只搜索这些域名 | - |
| `--exclude, -e` | 排除这些域名 | - |

## 输出字段说明

| 字段 | 说明 |
|------|------|
| url | 网页链接 |
| title | 网页标题 |
| text | 网页摘要 |
| publishedDate | 发布日期 |
| author | 作者 |
| score | 相关性分数 |

## Jina Reader

Jina Reader 可以将任意网页转换为 Markdown 格式：

```bash
# 读取网页内容
cd ~/.claude/commands/web-search && uv run scripts/web_search.py read --url "https://example.com/article"

# 读取 PDF
cd ~/.claude/commands/web-search && uv run scripts/web_search.py read --url "https://example.com/doc.pdf"
```

## 技术栈

- **Exa AI**: AI 驱动的语义搜索引擎
- **Jina Reader**: 网页转 Markdown 服务 (r.jina.ai)

## 失败处理

- **搜索无结果**: 尝试更换关键词
- **结果不相关**: 使用更具体的搜索词，或使用 `--include` 限定域名
- **连接超时**: 检查网络连接
- **API 限流**: 等待几分钟后重试，或配置 EXA_API_KEY

## 免费额度

- Exa: 每月 1000 次免费搜索
- Jina Reader: 免费使用，无需注册
