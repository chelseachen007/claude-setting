---
name: xhs-cover
description: |
  小红书封面图生成器。基于 HTML+CSS + Playwright 截图方案，零外部依赖，一句话出图。
  支持自动分析内容情绪，智能匹配配色方案和布局模板。
  触发词：生成封面图、小红书封面、封面、cover、做个封面、帮我做封面图。
  当用户需要为小红书帖子生成封面图时触发。也适用于 multi-publish 发布流程中的封面生成环节。
allowed-tools: Bash, Read, Write
---

# 小红书封面图生成器

HTML+CSS + Playwright 截图方案。零外部依赖，一句话出图。

## 触发条件

- "生成封面图"、"做个封面"、"小红书封面"
- "帮我做封面"、"出个 cover"
- multi-publish 流程中需要封面图时

## 核心原则

1. **封面图 ≠ 内容卡**。封面图是小红书 feed 中第一张图，目标是「让人停下来点击」，不是展示完整内容
2. **一眼法则**。缩小到手机 feed 流的缩略图尺寸，核心信息仍然可读
3. **标题即钩子**。封面标题 ≤15 字（大字报式 ≤10 字），必须压缩到最吸引眼球的核心信息
4. **零外部依赖**。不加载任何外部字体、CDN、图片。纯 HTML+CSS + 系统字体

## 工作流程

### 步骤 1：获取内容

从以下来源获取内容：
- 用户直接提供的标题/主题
- 文章文件（Read 读取）
- URL（通过 cn-content-extractor 提取）

### 步骤 2：分析内容

从内容中提取：
1. **核心主题**：这篇文章/主题在讲什么？（≤10 字概括）
2. **情绪色调**：属于哪类内容？（技术/搞钱/情感/自然/思辨/创意）
3. **关键数据**：有没有核心数字？（如"9.9"、"5000"、"3天"）
4. **要点数量**：核心要点有几个？（影响布局选择）
5. **对比元素**：有没有前后/优劣对比？

### 步骤 3：读取设计系统

Read `~/.claude/skills/xhs-cover/references/design-system.md`

根据步骤 2 的分析结果，按设计系统的决策规则选择：
- **配色方案**：6 选 1（糖果粉/薄荷绿/克莱因蓝/暖橘/冷灰/渐变紫）
- **布局模板**：4 选 1（大字报式/卡片式/列表式/对比式）
- **标题压缩**：将原标题压缩到封面标题的字数限制

### 步骤 4：生成 HTML

按选定的配色和布局，生成完整的 HTML 文件。

**硬性要求**：
- `<html>` 和 `<body>` 宽高严格 1080x1440px
- `overflow: hidden`（不滚动）
- CSS 全部内联（`<style>` 标签内）
- 字体栈：`system-ui, -apple-system, "PingFang SC", "Microsoft YaHei", sans-serif`
- 不加载任何外部资源
- 文件写入 `/tmp/xhs_cover_{name}.html`

**CSS 变量**（每张封面开头定义）：
```css
:root {
  --bg: {配色方案的背景色};
  --accent: {配色方案的强调色};
  --text-dark: {配色方案的深色};
  --text-mid: #6E6E73;
  --text-dim: #ACACB0;
}
```

### 步骤 5：截图

```bash
node ~/.claude/skills/xhs-cover/assets/capture.js \
  /tmp/xhs_cover_{name}.html \
  {输出路径}/cover_{name}.png \
  1080 1440
```

输出路径优先使用用户指定的路径，或 multi-publish 流程中的素材目录。

如果 capture.js 报错（Playwright 未安装）：
```bash
npm install -g playwright && npx playwright install chromium
```

### 步骤 6：验证

截图后用 Read 查看 PNG，检查：
1. 核心内容是否在安全区域（中心 60%）内
2. 标题是否 ≤3 行，有没有溢出
3. 缩小到约 375px 宽是否仍然清晰可读
4. 配色是否和谐，有没有刺眼的地方
5. 有没有空白过多（底部空白 >10% 需要调整）

如有问题，修改 HTML 重新截图。

## 与 multi-publish 集成

在 multi-publish 流程中，当需要生成小红书封面图时：
1. 从文章内容自动分析
2. 生成的封面 PNG 作为第一张图（封面卡）
3. 后续内容卡片由 card-caster 生成

## 文件结构

```
xhs-cover/
├── SKILL.md                          # 本文件
├── references/
│   └── design-system.md              # 设计系统（配色、布局、决策规则）
└── assets/
    └── capture.js                    # Playwright 截图工具
```
