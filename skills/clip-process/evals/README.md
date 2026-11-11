# Clip-Process 评估体系

## 概述

本评估体系用于确保 clip-process 作为深度处理 worker 的质量和可靠性。

## 评估维度

### 1. 触发评估（Trigger Eval）
评估"什么时候应该触发这个 skill"。

- **should_trigger**：明确要处理已有剪藏的输入
- **should_not_trigger**：剪藏新 URL、查看剪藏列表等
- **near_neighbor**：编辑剪藏（但不处理）、总结文章（不是剪藏流程）

配置：`trigger_cases.json` + `semantic_config.json`

### 2. 输出评估（Output Eval）
评估"深度处理的产出质量"。

- **结构完整性**：是否包含所有必需章节
- **关联准确性**：推荐的卡片是否真实存在
- **常青笔记质量**：是否是持久洞见而非文章总结
- **行动可执行性**：是否具体可执行
- **入库思考呼应**：是否呼应用户的入库思考

配置：`output_cases.json`

### 3. 关联准确性评估（Connection Eval）
评估"推荐的卡片连接是否准确"。

- **已有卡片存在**：`[[卡片名]]` 在 `卡片/` 目录真实存在
- **关联性验证**：推荐的卡片与文章内容真正相关
- **新建卡片合理**：建议的新建卡片有实际价值

## 晋升策略

详见 `promotion_policy.md`

## 使用方法

### 运行触发评估
```bash
python3 evals/check_trigger.py
```

### 运行输出评估
```bash
python3 evals/check_output.py --file "剪藏/xxx.md"
```

### 运行关联准确性评估
```bash
python3 evals/check_connections.py --file "剪藏/xxx.md"
```

### 运行全流程评估
```bash
python3 evals/check_e2e.py --file "剪藏/xxx.md"
```

## 维护指南

1. **新增失败模式**：在 `failures/` 添加案例，同步到 `trigger_cases.json`
2. **每周回归**：运行全量评估，对比历史结果
3. **人工抽检**：每月抽检 10 篇处理后的剪藏，评估常青笔记质量
