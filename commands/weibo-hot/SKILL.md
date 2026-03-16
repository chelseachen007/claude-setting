---
name: weibo-hot
description: |
  微博热搜和搜索工具. 直接调用微博移动端API获取热搜榜、搜索用户、搜索内容、获取用户动态.
  当用户需要查看微博热搜、搜索微博或获取微博数据时触发. 关键词: 微博、热搜、微博搜索、热搜榜.
version: 1.0.0
metadata:
  openclaw:
    requires:
      bins:
        - python3
        - uv
      emoji: "\U0001F525"
      os:
        - darwin
        - linux
---

# 微博热搜和搜索

你是"微博数据助手"。帮助用户获取微博热搜榜、搜索微博内容、查看用户动态。

## 功能特点

- **获取热搜榜** - 实时微博热搜
- **搜索用户** - 按关键词搜索微博用户
- **搜索内容** - 按关键词搜索微博帖子
- **用户资料** - 获取用户详细信息
- **用户动态** - 获取用户发布的微博
- **获取评论** - 获取微博帖子的评论

## 环境要求

- Python 3.10+
- uv 包管理器
- 无需登录，无需 Cookie
- 无需代理，海外服务器也可直接访问

## 使用方法

### 获取热搜榜

```bash
cd ~/.claude/commands/weibo-hot && uv run scripts/weibo_cli.py trending --limit 10
```

### 搜索用户

```bash
cd ~/.claude/commands/weibo-hot && uv run scripts/weibo_cli.py search-users --keyword "雷军" --limit 5
```

### 搜索内容

```bash
cd ~/.claude/commands/weibo-hot && uv run scripts/weibo_cli.py search-content --keyword "AI" --limit 10
```

### 获取用户资料

```bash
cd ~/.claude/commands/weibo-hot && uv run scripts/weibo_cli.py user-profile --uid 1749127163
```

### 获取用户动态

```bash
cd ~/.claude/commands/weibo-hot && uv run scripts/weibo_cli.py user-feeds --uid 1749127163 --limit 10
```

### 获取微博评论

```bash
cd ~/.claude/commands/weibo-hot && uv run scripts/weibo_cli.py comments --feed-id 5167970394572058 --page 1
```

## CLI 命令

| 命令 | 说明 | 参数 |
|------|------|------|
| `trending` | 获取热搜榜 | `--limit` |
| `search-users` | 搜索用户 | `--keyword`, `--limit` |
| `search-content` | 搜索内容 | `--keyword`, `--limit`, `--page` |
| `user-profile` | 用户资料 | `--uid` |
| `user-feeds` | 用户动态 | `--uid`, `--limit` |
| `comments` | 微博评论 | `--feed-id`, `--page` |

## 输出字段说明

### 热搜榜

| 字段 | 说明 |
|------|------|
| id | 排名 |
| description | 热搜词 |
| trending | 热度值 |
| url | 搜索链接 |

### 用户资料

| 字段 | 说明 |
|------|------|
| id | 用户ID |
| screen_name | 昵称 |
| description | 简介 |
| follow_count | 关注数 |
| followers_count | 粉丝数 |
| verified | 是否认证 |
| verified_reason | 认证信息 |

### 微博内容

| 字段 | 说明 |
|------|------|
| id | 微博ID |
| text | 内容 |
| source | 来源设备 |
| created_at | 发布时间 |
| comments_count | 评论数 |
| attitudes_count | 点赞数 |
| reposts_count | 转发数 |
| region_name | 发布地区 |
| pics | 图片列表 |
| videos | 视频信息 |

## 注意事项

- 无需登录，无需 Cookie
- 无需代理，但某些网络环境可能被限制
- 公开 API 有频率限制，避免频繁请求
- 每次请求后建议间隔 1-2 秒

## 网络限制说明

微博 API 对某些 IP 段有访问限制（返回 HTTP 432）。如果遇到此问题：

1. **使用代理/VPN**：切换到不同的网络环境
2. **使用第三方 API**：可以使用其他微博热搜聚合服务
3. **等待重试**：有时限制是临时的

## 失败处理

- **搜索无结果**: 检查关键词是否正确
- **连接失败**: 检查网络连接
- **用户不存在**: 检查用户ID是否正确
- **频率限制**: 等待几分钟后重试
