---
name: prompt-templates
description: AI 生图提示词模板库，按风格分类管理常用提示词
version: 1.0.0
---

# Prompt Templates Skill

## 概述
提示词模板管理技能。将常用风格的提示词存储为模板，生图时自动检索匹配。

## 触发条件
- 用户要求生成指定风格的图片
- 用户提到特定风格关键词

## 执行流程
1. 读取 `references/templates.md` 中的所有模板
2. 匹配用户描述的风格关键词
3. 用模板拼接完整提示词
4. 调用生图工具执行

## 添加模板
用户反馈某次生成效果好时，记录到 `references/templates.md`。

## 参考文件
- `references/templates.md` — 提示词模板库
