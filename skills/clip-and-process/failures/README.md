# Clip-and-Process 失败案例库

## 概述

本目录记录 clip-and-process 的已知失败模式，用于：
1. **回归测试**：每次修改后验证不引入新问题
2. **模式学习**：理解失败的根本原因
3. **持续改进**：基于真实失败优化策略

## 目录结构

```
failures/
├── README.md                              # 本文件
├── wrong-platform-routing/                # 平台识别错误
│   ├── README.md                          # 反模式文档
│   └── cases.json                         # 回归用例
├── content-type-misclassification/        # 内容类型误判
│   ├── README.md
│   └── cases.json
├── extraction-failure/                    # 提取失败但未降级
│   ├── README.md
│   └── cases.json
├── empty-or-truncated/                    # 提取内容为空或截断
│   ├── README.md
│   └── cases.json
├── wrong-worker-routing/                  # Worker 路由错误
│   ├── README.md
│   └── cases.json
└── translation-missed/                    # 英文内容未翻译
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
python3 evals/regression_test.py --failures-dir failures/wrong-platform-routing/
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
| `wrong_platform_routing` | 平台识别错误 | 小红书 URL 走通用网页 |
| `content_type_misclassification` | 内容类型误判 | 视频 URL 当文章处理 |
| `extraction_failure` | 提取失败未降级 | Layer 1 失败就放弃 |
| `empty_or_truncated` | 内容为空或截断 | 提取后只有标题 |
| `wrong_worker_routing` | Worker 路由错误 | 视频没调 whisper |
| `translation_missed` | 翻译遗漏 | 英文没翻译 |
| `short_link_resolve_fail` | 短链接解析失败 | b23.tv 打不开 |
| `cdp_session_crash` | CDP 会话崩溃 | 浏览器 OOM |
| `ocr_accuracy_drop` | OCR 准确率下降 | 图片文字提取错误 |
| `paywall_bypass_fail` | 付费墙绕过失败 | 无法提取付费内容 |

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
# 失败案例总数：23
# - wrong_platform_routing: 8 (35%)
# - extraction_failure: 6 (26%)
# - translation_missed: 5 (22%)
# - 其他: 4 (17%)
#
# 最近 30 天新增：3
# 已修复但保留：18
# 待修复：5
```
