---
name: multi-publish
description: |
  多平台一键发布。将文章同时发布到微信公众号草稿箱和小红书。
  支持内容格式自动适配：微信 HTML 优化、小红书图文卡片生成。
  小红书通过 web-access CDP 浏览器自动化发布。
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

## 一键发布工具

`~/.multi-publish/wechat_oneclick.py` 是集成工具，包含完整流程：

### 单篇文章发布（自动生成封面）
```bash
python3 ~/.multi-publish/wechat_oneclick.py \
  --md article.md \
  --prompt "描述封面图内容，900x383px，绿色系主题"
```

### 单篇发布（已有封面）
```bash
python3 ~/.multi-publish/wechat_oneclick.py \
  --md article.md \
  --cover /path/to/cover.jpg
```

### 批量发布
```bash
python3 ~/.multi-publish/wechat_oneclick.py --batch batch_config.json
```

### 仅生成封面（不发布）
```bash
python3 ~/.multi-publish/wechat_oneclick.py \
  --prompt "描述封面图" \
  --output cover_01.jpg
```

### 仅转换 HTML
```bash
python3 ~/.multi-publish/wechat_oneclick.py --md article.md --html-only
```

## 正确的发布流程（重要！）

**封面 → 上传 → 转换 → 发布**，不要跳步！

1. **生成封面图**（Gemini）：通过 `wechat_oneclick.py` 或 `batch_covers.py`
2. **上传封面到微信**：获取 `thumb_media_id`（必须，否则 40007 错误）
3. **从原始 MD 转换 HTML**：不要从 API 取回内容再重发（会丢失大量内容）
4. **创建草稿**：带上封面 media_id

### 踩坑记录
- **封面必须提供**：微信草稿 API 必须要 `thumb_media_id`，否则报 40007
- **API 编码**：`resp.content.decode('utf-8')` 而非 `resp.json()`
- **内容不要从 API 回取**：从原始 Markdown 重新转换，API 返回内容会丢失
- **IP 白名单**：IP 变化时需去 mp.weixin.qq.com 更新，token 缓存失效时 `rm -f ~/.multi-publish/wechat_token.json`
- **Gemini 检测**：用 `img[src^="blob:https://gemini.google.com/"]` 判断生成完成
- **Gemini 导出**：用 canvas.toDataURL() 自动导出，无需手动下载
- **微信不支持超链接**：`<a href>` 标签在公众号里不显示为可点击链接。所有链接必须用纯文本展示，格式为 `名称（URL）`，读者复制 URL 打开。文中引用和末尾链接区都适用。
- **pandoc 裸 HTML 无样式**：pandoc 转出的 HTML 没有排版样式，直接发布效果很差。需要手动写带 inline style 的 HTML：代码块用深色背景、金句用暖黄高亮块、H2 左侧装饰线、表格用 flex 布局模拟。模板参考 `/tmp/claude_code_article_styled.html` 的结构。

## 素材目录

所有素材（卡片图片、HTML 文件等）统一存放到：

```
/Users/chenjie/Documents/study/claude/素材/{平台}/{主题}/
```

示例：
- `素材/小红书/ai-yanggao/xhs_yanggao_1.png`
- `素材/公众号/knowledge-garden/`

每次发布前，先根据文章主题创建对应子目录。主题名用英文短横线风格（kebab-case）。

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
使用 web-access skill 的 CDP 浏览器自动化方案，需要：
- 用户的日常 Chrome 已登录小红书（creator.xiaohongshu.com）
- CDP proxy 可连接（`bash ~/.claude/skills/web-access/scripts/check-deps.sh`）
- 如果 proxy 连接失败，引导用户在 Chrome 中开启远程调试授权

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

当发布目标是小红书时，使用 `card-caster` 的 HTML 模板将文章内容拆分为多张 1080x1440 卡片图片。图片卡片是小红书的主要内容载体，正文只作为补充文案。

#### 4.1 创建素材目录

```bash
mkdir -p "/Users/chenjie/Documents/study/claude/素材/小红书/{主题名}"
```

主题名根据文章内容取一个简短的英文标识，如 `ai-yanggao`、`knowledge-garden`。

#### 4.2 内容拆分原则

将长文按主题拆为 6-10 张卡片，每张一个核心主题，遵循升番逻辑（简单→复杂→高潮）：
- **封面卡**：标题 + 引子数据/故事，建立好奇
- **内容卡**：每层一个主题，保留原文细节和完整论述，宁可多加卡片也不压缩原文
- **结尾卡**：核心洞察 + 行动建议

**核心原则：保留原文内容，不要缩减。** 如果原文较长，增加到 8-10 张卡片。用户的原始表述（具体数字、专有名词、完整论据）必须保留，不要用自己的话改写或概括。

#### 4.3 单卡内容密度

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

#### 4.4 HTML 模板结构

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

#### 4.5 截图命令

HTML 文件和截图都保存到素材目录：

```bash
# 逐张截图（可并行）
node ~/.claude/skills/card-caster/assets/capture.js \
  /tmp/xhs_{topic}_{N}.html \
  "/Users/chenjie/Documents/study/claude/素材/小红书/{topic}/xhs_{topic}_{N}.png" \
  1080 1440
```

截图后用 Read 查看每张 PNG，检查内容是否完整、有无截断或留白过多，必要时调整 HTML 重拍。

#### 4.6 预览与迭代

生成卡片后，**必须先展示预览**再发布：
1. 截图所有卡片后，用 Read 查看每张 PNG
2. 向用户汇报卡片数量、内容分布、指出潜在问题（截断/留白/排版）
3. 等用户确认后再进入发布流程
4. 如用户要求修改（内容缩减、标题换行、追加图片等），调整 HTML 重拍后再确认

