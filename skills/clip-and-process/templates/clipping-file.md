# 剪藏文件模板

## Frontmatter 格式

```yaml
---
title: 内容标题
date: YYYY-MM-DD
tags: [剪藏, 状态/未整理]
lastmod: YYYY-MM-DD
source: 来源平台
url: 原始链接
author: 作者
type: article
---
```

### title 字段注意事项

- 标题不含特殊字符时，不加引号：`title: 这是一篇文章`
- 标题含中文引号 `""`、冒号 `:` 等 YAML 特殊字符时，用**单引号**包裹：`title: '为什么上证是"综指"、深证用"成指"？'`
- 不要用双引号包裹含中文引号的标题（会 YAML 解析冲突）

### type 字段映射

| 提取来源 | type 值 |
|---------|---------|
| 网页提取 | `article` |
| 视频转录 | `video` |
| 飞书文档/Wiki | `article`（source 写 `飞书文档`/`飞书Wiki`/`飞书多维表格`） |
| 文档文件（PDF/EPUB/DOCX 等） | `document` |
| 图片 OCR | `image-post` |
| 小红书帖子 | `xhs-post` |

## 内容结构

```markdown
## 总结

（由用户在浏览器中手动填充）

## 金句摘抄

（由用户在浏览器中手动填充）

## 原文

[提取的正文内容 / 视频文字稿]
（英文内容此处为原文，下方有译文章节）

## 译文

（仅英文内容有此章节，由 baoyu-translate 生成）

## 入库思考

（剪藏后由用户强制填写，AI 在下一步询问）

## 闪念

（由用户手动填写，AI 不生成）

## 常青笔记

（深度处理时由 AI 填入）

## 连接

（深度处理时由 AI 填入）

## 行动

（深度处理时由 AI 填入）
```

## 图片规范

剪藏配图**不落本地附件**，一律上传到 OSS 后在正文里用远程链接（流程见 SKILL.md 的 Step 3.5）：

```markdown
![](<https://chelsechen-img.oss-cn-hangzhou.aliyuncs.com/fde说明书-01.png>)
```

- 文件名带文章短名前缀，避免所有剪藏都叫 `img-01.png` 互相覆盖
- URL 用尖括号包住，防止特殊字符打断 Markdown
- 不用 `![[附件/...]]` 嵌入，除非用户明确要求本地保存

## OCR 内容规范

如果提取过程中对图片做了 OCR，OCR 文字必须逐字完整写入 `### 图片内容（OCR 原文）` 小节，不做概括、不写摘要、不删减长文。
