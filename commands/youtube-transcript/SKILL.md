---
name: youtube-transcript
description: "YouTube视频信息和字幕提取工具. 获取YouTube视频元数据, 下载字幕和自动生成字幕. 当用户需要获取YouTube视频信息或字幕时触发. 关键词: YouTube、油管、YouTube字幕、视频字幕."
---

# YouTube 视频字幕

获取YouTube视频元数据和字幕内容。

## 环境要求

- yt-dlp 已安装: `pipx install yt-dlp`

## 使用方法

### 获取视频信息

```bash
yt-dlp --dump-json "https://www.youtube.com/watch?v=VIDEO_ID"
```

### 下载字幕

```bash
# 下载现有字幕 + 自动生成字幕
yt-dlp --write-sub --write-auto-sub --sub-lang "zh-Hans,zh,en" \
  --skip-download -o "/tmp/%(id)s" "https://www.youtube.com/watch?v=VIDEO_ID"
```

### 读取字幕文件

```bash
cat /tmp/VIDEO_ID.zh-Hans.vtt
# 或
cat /tmp/VIDEO_ID.en.vtt
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
| channel | 频道名称 |
| channel_id | 频道ID |
| duration | 时长(秒) |
| view_count | 播放量 |
| like_count | 点赞数 |
| upload_date | 上传日期 |
| thumbnail | 缩略图URL |

## 字幕语言代码

| 代码 | 语言 |
|------|------|
| zh-Hans | 简体中文 |
| zh-Hant | 繁体中文 |
| zh | 中文(通用) |
| en | 英文 |
| ja | 日文 |

## 故障排除

- **无字幕**: 视频可能没有字幕，尝试 `--write-auto-sub` 获取自动生成字幕
- **下载慢**: YouTube视频较大，下载需要时间
- **地区限制**: 某些视频有地区限制，需要代理
