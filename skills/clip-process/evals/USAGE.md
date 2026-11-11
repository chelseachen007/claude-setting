# Clip-Process 评估脚本使用指南

## 脚本概览

| 脚本 | 用途 | 用法 |
|------|------|------|
| `check_trigger.py` | 触发准确性评估 | `python3 check_trigger.py` |
| `check_output.py` | 输出质量评估 | `python3 check_output.py --file "剪藏/xxx.md"` |
| `collect_samples.py` | 样本收集 | `python3 collect_samples.py --file "剪藏/xxx.md" --result success/failure` |

## 1. 触发评估

评估"什么时候应该触发 clip-process"。

```bash
# 运行所有触发用例
cd ~/.agents/skills/clip-process/evals
python3 check_trigger.py

# 指定阈值
python3 check_trigger.py --threshold 0.35

# 输出报告到目录
python3 check_trigger.py --report reports/
```

**预期输出**：
```
============================================================
Clip-Process 触发评估报告
============================================================
时间: 2026-07-15T10:30:00
阈值: 0.35
总体得分: 95.00%

分项得分:
  should_trigger:     7/7
  should_not_trigger: 8/8
  near_neighbor:      5/5

✅ 触发评估通过
```

## 2. 输出质量评估

评估"深度处理的产出质量"。

### 评估单个文件

```bash
python3 check_output.py --file "剪藏/2026-07-15-xxx.md"

# 指定卡片目录
python3 check_output.py --file "剪藏/2026-07-15-xxx.md" --cards-dir "卡片/"

# 输出报告
python3 check_output.py --file "剪藏/2026-07-15-xxx.md" --report reports/
```

### 评估目录下所有已整理的文件

```bash
python3 check_output.py --dir "剪藏/"

# 输出报告
python3 check_output.py --dir "剪藏/" --report reports/
```

**预期输出**：
```
============================================================
Clip-Process 输出质量评估报告
============================================================
时间: 2026-07-15T10:30:00
总文件数: 10
通过: 8
失败: 2
总体得分: 85.00%

失败文件 (2 个):
  1. 剪藏/2026-07-10-xxx.md
     得分: 60.00%
     - evergreen: 40.00%
     - connections: 50.00%
  2. 剪藏/2026-07-08-xxx.md
     得分: 55.00%
     - actions: 33.33%

报告已保存: reports/output_eval_20260715.json

============================================================
```

## 3. 样本收集

收集真实的剪藏处理样本，用于后续分析和评估。

### 成功样本

```bash
python3 collect_samples.py \
  --file "剪藏/2026-07-15-xxx.md" \
  --result success \
  --output samples/
```

### 失败样本

```bash
# 自动识别失败家族
python3 collect_samples.py \
  --file "剪藏/2026-07-15-xxx.md" \
  --result failure \
  --output samples/

# 指定失败家族
python3 collect_samples.py \
  --file "剪藏/2026-07-15-xxx.md" \
  --result failure \
  --family summary_as_evergreen \
  --output samples/

# 带详细信息
python3 collect_samples.py \
  --file "剪藏/2026-07-15-xxx.md" \
  --result failure \
  --family vague_actions \
  --details '{"action": "深入学习时间管理", "reason": "too_vague"}' \
  --output samples/
```

### 生成统计报告

```bash
python3 collect_samples.py --report --output samples/
```

**预期输出**：
```
============================================================
Clip-Process 样本统计报告
============================================================
总样本数: 30
成功: 25
失败: 5

失败家族:
  summary_as_evergreen: 2
  vague_actions: 2
  non_existent_cards: 1

最近样本:
  2026-07-15T10:30:00: success
  2026-07-15T10:25:00: failure (summary_as_evergreen)
  2026-07-15T10:20:00: success
```

## 4. 工作流程

### 日常使用

1. **每次处理剪藏后**：记录结果
   ```bash
   # 成功
   python3 collect_samples.py --file "剪藏/xxx.md" --result success

   # 失败
   python3 collect_samples.py --file "剪藏/xxx.md" --result failure
   ```

2. **每周回归**：运行评估
   ```bash
   python3 check_trigger.py --report reports/
   python3 check_output.py --dir "剪藏/" --report reports/
   ```

