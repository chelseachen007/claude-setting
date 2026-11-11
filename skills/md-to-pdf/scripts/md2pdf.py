#!/usr/bin/env python3
"""
md2pdf.py — Markdown 转 PDF 通用转换器
用法: python3 md2pdf.py --input <目录或文件> --output <输出PDF路径> [--title 标题] [--exclude 排除文件1,排除文件2] [--order 01-a.md,02-b.md]
"""
import markdown
from weasyprint import HTML
import os
import re
import sys
import argparse

def process_content(content):
    """清理 Obsidian 语法"""
    # 移除 frontmatter
    content = re.sub(r'^---\n[\s\S]*?\n---\n', '', content)
    # 移除 Obsidian 嵌入
    content = re.sub(r'!\[\[([^\]]+)\]\]', r'\1', content)
    # wikilink 转纯文本
    content = re.sub(r'\[\[([^\]|]+)(?:\|[^\]]+)?\]\]', r'\1', content)
    # Obsidian callout 转引用块
    callout_names = {
        'info': '信息', 'important': '重要', 'warning': '注意', 'tip': '提示',
        'quote': '引用', 'example': '示例', 'note': '备注', 'abstract': '摘要',
        'analogy': '类比', 'success': '成功', 'failure': '失败', 'danger': '危险',
        'bug': 'Bug', 'check': '检查', 'question': '问题', 'cite': '引用',
    }
    def replace_callout(m):
        ctype = m.group(1)
        title = m.group(2)
        label = callout_names.get(ctype.lower(), ctype)
        return f'> **{label}：{title}**' if title else f'> **{label}**'
    content = re.sub(r'^> \[!(\w+)\]\s*(.*)$', replace_callout, content, flags=re.MULTILINE)
    # Dataview 代码块转普通代码块
    content = re.sub(r'```dataview\n', '```\n', content)
    # 连续分隔线合并
    content = re.sub(r'\n---\s*\n---\s*\n', '\n---\n', content)
    return content.strip()

def collect_files(source, exclude=None, order=None):
    """收集待处理文件"""
    if os.path.isfile(source):
        return [source]

    if order:
        return [os.path.join(source, f) for f in order if os.path.exists(os.path.join(source, f))]

    all_files = sorted([
        os.path.join(source, f)
        for f in os.listdir(source)
        if f.endswith('.md') and not f.startswith('.')
    ])

    if exclude:
        def should_exclude(f):
            basename = os.path.basename(f)
            for pat in exclude:
                if pat.lower() in basename.lower():
                    return True
            return False
        all_files = [f for f in all_files if not should_exclude(f)]

    return all_files

CSS = """
@page {
  size: A4;
  margin: 2.5cm 2cm;
  @bottom-center {
    content: counter(page);
    font-size: 10px;
    color: #666;
  }
}
body {
  font-family: "PingFang SC", "Hiragino Sans GB", "Microsoft YaHei", "Noto Sans CJK SC", sans-serif;
  font-size: 11pt;
  line-height: 1.8;
  color: #333;
}
h1 {
  font-size: 22pt;
  color: #1a1a1a;
  border-bottom: 3px solid #2c5f2d;
  padding-bottom: 10px;
  margin-top: 40px;
  page-break-before: always;
}
h1:first-of-type {
  page-break-before: avoid;
  text-align: center;
  font-size: 28pt;
  border: none;
  padding-top: 200px;
  color: #2c5f2d;
}
h2 {
  font-size: 16pt;
  color: #2c5f2d;
  margin-top: 30px;
  border-left: 4px solid #2c5f2d;
  padding-left: 12px;
}
h3 { font-size: 13pt; color: #3a7d3e; margin-top: 20px; }
h4 { font-size: 12pt; color: #555; margin-top: 15px; }
p { margin: 8px 0; text-align: justify; }
blockquote {
  border-left: 4px solid #2c5f2d;
  background: #f5f9f5;
  padding: 12px 16px;
  margin: 16px 0;
  border-radius: 4px;
  font-size: 10.5pt;
}
blockquote p { margin: 4px 0; }
strong { color: #1a1a1a; }
code {
  background: #f0f0f0;
  padding: 2px 6px;
  border-radius: 3px;
  font-size: 10pt;
  font-family: "SF Mono", "Fira Code", "Menlo", monospace;
}
pre {
  background: #f8f8f8;
  border: 1px solid #e0e0e0;
  border-radius: 6px;
  padding: 14px;
  overflow-x: auto;
  font-size: 9.5pt;
  line-height: 1.5;
  page-break-inside: avoid;
}
pre code { background: none; padding: 0; }
table {
  border-collapse: collapse;
  width: 100%;
  margin: 16px 0;
  font-size: 10pt;
  page-break-inside: avoid;
}
th { background: #2c5f2d; color: white; padding: 10px 12px; text-align: left; font-weight: 600; }
td { padding: 8px 12px; border-bottom: 1px solid #e0e0e0; }
tr:nth-child(even) { background: #f9f9f9; }
hr { border: none; border-top: 1px solid #ddd; margin: 30px 0; }
ul, ol { padding-left: 24px; margin: 8px 0; }
li { margin: 4px 0; }
"""

def main():
    parser = argparse.ArgumentParser(description='Markdown 转 PDF')
    parser.add_argument('--input', required=True, help='输入：.md 文件或目录路径')
    parser.add_argument('--output', required=True, help='输出 PDF 路径')
    parser.add_argument('--title', default='', help='文档标题')
    parser.add_argument('--exclude', default='', help='排除文件名（逗号分隔）')
    parser.add_argument('--order', default='', help='指定文件顺序（逗号分隔文件名）')
    args = parser.parse_args()

    exclude = [x.strip() for x in args.exclude.split(',') if x.strip()] if args.exclude else None
    order = [x.strip() for x in args.order.split(',') if x.strip()] if args.order else None
    title = args.title or os.path.splitext(os.path.basename(args.input))[0]

    files = collect_files(args.input, exclude=exclude, order=order)
    print(f"找到 {len(files)} 个文件待处理")

    # 合并
    combined = f"# {title}\n\n"
    for fpath in files:
        with open(fpath, 'r', encoding='utf-8') as f:
            content = f.read()
        processed = process_content(content)
        combined += processed + '\n\n<hr/>\n\n'

    # Markdown → HTML → PDF
    html_body = markdown.markdown(combined, extensions=['tables', 'fenced_code', 'toc'])
    html = f'<!DOCTYPE html>\n<html lang="zh-CN"><head><meta charset="UTF-8"><style>{CSS}</style></head><body>{html_body}</body></html>'

    # 确保输出目录存在
    os.makedirs(os.path.dirname(os.path.abspath(args.output)), exist_ok=True)

    HTML(string=html).write_pdf(args.output)
    size_kb = os.path.getsize(args.output) / 1024
    print(f"PDF 已生成: {args.output} ({size_kb:.1f} KB)")

if __name__ == '__main__':
    main()
