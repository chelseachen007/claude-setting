---
name: v2ex-topics
description: "V2EX话题浏览工具. 获取V2EX热门话题、节点话题、主题详情和回复. 当用户需要浏览V2EX内容时触发. 关键词: V2EX、V站、威克斯、程序员社区."
---

# V2EX 话题

获取 V2EX 热门话题、节点话题、主题详情和回复。

## 环境要求

无需配置，使用公开 API。

## 使用方法

### 获取热门话题

```bash
curl -s "https://www.v2ex.com/api/topics/hot.json" -H "User-Agent: agent-reach/1.0"
```

### 获取节点话题

```bash
# node_name: python, tech, jobs, qna, apple, creative 等
curl -s "https://www.v2ex.com/api/topics/show.json?node_name=python&page=1" -H "User-Agent: agent-reach/1.0"
```

### 获取主题详情

```bash
# topic_id 从 URL 获取，如 https://www.v2ex.com/t/1234567
curl -s "https://www.v2ex.com/api/topics/show.json?id=TOPIC_ID" -H "User-Agent: agent-reach/1.0"
```

### 获取主题回复

```bash
curl -s "https://www.v2ex.com/api/replies/show.json?topic_id=TOPIC_ID&page=1" -H "User-Agent: agent-reach/1.0"
```

### 获取用户信息

```bash
curl -s "https://www.v2ex.com/api/members/show.json?username=USERNAME" -H "User-Agent: agent-reach/1.0"
```

## 常用节点

| 节点名 | 说明 |
|--------|------|
| tech | 技术 |
| python | Python |
| apple | Apple |
| jobs | 酷工作 |
| qna | 问与答 |
| creative | 分享创造 |
| cloud | 云计算 |
| dev | 开发者 |

## 输出字段说明

| 字段 | 说明 |
|------|------|
| id | 主题ID |
| title | 标题 |
| url | 链接 |
| content | 内容摘要 |
| replies | 回复数 |
| node.name | 节点名称 |
| member.username | 作者用户名 |
| created | 创建时间 |

## 注意事项

- 无需认证
- 公开 JSON API
- 有频率限制，避免频繁请求
