# Clip-Process 晋升策略

## 概述

本策略定义了 clip-process skill 从开发到生产的质量门控标准。

## 6 级门控系统

### Level 1：结构完整性（Structure Completeness）

**门控**：输出结构检查通过率

**要求**：
- 必需章节存在：`## 常青笔记`、`## 连接`、`## 行动` - 100%
- 章节顺序正确 - 100%
- frontmatter 更新正确（`状态/已整理`、`lastmod`） - 100%

**验证方法**：
```bash
python3 evals/check_structure.py --file "剪藏/xxx.md"
```

**不通过处理**：检查 Step 7 的写入逻辑

---

### Level 2：关联准确性（Connection Accuracy）

**门控**：卡片关联测试通过率

**要求**：
- 已有卡片推荐：≥95% 在 `卡片/` 目录真实存在
- 关联原因说明：100% 有具体说明（10-20字）
- 新建卡片建议：≥80% 有实际价值

**验证方法**：
```bash
python3 evals/check_connections.py --file "剪藏/xxx.md"
```

**不通过处理**：
- 检查 Step 5 的搜索逻辑
- 检查卡片存在性验证
- 更新 `failures/non-existent-cards/`

---

### Level 3：常青笔记质量（Evergreen Quality）

**门控**：常青笔记质量抽检通过率

**要求**：
- 无复述性语句（"文章认为"、"作者提出"等）：100%
- 独立命题（不依赖文章存在）：≥80%（人工抽检）
- 面向未来的知识点：≥80%（人工抽检）

**验证方法**：
```bash
python3 evals/check_evergreen.py --file "剪藏/xxx.md"
# 人工抽检：每月 10 篇
```

**不通过处理**：
- 检查 Step 6b 的生成逻辑
- 更新 `failures/summary-as-evergreen/`

---

### Level 4：行动可执行性（Action Executability）

**门控**：行动项质量检查通过率

**要求**：
- 格式正确（`- [ ]`）：100%
- 无空泛行动（"深入学习"、"了解更多"）：100%
- 具体可执行（有明确动词和对象）：≥90%

**验证方法**：
```bash
python3 evals/check_actions.py --file "剪藏/xxx.md"
```

**不通过处理**：更新 `failures/vague-actions/`

---

### Level 5：入库思考呼应（Anchor Alignment）

**门控**：入库思考呼应度人工评审

**要求**：
- 常青笔记覆盖用户打动点：≥70%（人工评审）
- 连接呼应用户当下关联：≥70%（人工评审）
- 行动基于用户锚点分析：≥70%（人工评审）

**验证方法**：
```bash
# 人工评审，每月 10 篇
python3 evals/generate_review_report.py
```

**不通过处理**：更新 `failures/ignore-user-anchor/`

---

### Level 6：稳定性（Stability）

**门控**：连续回归测试通过

**要求**：
- 连续 20 篇不同剪藏无退步
- 无新增 failure 模式
- 处理时间 <60s

**验证方法**：
```bash
python3 evals/regression_test.py --rounds 20
```

**不通过处理**：回滚到上一个稳定版本，分析退步原因

---

## 晋升流程

### 准备阶段

1. 运行全量评估套件
2. 收集评估报告
3. 修复所有 Level 1-4 的失败用例
4. 完成 Level 5 的人工评审

### 晋升检查清单

```markdown
## Clip-Process 晋升检查清单

- [ ] Level 1：结构完整性 100%
- [ ] Level 2：关联准确性 ≥95%
- [ ] Level 3：常青笔记质量 ≥80%（人工抽检）
- [ ] Level 4：行动可执行性 ≥90%
- [ ] Level 5：入库思考呼应 ≥70%（人工评审）
- [ ] Level 6：连续 20 轮无退步
- [ ] 失败案例库已更新（如有新失败模式）
- [ ] 评估报告已归档
```

### 晋升结果

| 结果 | 条件 | 处理 |
|------|------|------|
| **Promote** | 所有 Level 通过 | 更新 maturity 等级 |
| **Keep Current** | Level 1-5 通过，Level 6 有退步 | 保持当前版本，分析退步 |
| **Block** | Level 1-5 任一失败 | 修复后重新评估 |

---

## 退步原因分类

当出现退步时，使用以下标签分类原因：

| 标签 | 含义 | 示例 |
|------|------|------|
| `card_not_found` | 推荐的卡片不存在 | 卡片名拼写错误 |
| `evergreen_is_summary` | 常青笔记变成文章总结 | 复述文章观点 |
| `vague_action` | 行动项太空泛 | "深入学习" |
| `anchor_ignored` | 忽略入库思考 | 没有呼应用户打动点 |
| `structure_broken` | 结构不完整 | 缺少必需章节 |
| `frontmatter_not_updated` | frontmatter 未更新 | 状态未改为已整理 |
| `search_incomplete` | 搜索不完整 | 只搜了 1 个关键词 |
| `connection_forced` | 强行关联 | 关联不相关的卡片 |
| `unknown` | 未知原因 | 需人工分析 |

---

## 评估频率

| 场景 | 频率 | 范围 |
|------|------|------|
| 开发中 | 每次修改后 | Level 1-2 |
| 提测前 | 完整评估 | Level 1-4 |
| 发版前 | 全量回归 | Level 1-6 |
| 线上监控 | 每周 | 抽样 Level 2-4 |
| 人工评审 | 每月 | Level 5（10 篇） |
