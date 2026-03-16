---
name: bilibili-video
description: "B站视频信息和字幕提取工具. 获取B站视频元数据, 下载字幕, 提取视频信息. 当用户需要获取B站视频信息或字幕时触发. 关键词: B站、bilibili、B站视频、B站字幕、哔哩哔哩."
---

# B站视频信息

获取B站视频元数据和字幕内容。

## 环境要求

- yt-dlp 已安装: `pipx install yt-dlp`

## 使用方法

### 获取视频信息

```bash
yt-dlp --dump-json "https://www.bilibili.com/video/BVxxxxxx"
```

### 下载字幕

```bash
yt-dlp --write-sub --write-auto-sub --sub-lang "zh-Hans,zh,en" \
  --convert-subs vtt --skip-download \
  -o "/tmp/%(id)s" "https://www.bilibili.com/video/BVxxxxxx"
```

### 读取字幕文件

```bash
cat /tmp/视频ID.zh-Hans.vtt
```

### 搜索视频

```bash
yt-dlp --dump-json "ytsearch5:搜索关键词"
```

## 输出字段说明

| 字段 | 说明 |
|------|------|
| id | 视频ID |
| title | 视频标题 |
| description | 视频简介 |
| uploader | 上传者 |
| duration | 时长(秒) |
| view_count | 播放量 |
| like_count | 点赞数 |
| upload_date | 上传日期 |

## 注意事项

- 服务器 IP 可能被限制 (412 错误)
- 本地环境通常正常工作
- 如遇问题可尝试: `--cookies-from-browser chrome`

## 故障排除

- **412 错误**: 服务器 IP 被限制，使用代理或本地环境
- **无字幕**: 视频可能没有字幕，尝试自动生成字幕
- **下载失败**: 检查视频链接是否有效
