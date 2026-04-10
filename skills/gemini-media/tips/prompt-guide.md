# Gemini 媒体生成 Prompt 指南

## 图片生成 Prompt 技巧

### 基本结构

好的图片 prompt 应包含以下要素（不必全部，但越多越精确）：

- **主体**：画面核心内容
- **风格**：写实、水彩、油画、像素风、3D渲染、动漫、扁平插画等
- **构图**：特写、全身、鸟瞰、对称、黄金分割等
- **光影**：自然光、霓虹灯、逆光、黄金时刻等
- **色调**：暖色调、冷色调、莫兰迪色、高饱和等

### Prompt 示例

| 类型 | 示例 |
|------|------|
| 写实风格 | A photorealistic portrait of a young woman with freckles, soft golden hour lighting, shallow depth of field, shot on 85mm lens |
| 动漫风格 | An anime-style illustration of a girl sitting by a window watching rain, Studio Ghibli style, warm muted colors, peaceful atmosphere |
| 产品图 | A sleek wireless headphone floating in mid-air against a gradient background, minimalist product photography, studio lighting, clean composition |
| 风景 | A breathtaking mountain landscape at sunset with a crystal clear lake reflecting the sky, dramatic clouds, National Geographic style |
| UI 设计 | A modern dashboard UI design for a fitness app, dark theme, clean data visualization, Dribbble style, Figma mockup |

### 语言建议

- 英文 prompt 通常效果更好，Gemini 对英文理解更精准
- 可以用中文描述需求，再翻译成英文 prompt 发送给 Gemini
- 如果用户明确要求中文场景（如中文海报），直接用中文 prompt

## 视频生成 Prompt 技巧

### 关键要素

视频 prompt 需要额外描述**运动和变化**：

- **镜头运动**：推进、拉远、平移、跟随、环绕、航拍
- **主体运动**：走路、奔跑、飘动、旋转、变形
- **时间变化**：日出日落、季节变换、生长过程
- **节奏**：慢动作、延时摄影、正常速度

### Prompt 示例

| 类型 | 示例 |
|------|------|
| 自然风景 | Aerial shot slowly flying over a misty forest at sunrise, golden light filtering through trees, cinematic 4K quality |
| 人物动态 | A woman in a red dress walking through a field of lavender, camera following from behind, gentle breeze moving the fabric, soft focus background |
| 产品展示 | A luxury watch rotating slowly on a dark surface, dramatic spotlight creating lens flares, macro details visible, 360 degree rotation |
| 抽象动画 | Colorful ink drops falling into clear water, slow motion, swirling and mixing in organic patterns, deep blue and gold colors |
| 城市生活 | Timelapse of a busy Tokyo street at night, neon signs reflecting on wet pavement, people walking with umbrellas, cyberpunk atmosphere |

## 中文文字处理技巧

AI 图像生成对中文文字的处理有局限性，以下技巧可提高准确率。

| 技巧 | 示例 | 说明 |
|-----|------|------|
| 明确指出具体文字 | 把「肥」字改成「爬」字 | 比"修正错别字"效果好 |
| 使用引号标注 | 将「又要肥楼了」改为「又要爬楼了」 | 清晰标注原文和目标 |
| 强调只改一处 | 只改这一个字，图片其他部分完全不动 | 避免整体被重绘 |
| 一次只改一处 | 不要同时要求修改多处文字 | 降低复杂度 |

### 推荐模板

```
这张图左上角黄色对话框里写的是「原文」，请把「X」字改成「Y」字，变成「目标文字」。只改这一个字，图片其他部分完全不动。
```

**注意**：同样的提示词可能需要 2-3 次才成功，AI 生成有随机性。每次生成后务必检查文字是否正确。

## 图生图/编辑技巧

### 修改局部

```
修改这张图片：只把背景从白色改成渐变蓝色，其他部分完全保持不变
```

### 风格转换

```
把这张照片转换成水彩画风格，保持构图和内容不变
```

### 添加元素

```
在这张图片的右上角添加一个红色的蝴蝶结，不影响其他区域
```

### 超分辨率

```
将这张图片提升清晰度，保持所有细节不变，增强边缘锐度
```

## 通用注意事项

1. **多次尝试**：AI 生成有随机性，不满意可以重新生成
2. **逐步迭代**：复杂修改分步进行，每步确认后再进行下一步
3. **简洁明了**：避免过于复杂的指令，一次聚焦一个目标
4. **反向描述**：有时描述"不要什么"比"要什么"更有效
