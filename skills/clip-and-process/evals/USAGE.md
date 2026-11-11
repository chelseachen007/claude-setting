# Clip-and-Process 评估脚本使用指南

## 脚本概览

| 脚本 | 用途 | 用法 |
|------|------|------|
| `check_trigger.py` | 触发准确性评估 | `python3 check_trigger.py` |
| `check_routing.py` | 路由准确性评估 | `python3 check_routing.py` |
| `collect_samples.py` | 样本收集 | `python3 collect_samples.py --url "xxx" --result success/failure` |

## 1. 触发评估

评估"什么时候应该触发 clip-and-process"。

```bash
# 运行所有触发用例
cd ~/.agents/skills/clip-and-process/evals
python3 check_trigger.py

# 指定阈值
python3 check_trigger.py --threshold 0.35

# 输出报告到目录
python3 check_trigger.py --report reports/
```

**预期输出**：
```
============================================================
Clip-and-Process 触发评估报告
============================================================
时间: 2026-07-15T10:30:00
阈值: 0.35
总体得分: 95.00%

分项得分:
  should_trigger:     10/10
  should_not_trigger: 8/8
  near_neighbor:      5/5

✅ 触发评估通过
```

## 2. 路由准确性评估

评估"平台识别和内容类型判断是否准确"。

```bash
# 运行所有路由用例
python3 check_routing.py

# 只测试小红书
python3 check_routing.py --platform xiaohongshu

# 输出报告到目录
python3 check_routing.py --report reports/
```

**预期输出**：
```
============================================================
Clip-and-Process 路由准确性评估报告
============================================================
时间: 2026-07-15T10:30:00
总体得分: 100.00%

分项得分:
  平台识别:     14/14
  内容类型检测: 14/14
  策略选择:     14/14

✅ 路由准确性评估通过
```

## 3. 样本收集

收集真实的剪藏样本，用于后续分析和评估。

### 成功样本

```bash
# URL 样本
python3 collect_samples.py \
  --url "https://www.xiaohongshu.com/explore/xxx" \
  --result success \
  --output samples/

# 文件样本
python3 collect_samples.py \
  --file "剪藏/2026-07-15-xxx.md" \
  --result success \
  --output samples/
```

### 失败样本

```bash
# 自动识别失败家族
python3 collect_samples.py \
  --url "https://www.wsj.com/articles/xxx" \
  --result failure \
  --output samples/

# 指定失败家族
python3 collect_samples.py \
  --url "https://medium.com/@xxx/article" \
  --result failure \
  --family translation_missed \
  --output samples/

# 带详细信息
python3 collect_samples.py \
  --url "https://www.xiaohongshu.com/explore/xxx" \
  --result failure \
  --details '{"error": "platform_not_recognized", "detected_as": "generic"}' \
  --output samples/
```

### 生成统计报告

```bash
python3 collect_samples.py --report --output samples/
```

**预期输出**：
```
============================================================
样本统计报告
============================================================
总样本数: 50
成功: 42
失败: 8

按类型:
  URL: 45
  文件: 5

失败家族:
  wrong_platform_routing: 3
  extraction_failure: 2
  translation_missed: 2
  unknown: 1

最近样本:
  2026-07-15T10:30:00: success
  2026-07-15T10:25:00: failure (translation_missed)
  2026-07-15T10:20:00: success
```

## 4. 工作流程

### 日常使用

1. **每次剪藏后**：记录结果
   ```bash
   # 成功
   python3 collect_samples.py --url "xxx" --result success

   # 失败
   python3 collect_samples.py --url "xxx" --result failure
   ```

2. **每周回归**：运行评估
   ```bash
   python3 check_trigger.py --report reports/
   python3 check_routing.py --report reports/
   ```

3. **每月分析**：查看样本统计
   ```bash
   python3 collect_samples.py --report --output samples/
   ```

### 修改 skill 后

1. **运行全量评估**
   ```bash
   python3 check_trigger.py
   python3 check_routing.py
   ```

2. **对比历史报告**
   ```bash
   diff reports/trigger_eval_20260701.json reports/trigger_eval_20260715.json
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
├── check_routing.py           # 路由评估脚本
├── collect_samples.py         # 样本收集脚本
├── USAGE.md                   # 本文件
├── trigger_cases.json         # 触发评估用例
├── semantic_config.json       # 语义配置
├── routing_cases.json         # 路由评估用例
├── promotion_policy.md        # 晋升策略
├── reports/                   # 评估报告（自动生成）
│   ├── trigger_eval_20260715.json
│   └── routing_eval_20260715.json
└── samples/                   # 收集的样本
    ├── url_success_20260715.json
    ├── url_failure_20260715.json
    ├── wrong_platform_routing/
    │   └── url_failure_20260715.json
    ├── extraction_failure/
    └── translation_missed/
```

## 6. 常见问题

### Q: 评估脚本报错怎么办？

A: 检查 Python 版本（需要 3.7+）和 JSON 文件格式。

### Q: 如何添加新的测试用例？

A: 编辑 `trigger_cases.json` 或 `routing_cases.json`，添加新的用例。

### Q: 如何添加新的失败家族？

A: 在 `collect_samples.py` 的 `identify_failure_family()` 函数中添加新的家族和指标。

### Q: 样本收集后怎么用？

A: 用于：
1. 分析失败模式
2. 优化评估用例
3. 改进 skill 策略
4. 生成月度报告

## 7. 最佳实践

1. **真实样本优先**：优先收集真实失败，而非构造边界 case
2. **及时记录**：每次剪藏后立即记录结果
3. **定期回归**：每周运行一次全量评估
4. **分析失败**：每月分析失败样本，找出改进点
5. **持续迭代**：基于样本优化评估用例和 skill 策略
