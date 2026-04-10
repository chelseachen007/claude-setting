---
name: gemini-media
description: 当用户想要生成图片、画图、绘画、创建图像、AI作画、生成视频、创作视频时使用此 Skill。通过 CDP 自动化 Gemini 网页端生成图片和视频，无需 API Key，直接使用用户 Gemini 订阅。
---

# Gemini 媒体生成（CDP 方式）

通过 web-access skill 的 CDP 能力，自动化操作 Gemini 网页端（gemini.google.com）生成图片和视频。

**必须先加载 web-access skill 并遵循其指引。**

## 前置条件

1. 用户 Chrome 已打开且启用了 remote debugging（参考 web-access skill）
2. 用户已登录 Gemini（gemini.google.com）— Chrome 天然携带登录态，无需额外操作

## 判断生成类型

| 用户意图 | 类型 | Prompt 建议 |
|---------|------|------------|
| 画、生成图片、AI作画、create image | 图片生成 | 直接描述画面内容 |
| 生成视频、创作视频、create video | 视频生成 | 描述动态场景，建议加入运动、镜头等描述 |
| 修改图片、编辑图片、基于图片 | 图生图/编辑 | 先上传图片再描述修改要求 |

## 标准工作流

### 第一步：初始化 CDP 环境

```bash
bash ~/.claude/skills/web-access/scripts/check-deps.sh
```

检查通过后继续。

### 第二步：打开 Gemini

```bash
curl -s "http://localhost:3456/new?url=https://gemini.google.com/app"
```

记录返回的 `targetId`，后续所有操作都使用它。

### 第三步：确认页面状态

截图确认页面已加载且已登录：

```bash
curl -s "http://localhost:3456/screenshot?target=TARGET_ID&file=/tmp/gemini-check.png"
```

**未登录判断**：如果截图显示登录页面而非聊天界面，告知用户：

> 请在你的 Chrome 中登录 gemini.google.com，完成后告诉我继续。

### 第四步：输入 Prompt

找到输入框（contenteditable div），写入 prompt：

```bash
curl -s -X POST "http://localhost:3456/eval?target=TARGET_ID" -d '
const editor = document.querySelector(".ql-editor.textarea");
editor.focus();
editor.textContent = "YOUR_PROMPT_HERE";
editor.dispatchEvent(new Event("input", {bubbles: true}));
editor.classList.remove("ql-blank");
"prompt set";
'
```

### 第五步：发送

```bash
curl -s -X POST "http://localhost:3456/click?target=TARGET_ID" -d 'button.send-button'
```

### 第六步：等待生成完成

轮询检查响应区域是否出现图片或视频元素，每次间隔 10 秒，最多等待 120 秒：

```bash
curl -s -X POST "http://localhost:3456/eval?target=TARGET_ID" -d '
JSON.stringify({
  hasImage: !!document.querySelector("img[src*=\"googleusercontent.com/gg\"]"),
  hasVideo: !!document.querySelector("video source"),
  hasDownload: !!document.querySelector("button[aria-label=\"下载完整尺寸的图片\"], button[aria-label*=\"下载\"]"),
  loadingCount: document.querySelectorAll("[class*=loading], [class*=spinner], [class*=progress]").length
});
'
```

**判断逻辑**：
- `hasImage` 或 `hasVideo` 为 true → 生成完成
- `loadingCount > 0` → 仍在生成，继续等待
- 两者都为 false → 可能生成失败或返回了纯文字，截图检查

### 第七步：下载文件

**图片下载**：点击下载按钮（需要真实鼠标事件才能触发浏览器下载）：

```bash
curl -s -X POST "http://localhost:3456/clickAt?target=TARGET_ID" -d 'button[aria-label="下载完整尺寸的图片"]'
```

**视频下载**：查找视频下载按钮并点击，选择器可能为：

```bash
curl -s -X POST "http://localhost:3456/clickAt?target=TARGET_ID" -d 'button[aria-label*="下载"]'
```

如果页面出现下载选项菜单，截图确认后点击对应选项。

等待 5 秒后检查 `~/Downloads/` 目录：

```bash
ls -lt ~/Downloads/ | head -3
```

**下载失败兜底**：如果下载按钮点击后没有文件，回退到截图方式保存：

```bash
curl -s "http://localhost:3456/screenshot?target=TARGET_ID&file=/Users/chenjie/Downloads/gemini-generated.png"
```

### 第八步：清理

```bash
curl -s "http://localhost:3456/close?target=TARGET_ID"
```

## 图生图/编辑流程

当用户需要基于已有图片进行生成或编辑时：

1. 完成标准工作流第一步到第三步
2. 上传参考图片：

```bash
# 方法一：通过文件上传按钮
curl -s -X POST "http://localhost:3456/click?target=TARGET_ID" -d 'button[aria-label="打开文件上传菜单"]'
# 然后用 setFiles 设置文件
curl -s -X POST "http://localhost:3456/setFiles?target=TARGET_ID" -d '{"selector":"input[type=file]","files":["/path/to/image.png"]}'
```

3. 输入编辑 prompt（描述要修改的内容）
4. 继续标准工作流第五步到第八步

## Prompt 技巧

参考 `tips/prompt-guide.md`，关键要点：

- **图片生成**：详细描述画面元素、风格、构图。英文 prompt 通常效果更好
- **视频生成**：描述动态场景、运动方向、镜头变化。如 "A cat running through a flower garden, camera following from behind"
- **中文文字处理**：明确指出具体文字内容，用引号标注，一次只改一处
- **图生图编辑**：强调"只修改 XX 部分，其他保持不变"

## 边界情况处理

| 情况 | 处理方式 |
|------|---------|
| 页面显示"无法生成" | 截图查看错误信息，可能是内容策略限制，建议调整 prompt |
| 生成超时（>120秒） | 告知用户可能需要更长时间，建议手动在 Gemini 网页端查看 |
| 下载按钮未出现 | 可能是视频格式，尝试查找其他下载入口，或截图保存 |
| 当前对话已有内容 | 先导航到 `gemini.google.com/app` 开启新对话 |
| Gemini 返回纯文字 | 可能 prompt 未被识别为图片/视频请求，重新尝试更明确的描述 |

## 注意事项

- Gemini 网页端有每日生成配额，达到限制后需要等待
- 视频生成通常比图片需要更长时间（30-60秒），耐心等待
- 生成内容受 Google 内容策略约束，某些 prompt 可能被拒绝
- 每次生成后及时关闭 tab，避免占用浏览器资源
