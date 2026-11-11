---
name: md-to-pdf
description: "触发词：生成PDF、导出PDF、转PDF、Markdown转PDF、做成PDF、导出文档。将 Obsidian 笔记（单个文件或整个目录）转为排版精美的 PDF 文档。自动处理 Obsidian 语法、中文排版、代码高亮。"
---

# MD to PDF — Markdown 转 PDF 导出工具

将 Obsidian 笔记转为排版精美的 PDF。支持单文件或整个目录合并导出，自动清理 Obsidian 语法，输出 A4 中文友好排版。

## 触发词

- `/md-to-pdf`
- "生成PDF"
- "导出PDF"
- "转PDF"
- "做成PDF"
- "导出文档"
- "Markdown转PDF"

## 前提条件

### 系统依赖

执行前检查以下依赖是否已安装，缺什么装什么：

```bash
# 检查 Python3
python3 --version

# 检查依赖库
pip3 list 2>/dev/null | grep -E "weasyprint|markdown"

# 检查系统库（weasyprint 需要）
ls /opt/homebrew/lib/libgobject-2.0*.dylib 2>/dev/null
```

如需安装：

```bash
# 安装系统库
brew install pango glib

# 安装 Python 依赖
pip3 install --break-system-packages markdown weasyprint
```

### 输入要求

- 源文件必须是 `.md` 格式
- 文件可包含 Obsidian 语法（frontmatter、wikilink、callout 等），会自动清理

## 执行流程

### Step 1：确认输入

询问用户（或从上下文推断）：

1. **源路径**：单个 `.md` 文件路径，或包含多个 `.md` 文件的目录路径
2. **排除文件**：是否有需要排除的文件（按文件名或模式）
3. **输出路径**：PDF 保存位置，默认 `~/Downloads/` 或用户指定的素材目录
4. **文档标题**：PDF 的标题，默认取目录名或文件名

如果用户指定的是目录，按文件名自然排序合并。如果用户指定了排除列表，跳过匹配的文件。

如果用户已经明确说了源和目标（如"把 XX 目录做成 PDF"），直接执行，不用再问。

### Step 2：构建命令

根据用户输入构建 `md2pdf.py` 命令行参数。

脚本位置：`{SKILL_DIR}/scripts/md2pdf.py`（即本 skill 目录下的 `scripts/md2pdf.py`）

参数说明：

| 参数 | 必填 | 说明 |
|------|------|------|
| `--input` | 是 | `.md` 文件路径或目录路径 |
| `--output` | 是 | 输出 PDF 路径 |
| `--title` | 否 | 文档标题，默认取文件/目录名 |
| `--exclude` | 否 | 排除文件名（逗号分隔） |
| `--order` | 否 | 指定文件顺序（逗号分隔文件名） |

关键清理规则（脚本内置）：

| Obsidian 语法 | 处理方式 |
|---------------|---------|
| Frontmatter `---...---` | 移除 |
| `[[wikilink\|别名]]` | 转为别名文本 |
| `[[wikilink]]` | 转为纯文本 |
| `!\[\[embed\]\]` | 转为纯文本 |
| `> [!type] title` | 转为 `> **类型：title**` 引用块 |
| ` ```dataview ` | 转为普通代码块 |
| 连续 `---` 分隔线 | 合并为一个 |

### Step 3：生成 PDF

执行转换脚本：

```bash
python3 {SKILL_DIR}/scripts/md2pdf.py \
  --input "<源路径>" \
  --output "<输出PDF路径>" \
  --title "<文档标题>" \
  --exclude "<排除文件1,排除文件2>" \
  --order "<01-a.md,02-b.md>"
```

其中 `{SKILL_DIR}` 是本 SKILL.md 所在目录（全局技能库中即 `~/ai/skills/md-to-pdf/`）。

成功后告知用户 PDF 文件路径，并用 `open` 命令打开预览。

如果失败，根据错误信息排查：
- 缺依赖 → 执行前提条件中的安装命令
- 权限问题 → 提示用户检查路径
- 中文乱码 → 检查系统是否安装中文字体

### Step 4：输出

1. 告知用户 PDF 文件位置和大小
2. 用 `open` 打开 PDF 预览

## 注意事项

1. **依赖前置**：首次使用时检查并安装依赖，后续跳过
2. **临时文件**：脚本和中间文件放在 `/tmp/`，完成后清理
3. **中文排版**：CSS 已配置 PingFang SC 等中文字体，macOS 原生支持
4. **分页控制**：h1 自动分页，表格和代码块避免跨页断裂
5. **大文件**：超过 50 个文件时提醒用户可能耗时较长
6. **输出默认路径**：优先用用户指定的路径，其次 `~/Downloads/`，再次 `素材/` 目录

## 使用场景

- 将系列文章（如手册、教程）导出为 PDF 分享
- 将单个笔记导出为 PDF 存档
- 将目录下的笔记合并为一份完整文档
