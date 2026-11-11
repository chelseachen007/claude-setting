# Clip-and-Process 评估体系

## 概述

本评估体系用于确保 clip-and-process 作为智能路由器的可靠性和准确性。

## 评估维度

### 1. 触发评估（Trigger Eval）
评估"什么时候应该触发这个 skill"。

- **should_trigger**：URL + 剪藏意图的输入
- **should_not_trigger**：处理已有剪藏、查看剪藏列表等
- **near_neighbor**：只是打开链接、翻译文章等

配置：`trigger_cases.json` + `semantic_config.json`

### 2. 路由准确性评估（Routing Eval）
评估"平台识别和内容类型判断是否准确"。

- 平台识别：小红书/B站/抖音/YouTube/通用网页
- 内容类型：文章/视频/图文/音频
- 降级策略：Layer 1 → Layer 2 → Layer 3

配置：`routing_cases.json`

### 3. 提取成功率评估（Extraction Eval）
评估"内容提取是否成功"。

- 内容非空（>100字）
- 标题存在
- 结构完整（有必需章节）
- 图片/视频提取成功

### 4. 整体流程完整性（End-to-End Eval）
评估"从 URL 到保存的完整流程"。

- 文件保存成功
- frontmatter 正确
- 状态标记正确
- 错误时有降级提示

## 晋升策略

详见 `promotion_policy.md`

## 使用方法

### 运行触发评估
```bash
python3 evals/check_trigger.py
```

### 运行路由评估
```bash
python3 evals/check_routing.py
```

### 运行全流程评估
```bash
python3 evals/check_e2e.py --url "https://xxx"
```

## 维护指南

1. **新增平台**：在 `routing_cases.json` 添加测试用例
2. **新失败模式**：在 `failures/` 添加案例，同步到 `trigger_cases.json`
3. **每周回归**：运行全量评估，对比历史结果
