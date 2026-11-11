# Clip-Process 失败案例库

## 概述

本目录记录 clip-process 的已知失败模式，用于：
1. **回归测试**：每次修改后验证不引入新问题
2. **模式学习**：理解失败的根本原因
3. **持续改进**：基于真实失败优化策略

## 目录结构

```
failures/
├── README.md                              # 本文件
├── summary-as-evergreen/                  # 常青笔记变成文章总结
│   ├── README.md                          # 反模式文档
│   └── cases.json                         # 回归用例
├── non-existent-cards/                    # 推荐不存在的卡片
│   ├── README.md
│   └── cases.json
├── vague-actions/                         # 行动项太空泛
│   ├── README.md
│   └── cases.json
├── ignore-user-anchor/                    # 忽略入库思考
│   ├── README.md
│   └── cases.json
└── forced-connections/                    # 强行关联不相关卡片
    ├── README.md
    └── cases.json
```

## 如何使用

### 1. 发现新失败模式时

```bash
# 1. 创建新的失败案例目录
mkdir -p failures/new-failure-mode

# 2. 编写 README.md（参考模板）
# 3. 创建 cases.json（回归用例）
# 4. 运行回归测试验证
python3 evals/regression_test.py --failures-only
```

### 2. 修改 skill 后验证

```bash
# 运行所有失败案例的回归测试
python3 evals/regression_test.py --failures-dir failures/

# 只运行特定类型的失败案例
python3 evals/regression_test.py --failures-dir failures/summary-as-evergreen/
```

### 3. 每周回归

```bash
# 全量回归（包括正常用例 + 失败案例）
python3 evals/regression_test.py --full --report reports/weekly-$(date +%Y%m%d).md
```

## 如何贡献

### 新增失败案例

1. **复现问题**：确认是可复现的失败
2. **分析根因**：找到失败的根本原因
3. **创建案例**：
   - `README.md`：症状、反模式、原因、修复方案
   - `cases.json`：回归用例和断言
4. **验证修复**：修复后确保案例通过
5. **保留案例**：即使修复了，案例保留用于回归

### README.md 模板

```markdown
# 反模式：[失败模式名称]

## 症状（Symptom）
[描述用户看到的现象]

## 反模式（Anti-Pattern）
[描述 AI 的错误行为]

## 示例 Prompt
输入：[用户输入]
错误行为：[AI 的错误响应]
正确行为：[期望的正确响应]

## 为什么失败（Why It Fails）
[根因分析]

## 修复方案（Fix）
[如何修复，包括代码/配置修改]

## 回归用例（Regression Prompts）
- [测试用例 1]
- [测试用例 2]
```

### cases.json 格式

```json
{
  "should_trigger": [],
  "should_not_trigger": [],
  "near_neighbor": [
    {
      "text": "用户输入",
      "family": "failure_family_name",
      "expected_behavior": "期望行为",
      "common_mistake": "常见错误"
    }
  ],
  "regression_assertions": [
    {
      "input_pattern": "匹配模式",
      "assertion": "必须满足的条件",
      "severity": "critical/high/medium/low"
    }
  ]
}
```

## 失败家族（Failure Families）

| Family | 含义 | 典型症状 |
|--------|------|---------|
| `summary_as_evergreen` | 常青笔记变成文章总结 | "文章认为..."、"作者提出..." |
| `non_existent_cards` | 推荐不存在的卡片 | 点击链接跳转到空页面 |
| `vague_actions` | 行动项太空泛 | "深入学习"、"了解更多" |
| `ignore_user_anchor` | 忽略入库思考 | 常青笔记与用户打动点无关 |
| `forced_connections` | 强行关联不相关卡片 | 关联原因泛泛（"主题相关"） |
| `structure_broken` | 结构不完整 | 缺少必需章节 |
| `frontmatter_not_updated` | frontmatter 未更新 | 状态未改为已整理 |
| `search_incomplete` | 搜索不完整 | 只搜了 1 个关键词 |

## 最佳实践

1. **真实案例优先**：优先记录线上真实失败，而非构造的边界 case
2. **根因要深挖**：不要只记录症状，要找到根本原因
3. **回归要自动化**：每个失败案例必须有可自动运行的回归用例
4. **保留不删除**：即使问题修复了，案例保留用于防止回归
5. **定期清理**：每季度 review 一次，合并重复的失败模式

## 统计仪表盘

```bash
# 查看失败案例统计
python3 scripts/failure_stats.py

# 输出示例：
# 失败案例总数：18
# - summary_as_evergreen: 6 (33%)
# - non_existent_cards: 5 (28%)
# - vague_actions: 4 (22%)
# - 其他: 3 (17%)
#
# 最近 30 天新增：2
# 已修复但保留：14
# 待修复：4
```
