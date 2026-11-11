#!/usr/bin/env node

/**
 * Daily Learning Journal Generator
 * 按照年/月/日目录结构创建行思录
 */

const fs = require('fs');
const path = require('path');

// 获取当前日期
const now = new Date();
const year = now.getFullYear();
const month = String(now.getMonth() + 1).padStart(2, '0');
const day = String(now.getDate()).padStart(2, '0');

const dateStr = `${year}-${month}-${day}`;
const monthStr = `${year}-${month}`;

// 目录路径
const journalDir = '行思录';
const yearDir = path.join(journalDir, String(year));
const monthDir = path.join(yearDir, monthStr);
const filePath = path.join(monthDir, `${dateStr}.md`);

// 创建目录结构
function ensureDir(dir) {
  if (!fs.existsSync(dir)) {
    fs.mkdirSync(dir, { recursive: true });
  }
}

// 生成日记内容
function generateJournalContent() {
  return `---
tags: [日记, 学习总结]
date: ${dateStr}
lastmod: ${dateStr}
---

## 今日学习

<!-- 在这里记录今天学到的知识点 -->



## 问题解决

<!-- 记录遇到的问题和解决方案 -->



## 待办事项

- [ ] 待办事项1
- [ ] 待办事项2



## 代码片段

\`\`\`
// 重要的代码记录
\`\`\`



## 思考与反思

<!-- 个人见解和心得 -->



---
*生成时间：${new Date().toLocaleString('zh-CN')}*
`;
}

// 主函数
function main() {
  // 确保目录存在
  ensureDir(monthDir);

  // 检查文件是否已存在
  if (fs.existsSync(filePath)) {
    console.log(`⚠️  日记已存在：${filePath}`);
    console.log('文件内容：');
    console.log('---');
    console.log(fs.readFileSync(filePath, 'utf-8'));
    console.log('---');
    console.log('如需追加内容，请手动编辑文件');
    return;
  }

  // 生成日记内容
  const content = generateJournalContent();

  // 写入文件
  fs.writeFileSync(filePath, content, 'utf-8');

  console.log('✅ 日记已创建');
  console.log(`📅 日期：${dateStr}`);
  console.log(`📁 路径：${filePath}`);
  console.log('');
  console.log('目录结构：');
  console.log(`${journalDir}/`);
  console.log(`└── ${year}/`);
  console.log(`    └── ${monthStr}/`);
  console.log(`        └── ${dateStr}.md`);
}

// 运行
main();
