---
name: dev-workflow
description: 全栈开发工作流技能，覆盖 bug 修复、功能开发、Issue 处理、PR 审查
version: 1.0.0
---

# Dev Workflow Skill

## 概述
小胖开发助手的标准开发工作流，从任务理解到代码提交的全流程。

## 触发条件
- 修 bug、加功能、重构代码
- 处理 GitHub Issue
- 审查 PR
- 代码分析

## 执行流程

### Bug 修复
1. 读取相关代码 → 2. 用测试复现 → 3. 定位根因 → 4. 修复 → 5. 跑验证

### 功能开发
1. 理解需求 → 2. 读取相关代码 → 3. 列出改动文件 → 4. 实施 → 5. 跑验证 → 6. 提交

### Issue 处理
1. 读取 Issue → 2. 定位相关代码 → 3. 分析根因 → 4. 输出排查结论或修复

### PR 审查
1. 读取 PR diff → 2. 检查逻辑/安全/性能/风格 → 3. 输出审查意见

## 工具依赖
- /multi-* 命令族：多模型协作开发
- project-analyzer：深度代码分析
- GitHub MCP：Issue/PR 操作
