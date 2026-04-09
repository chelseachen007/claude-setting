---
name: multi-publish
description: |
  多平台一键发布。将文章同时发布到微信公众号草稿箱和小红书。
  支持内容格式自动适配：微信 HTML 优化、小红书 emoji 风格压缩。
  触发词：一键发布、多平台发布、发布到微信、发布到小红书、同步发布。
allowed-tools: Bash, Read, Write, Skill
---

# 多平台一键发布 Skill

将文章内容一键发布到微信公众号草稿箱 + 小红书，自动适配各平台格式。

## 触发条件

当用户说以下类似话术时使用此 Skill：
- "一键发布"、"多平台发布"、"同步发布"
- "发布到微信" / "发到公众号" / "推到草稿箱"
- "发布到小红书" / "推到小红书"
- "同时发布到微信和小红书"

## 前置检查

### 微信公众号配置
配置文件位于 `~/.multi-publish/wechat_config.json`，首次使用需要运行配置向导：

```bash
python3 ~/.claude/skills/multi-publish/wechat_publisher.py --setup
```

需要：
- 微信公众号 AppID 和 AppSecret（从 mp.weixin.qq.com 获取）
- 服务器 IP 添加到微信 IP 白名单
- Python 依赖：`requests`, `Pillow`（可选，用于图片转换）

### 小红书配置
复用已有的 `xiaohongshu-skills`，需要：
- Chrome 浏览器已启动（`python scripts/chrome_launcher.py`）
- 已登录小红书账号（`python scripts/cli.py check-login`）

## 执行流程

### 步骤 1：确认发布内容

从用户提供的素材中确认：
- **标题**（微信标题 ≤64字，小红书标题 ≤20字）
- **内容**（HTML 或 Markdown 格式）
- **封面图**（可选，用于微信草稿）
- **作者**（可选）
- **摘要**（可选）

如果用户提供了 Markdown 内容，需要先转换为 HTML。

### 步骤 2：确认发布平台

询问用户要发布到哪些平台：
- 仅微信公众号草稿箱
- 仅小红书
- 两者都发（默认）

### 步骤 3：发布到微信公众号草稿箱

```bash
python3 ~/.claude/skills/multi-publish/wechat_publisher.py \
  --title "文章标题" \
  --content /tmp/article.html \
  --author "作者名" \
  --cover /path/to/cover.png
```

脚本会自动处理：
- access_token 获取和缓存
- 封面图上传（转 JPG，≤1MB）
- HTML 内容图片上传到微信 CDN
- 微信编辑器样式修复（背景色转 table、CSS 加 !important、禁用缩进等）
- 字段长度自动截断

成功后输出 media_id，用户可在 mp.weixin.qq.com 草稿箱查看。

### 步骤 4：生成小红书图文卡片

当发布目标是小红书时，使用 `card-caster` skill 的 `-m` 模式将文章内容拆分为多张 1080x1440 卡片图片。图片卡片是小红书的主要内容载体，正文只作为补充文案。

#### 4.1 内容拆分原则

将长文按主题拆为 6-10 张卡片，每张一个核心主题，遵循升番逻辑（简单→复杂→高潮）：
- **封面卡**：标题 + 引子数据/故事，建立好奇
- **内容卡**：每层一个主题，保留原文细节和完整论述，宁可多加卡片也不压缩原文
- **结尾卡**：核心洞察 + 行动建议

**核心原则：保留原文内容，不要缩减。** 如果原文较长，增加到 8-10 张卡片。用户的原始表述（具体数字、专有名词、完整论据）必须保留，不要用自己的话改写或概括。

#### 4.2 单卡内容密度

每张卡可用高度约 1274px（1440 - 64顶部 - 52底部 - 50页脚），正文 36px/1.7 行高。参考视觉重量：
- 首卡标题区约 160px，续卡 running title 约 60px
- h2 标题约 90px（含上下间距）
- 普通段落（~50字）约 150px
- 金句 highlight 约 130px
- 分割线约 72px

**经验值**：每张卡放 5-8 个短段落或 4 个段落 + 1 条金句。底部呼吸空间控制在 5-8%，不要留大片空白。如果截图后发现底部空白超过一屏的 10%，说明内容不够——应追加原文内容或合并到更少的卡片中。

**内容密度检查清单**（截图后逐卡检查）：
- 底部空白是否 < 页面高度的 10%？如果太大，追加原文内容
- 是否有原文关键论述被省略？把省略的内容补回来
- 单张卡是否只有一个 h2 + 1-2 句话就结束了？太单薄，合并到相邻卡片或补内容

#### 4.3 HTML 模板结构

