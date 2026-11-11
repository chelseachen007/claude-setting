---
name: yao-tutorial-skill
description: 输入主题或参考资料，生成教程（tutorial.md + 配图）。用户明确要求时才导出 DOCX/PDF/HTML。
---

# Yao Tutorial Skill

## 工作流

### 默认模式（tutorial.md + 配图）

1. 将主题、受众、目标、语言、格式、用户材料、风格参考和排除项归一化为 `brief.json`。
2. 读取 `references/input-adaptation.md`；用户材料充足时以其为主线，仅补充必要的外部研究。
3. 读取 `references/research-sourcing.md`；按需创建 `research/user-materials-register.md`、`research/source-register.md` 和 `research/evidence-map.md`。
4. 读取 `references/tutorial-outline-and-writing.md` 和 `references/course-design-principles.md`；编写 `outline.md`、独立的公开版 `tutorial.md`（使用「第1章」「1.1」格式），以及 `research/chapter-quality-review.md`。
5. 读取编辑和配图参考文档；创建 `visuals/visual-spec.json`，然后运行 `build_visual_pack.py` 和 `capture_visuals.py`。
6. 用 PicGo 上传所有配图：`npx picgo upload <路径>`，将 tutorial.md 中本地路径替换为远程 URL。
7. 停止。产出：`brief.json`、`outline.md`、`tutorial.md`（含远程配图）、`research/`、`visuals/`。

### 完整导出模式（用户明确要求时触发）

在默认模式基础上继续：

8. 读取 `references/export-workflow.md`；运行 `export_tutorial.py`，然后运行 `validate_package.py`。
9. 报告确切的失败和回退情况。

### 触发导出模式的信号

用户说以下关键词时走完整导出：「导出」「HTML」「DOCX」「PDF」「完整包」「发布」「多格式」。

## 配图上传规范

- 使用 `npx picgo upload <路径>` 上传图片（阿里云 OSS）
- 上传后将 tutorial.md 中 `assets/screenshots/...` 替换为远程 URL
- 不保留本地图片路径在 tutorial.md 中

## 质量门禁

- 用户材料足够时控制教程意图；外部证据用于验证和补充缺口。
- 公开导出文件不显示内部来源 ID 或参考包来源。
- 正文读起来像独立的正式教学产品。
- 每个编号章节有对应的配图规格和嵌入配图。
- 深度由学习充分性决定，而非固定字数上限；持续到学习者能理解、应用和自检。
- 每个编号章节有独立的质检记录，覆盖深度、案例、练习、证据、配图适配度和后半部分一致性。
- 完整导出模式下：HTML 使用居中 `report-shell`；DOCX/PDF 无可见页眉脚、本地路径或打印元素；通过 `validate_package.py` 验证。
- 绝不捏造 X 帖子、论文、仓库详情、日期或引用。

## 参考文件

- `references/input-adaptation.md`
- `references/research-sourcing.md`
- `references/tutorial-outline-and-writing.md`
- `references/course-design-principles.md`
- `references/editorial-production.md`
- `references/visual-html-workflow.md`
- `references/visual-board-benchmarks.md`
- `references/export-workflow.md`
- `scripts/build_visual_pack.py`, `scripts/capture_visuals.py`, `scripts/export_tutorial.py`, `scripts/validate_package.py`
- `templates/topic-brief-template.json`, `templates/visual-spec-template.json`, `templates/tutorial-style.css`
