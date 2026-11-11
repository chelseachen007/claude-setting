#!/bin/bash

# Daily Learning Journal Skill
# 按照年/月/日目录结构创建行思录

# 获取当前日期
YEAR=$(date +%Y)
MONTH=$(date +%Y-%m)
DAY=$(date +%Y-%m-%d)

# 目录路径
JOURNAL_DIR="行思录"
YEAR_DIR="$JOURNAL_DIR/$YEAR"
MONTH_DIR="$YEAR_DIR/$MONTH"
FILE_PATH="$MONTH_DIR/$DAY.md"

# 创建目录结构
mkdir -p "$MONTH_DIR"

# 检查文件是否已存在
if [ -f "$FILE_PATH" ]; then
    echo "日记已存在：$FILE_PATH"
    echo "是否要追加内容？(y/n)"
    read -r answer
    if [ "$answer" != "y" ]; then
        echo "取消操作"
        exit 0
    fi
fi

# 创建或追加日记
cat >> "$FILE_PATH" << 'EOF'

---
tags: [日记, 学习总结]
date: {{DATE}}
lastmod: {{DATE}}
---

## 今日学习

<!-- 在这里记录今天学到的知识点 -->

## 问题解决

<!-- 记录遇到的问题和解决方案 -->

## 待办事项

<!-- 未完成的任务 -->

## 代码片段

<!-- 重要的代码记录 -->

## 思考与反思

<!-- 个人见解和心得 -->

EOF

# 替换日期标记
sed -i '' "s/{{DATE}}/$DAY/g" "$FILE_PATH"

echo "✅ 日记已创建：$FILE_PATH"
echo "📝 文件路径：$FILE_PATH"