使用 `card-caster` 的 `assets/poster_template.html` 模板：
- **首卡**：`{{TITLE_BLOCK}}` + `{{HEADER_BLOCK}}` 为空 + `{{BODY_HTML}}`（**不要**使用 `.dropcap`，首字不放大）
- **续卡**：`{{HEADER_BLOCK}}` 含 running title + `{{TITLE_BLOCK}}` 为空 + `{{BODY_HTML}}`
- **末卡**：body 末尾追加 `<p style="text-align:right;font-size:16px;color:#ACACB0;margin-top:40px;">∎</p>`
- 所有卡片：`{{PAGE_INFO}}` 显示 `N / M`

**标题字号规则**：
- 首卡 `<h1>` 默认使用 `52-56px`，确保标题在 1080px 宽度内不换行
- 仅当标题 ≤6 个字时可使用 72-84px
- 混合中英文标题尤其要注意宽度，宁可小一点也不换行

**首字放大（dropcap）规则**：
- **默认不使用** dropcap 效果
- 除非用户明确要求，否则正文首字保持与正文相同字号和颜色

色调选择复用 card-caster 的色调感知表，根据内容气质匹配 BG + Accent 色。

#### 4.4 截图命令

```bash
# 逐张截图（可并行）
node ~/.claude/skills/card-caster/assets/capture.js /tmp/ljg_cast_poster_{name}_{N}.html ~/Downloads/{name}_{N}.png 1080 1440
```

截图后用 Read 查看每张 PNG，检查内容是否完整、有无截断或留白过多，必要时调整 HTML 重拍。

#### 4.5 预览与迭代

生成卡片后，**必须先展示预览**再发布：
1. 截图所有卡片后，用 Read 查看每张 PNG
2. 向用户汇报卡片数量、内容分布、指出潜在问题（截断/留白/排版）
3. 等用户确认后再进入发布流程
4. 如用户要求修改（内容缩减、标题换行、追加图片等），调整 HTML 重拍后再确认

#### 4.6 追加用户图片

用户可能在卡片之外提供自己的图片（截图、照片等），需要混合排列：
- 用户图片通常放在第一张（作为封面）或最后一张
- 将用户图片路径加入 `--images` 参数，与卡片 PNG 一起发布
- 图片总数 ≤18 张（小红书限制）

#### 4.7 适配小红书正文

图片是主内容，正文作为钩子文案（≤350字）：
- 开头用引子数据或反差句吸引注意
- 简要列出 3-5 个核心点，引导滑动图片
- 加入适当 emoji（但不要每句都加）
- 末尾 CTA：点赞收藏 + 引导评论

### 步骤 5：发布到小红书

#### 5.1 检查登录状态

```bash
cd ~/.claude/commands/xiaohongshu-skills
python3 scripts/cli.py check-login
```

#### 5.2 发布

```bash
cd ~/.claude/commands/xiaohongshu-skills
python3 scripts/cli.py publish \
  --title-file /tmp/xhs_title.txt \
  --content-file /tmp/xhs_content.txt \
  --images /path/to/card_1.png /path/to/card_2.png ... /path/to/card_N.png
```

注意：多张图片用空格分隔，不要用逗号。

发布前必须确认用户同意。

### 步骤 6：汇报结果

展示各平台发布结果：
- 微信：media_id + 提示去后台预览
- 小红书：发布状态 + 笔记链接（如有）

## 单平台快捷发布

### 仅发布到微信
```bash
python3 ~/.claude/skills/multi-publish/wechat_publisher.py \
  --title "标题" --content article.html --cover cover.png
```

### 仅发布到小红书
生成卡片图片 → 适配正文 → 调用 xiaohongshu-skills 发布（见步骤 4-5）。

## 常见问题

### 微信 IP 白名单错误
登录 mp.weixin.qq.com → 设置 → 基本配置 → IP白名单 → 添加当前 IP。

### 微信 access_token 过期
脚本自动刷新，如持续失败检查 AppID/AppSecret 是否正确。

### 小红书未登录
先运行 `python scripts/cli.py login` 完成登录。

### 图片上传失败
确保图片为 JPG/PNG 格式，≤1MB。

## 文件结构

```
multi-publish/
├── SKILL.md              # 本文件 - Skill 定义和执行流程
├── wechat_publisher.py   # 微信公众号草稿发布脚本
└── xhs_adapter.py        # 小红书内容适配器
```

## 技术说明

- **微信发布**：使用微信公众号官方 API（OAuth2 Client Credentials），通过 AppID + AppSecret 获取 access_token，调用草稿箱接口创建草稿
- **小红书发布**：复用已有的 `xiaohongshu-skills`（Chrome 自动化方案），不重复实现
- **内容适配**：独立 Python 脚本处理格式转换，微信 HTML 优化和小红书 emoji 风格压缩
