# Clip-and-Process 晋升策略

## 概述

本策略定义了 clip-and-process skill 从开发到生产的质量门控标准。

## 6 级门控系统

### Level 1：触发准确性（Trigger Accuracy）

**门控**：触发评估通过率

**要求**：
- `should_trigger` 用例：100% 召回
- `should_not_trigger` 用例：100% 精确
- `near_neighbor` 用例：≥80% 正确路由

**验证方法**：
```bash
python3 evals/check_trigger.py --threshold 0.35
```

**不通过处理**：调整 `semantic_config.json` 权重或添加排除规则

---

### Level 2：平台识别准确性（Platform Recognition）

**门控**：平台识别测试通过率

**要求**：
- 已支持平台（小红书/B站/抖音/YouTube/Twitter/微信/飞书）：100% 准确
- 通用网页：100% 正确路由到三层降级
- 短链接解析：100% 成功

**验证方法**：
```bash
python3 evals/check_routing.py --platform all
```

**不通过处理**：检查 URL 正则匹配逻辑，更新 `routing_cases.json`

---

### Level 3：内容提取成功率（Extraction Success）

**门控**：内容提取测试通过率

**要求**：
- 文章类 URL：≥95% 提取成功（内容 >100字）
- 视频类 URL：≥90% 有字幕或转录
- 图文类 URL：≥85% 图片 OCR 成功
- 本地文件：100% 提取成功

**验证方法**：
```bash
python3 evals/check_extraction.py --sample-size 20
```

**不通过处理**：
- 检查对应平台的策略文件
- 检查降级逻辑是否正确执行
- 更新 `failures/extraction-failure/`

---

### Level 4：翻译准确性（Translation Quality）

**门控**：英文内容翻译测试通过率

**要求**：
- 英文域名识别：100%（medium/substack/*.dev/*.io）
- 英文内容检测：≥95%（前200词英文占比 >60%）
- 翻译执行：100%（检测到英文必须翻译）
- 双语格式：100%（原文 + 译文）

**验证方法**：
```bash
python3 evals/check_translation.py
```

**不通过处理**：
- 更新域名启发列表
- 检查内容采样逻辑
- 更新 `failures/translation-missed/`

---

### Level 5：端到端完整性（End-to-End Integrity）

**门控**：完整流程测试通过率

**要求**：
- 文件保存成功：100%
- frontmatter 完整（title/date/tags/source）：100%
- 状态标记正确（`状态/未整理`）：100%
- 深度处理提示：100%
- 错误降级提示：100%

**验证方法**：
```bash
python3 evals/check_e2e.py --full-flow
```

**不通过处理**：检查 Step 3-4 的执行逻辑

---

### Level 6：稳定性（Stability）

**门控**：连续回归测试通过

**要求**：
- 连续 20 个不同 URL/文件无退步
- 无新增 failure 模式
- 性能无显著下降（提取时间 <30s）

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
3. 修复所有 Level 1-5 的失败用例

### 晋升检查清单

```markdown
## Clip-and-Process 晋升检查清单

- [ ] Level 1：触发准确性 100%
- [ ] Level 2：平台识别准确性 100%
- [ ] Level 3：内容提取成功率 ≥95%
- [ ] Level 4：翻译准确性 100%
- [ ] Level 5：端到端完整性 100%
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
| `platform_regex_changed` | 平台 URL 格式变化 | 小红书新版 URL 结构 |
| `strategy_file_bug` | 策略文件逻辑错误 | CSS 选择器失效 |
| `worker_unavailable` | Worker 不可用 | Whisper 模型加载失败 |
| `translation_api_error` | 翻译 API 异常 | baoyu-translate 超时 |
| `cdp_session_crash` | CDP 会话崩溃 | 浏览器进程 OOM |
| `short_link_resolve_fail` | 短链接解析失败 | DNS 解析超时 |
| `paywall_bypass_fail` | 付费墙绕过失败 | 新增反爬机制 |
| `ocr_accuracy_drop` | OCR 准确率下降 | 图片质量太差 |
| `unknown` | 未知原因 | 需人工分析 |

---

## 评估频率

| 场景 | 频率 | 范围 |
|------|------|------|
| 开发中 | 每次修改后 | Level 1-2 |
| 提测前 | 完整评估 | Level 1-5 |
| 发版前 | 全量回归 | Level 1-6 |
| 线上监控 | 每周 | 抽样 Level 3-5 |