#### 4.7 追加用户图片

用户可能在卡片之外提供自己的图片（截图、照片等），需要混合排列：
- 用户图片通常放在第一张（作为封面）或最后一张
- 将用户图片复制到素材目录，与卡片 PNG 一起发布
- 图片总数 ≤18 张（小红书限制）

#### 4.8 适配小红书正文

图片是主内容，正文作为钩子文案（≤350字）：
- 开头用引子数据或反差句吸引注意
- 简要列出 3-5 个核心点，引导滑动图片
- 加入适当 emoji（但不要每句都加）
- 末尾 CTA：点赞收藏 + 引导评论

### 步骤 5：通过 web-access 发布到小红书

使用 web-access skill 的 CDP proxy 操控用户日常 Chrome 完成发布。

#### 5.1 启动 CDP Proxy

```bash
bash ~/.claude/skills/web-access/scripts/check-deps.sh
```

如果连接失败，引导用户：
1. 在 Chrome 地址栏输入 `chrome://inspect/#remote-debugging`
2. 勾选 "Allow remote debugging for this browser instance"
3. 重启 Chrome 后重试

#### 5.2 打开发布页面

```bash
# 打开小红书创作平台发布页
curl -s "http://localhost:3456/new?url=https://creator.xiaohongshu.com/publish/publish"
```

等待页面加载后，切换到"上传图文"标签：

```bash
# 切换到上传图文
curl -s -X POST "http://localhost:3456/eval?target={TARGET_ID}" \
  -d '(() => {
    const tabs = document.querySelectorAll(".creator-tab");
    for (const t of tabs) {
      if (t.textContent.trim() === "上传图文" && !t.classList.contains("active")) {
        t.click(); return "ok";
      }
    }
  })()'
```

#### 5.3 上传图片

```bash
curl -s -X POST "http://localhost:3456/setFiles?target={TARGET_ID}" \
  -d '{
    "selector": "input.upload-input",
    "files": ["/path/to/card_1.png", "/path/to/card_2.png", ...]
  }'
```

等待图片上传完成（约 3-5 秒）。

#### 5.4 填写标题和正文

```bash
# 填写标题
curl -s -X POST "http://localhost:3456/eval?target={TARGET_ID}" \
  -d '(() => {
    const input = document.querySelector("input.d-text");
    const setter = Object.getOwnPropertyDescriptor(window.HTMLInputElement.prototype, "value").set;
    setter.call(input, "标题内容");
    input.dispatchEvent(new Event("input", { bubbles: true }));
    input.dispatchEvent(new Event("change", { bubbles: true }));
  })()'

# 填写正文
curl -s -X POST "http://localhost:3456/eval?target={TARGET_ID}" \
  -d '(() => {
    const editor = document.querySelector("div.tiptap.ProseMirror");
    editor.focus();
    document.execCommand("selectAll", false, null);
    document.execCommand("insertText", false, `正文内容`);
  })()'
```

#### 5.5 确认并发布

截图展示最终效果，等用户确认后点击发布按钮：

```bash
# 截图确认
curl -s "http://localhost:3456/screenshot?target={TARGET_ID}&file=/tmp/xhs_final.png"

# 点击发布
curl -s -X POST "http://localhost:3456/click?target={TARGET_ID}" \
  -d 'button.d-button.d-button-default.d-button-with-content.custom-button.bg-red'
```

发布后等待 3-5 秒，检查页面状态确认是否成功。

#### 5.6 清理

发布完成后关闭创建的 tab（不关闭用户原有的 tab）：

```bash
curl -s "http://localhost:3456/close?target={TARGET_ID}"
```

### 步骤 6：汇报结果

展示各平台发布结果：
- 微信：media_id + 提示去后台预览
- 小红书：发布状态 + 素材目录位置

## 单平台快捷发布

### 仅发布到微信
```bash
python3 ~/.claude/skills/multi-publish/wechat_publisher.py \
  --title "标题" --content article.html --cover cover.png
```

### 仅发布到小红书
生成卡片图片到素材目录 → 通过 web-access CDP 上传发布（见步骤 4-5）。

## 常见问题

### 微信 IP 白名单错误
登录 mp.weixin.qq.com → 设置 → 基本配置 → IP白名单 → 添加当前 IP。

### 微信 access_token 过期
脚本自动刷新，如持续失败检查 AppID/AppSecret 是否正确。

### CDP Proxy 连接失败
1. 确认 Chrome 已开启远程调试：`chrome://inspect/#remote-debugging` → 勾选允许
2. 重启 Chrome 后重试 `bash ~/.claude/skills/web-access/scripts/check-deps.sh`
3. 如果标准 Chrome DevToolsActivePort 可用，proxy 会自动发现并连接

### 图片上传失败
确保图片为 JPG/PNG 格式，≤1MB。上传后等待 3-5 秒让 XHS 处理完成再填写内容。

### 小红书发布页面报错
如果发布后出现"遇到问题"，可能是图片未完全上传。重新打开发布页，确保图片上传完成后再填写内容并发布。

## 文件结构

```
multi-publish/
├── SKILL.md              # 本文件 - Skill 定义和执行流程
├── wechat_publisher.py   # 微信公众号草稿发布脚本
└── xhs_adapter.py        # 小红书内容适配器（正文文本适配）
```

## 技术说明

- **微信发布**：使用微信公众号官方 API（OAuth2 Client Credentials），通过 AppID + AppSecret 获取 access_token，调用草稿箱接口创建草稿
- **小红书发布**：通过 web-access skill 的 CDP proxy 直接操控用户日常 Chrome，天然携带登录态，在创作者平台完成发布
- **内容适配**：卡片图片通过 card-caster 模板生成，正文通过 xhs_adapter.py 适配为小红书风格
