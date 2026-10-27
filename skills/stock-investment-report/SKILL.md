---
name: stock-investment-report
description: 个股投资分析报告生成技能，包含评分体系和报告模板
version: 1.0.0
---

# Stock Investment Report Skill

## 概述
基于多维数据的专业个股投资分析报告生成技能。从数据获取到评分输出，全流程标准化。

## 触发条件
- 用户要求分析个股
- 用户要求对比多只股票
- 用户要求行业/板块分析

## 执行流程
1. 读取 `references/investment_framework.md` 了解评分体系
2. 调用 cn-finance-toolkit 获取数据
3. 按评分体系逐项分析（基本面、估值、资金、技术、风险）
4. 按 `references/report_template.md` 格式输出报告
5. 附加投资评分和操作建议

## 参考文件
- `references/investment_framework.md` — 多维评分体系
- `references/report_template.md` — 标准报告模板

## 工具依赖
- cn-finance-toolkit：行情、财务、宏观数据
- stock-debate-analysis：多空辩论（可选）