3. **每月分析**：查看样本统计
   ```bash
   python3 collect_samples.py --report --output samples/
   ```

### 修改 skill 后

1. **运行全量评估**
   ```bash
   python3 check_trigger.py
   python3 check_output.py --dir "剪藏/"
   ```

2. **对比历史报告**
   ```bash
   diff reports/output_eval_20260701.json reports/output_eval_20260715.json
   ```

3. **检查失败样本**
   ```bash
   # 查看新增失败
   ls -lt samples/failure_*.json | head -5
   ```

## 5. 目录结构

```
evals/
├── check_trigger.py           # 触发评估脚本
├── check_output.py            # 输出质量评估脚本
├── collect_samples.py         # 样本收集脚本
├── USAGE.md                   # 本文件
├── trigger_cases.json         # 触发评估用例
├── semantic_config.json       # 语义配置
├── output_cases.json          # 输出质量评估用例
├── promotion_policy.md        # 晋升策略
├── reports/                   # 评估报告（自动生成）
│   ├── trigger_eval_20260715.json
│   └── output_eval_20260715.json
└── samples/                   # 收集的样本
    ├── clip_process_success_20260715.json
    ├── clip_process_failure_20260715.json
    ├── summary_as_evergreen/
    │   └── clip_process_failure_20260715.json
    ├── vague_actions/
    └── non_existent_cards/
```

## 6. 评估维度说明

### 输出质量评估维度

| 维度 | 权重 | 检查内容 |
|------|------|---------|
| 结构完整性 | 25% | 是否包含常青笔记、连接、行动章节 |
| 常青笔记质量 | 20% | 是否包含复述性语句（"文章认为"等） |
| 关联准确性 | 30% | 推荐的卡片是否真实存在 |
| 行动可执行性 | 15% | 是否包含空泛行动（"深入学习"等） |
| frontmatter | 10% | 状态是否更新、是否有 lastmod |

### 失败家族说明

| 家族 | 含义 | 典型症状 |
|------|------|---------|
| `summary_as_evergreen` | 常青笔记变成文章总结 | "文章认为..."、"作者提出..." |
| `non_existent_cards` | 推荐不存在的卡片 | 点击链接跳转到空页面 |
| `vague_actions` | 行动项太空泛 | "深入学习"、"了解更多" |
| `ignore_user_anchor` | 忽略入库思考 | 常青笔记与用户打动点无关 |
| `forced_connections` | 强行关联不相关卡片 | 关联原因泛泛（"主题相关"） |

## 7. 常见问题

### Q: 输出评估脚本报错"Ambiguous option"怎么办？

A: 这是 argparse 的参数冲突问题。使用完整的参数名（`--file` 而非 `-f`）。

### Q: 如何添加新的测试用例？

A: 编辑 `output_cases.json`，添加新的用例和断言。

### Q: 如何添加新的失败家族？

A: 在 `collect_samples.py` 的 `identify_failure_family()` 函数中添加新的家族和指标。

### Q: 样本收集后怎么用？

A: 用于：
1. 分析失败模式
2. 优化评估用例
3. 改进 skill 策略
4. 生成月度报告

## 8. 最佳实践

1. **真实样本优先**：优先收集真实失败，而非构造边界 case
2. **及时记录**：每次处理剪藏后立即记录结果
3. **定期回归**：每周运行一次全量评估
4. **分析失败**：每月分析失败样本，找出改进点
5. **持续迭代**：基于样本优化评估用例和 skill 策略

## 9. 人工评审

对于常青笔记质量和入库思考呼应度，需要人工评审。

### 评审清单

```markdown
## 常青笔记质量评审

- [ ] 是否是独立命题（不依赖文章存在）
- [ ] 是否是面向未来的知识点
- [ ] 是否覆盖用户打动点
- [ ] 是否有复述性语句

## 入库思考呼应度评审

- [ ] 常青笔记是否覆盖打动点
- [ ] 连接是否呼应当下关联
- [ ] 行动是否基于用户锚点
```

### 评审流程

1. 每月抽取 10 篇已处理的剪藏
2. 按评审清单逐项打分
3. 计算平均得分
4. 记录改进建议
