#!/usr/bin/env python3
"""
间隔重复复习脚本
基于笔记创建日期计算复习节点：+1, +3, +7, +30, +90 天
"""

import os
import re
from datetime import datetime, date
from pathlib import Path
import json

# 复习间隔（天）
REVIEW_INTERVALS = [1, 3, 7, 30, 90]

def find_obsidian_vault():
    """查找 Obsidian Vault 路径"""
    # 优先使用环境变量
    if os.environ.get('OBSIDIAN_VAULT_PATH'):
        return Path(os.environ['OBSIDIAN_VAULT_PATH'])

    # 常见路径
    candidates = [
        Path.home() / 'Documents' / 'study' / 'github' / 'Obsidian',
        Path.home() / 'Obsidian',
        Path.home() / 'Documents' / 'Obsidian',
        Path.home() / 'Library' / 'Mobile Documents' / 'iCloud~md~obsidian' / 'Documents',
    ]

    for path in candidates:
        if path.exists():
            return path

    return None

def parse_frontmatter(content: str) -> dict:
    """解析 Markdown 文件的 YAML frontmatter"""
    if not content.startswith('---'):
        return {}

    # 提取 frontmatter
    match = re.match(r'^---\s*\n(.*?)\n---', content, re.DOTALL)
    if not match:
        return {}

    frontmatter_text = match.group(1)
    result = {}

    # 简单解析 YAML
    for line in frontmatter_text.split('\n'):
        if ':' in line:
            key, value = line.split(':', 1)
            key = key.strip()
            value = value.strip()

            # 处理日期
            if key in ['date', 'lastmod'] and value:
                try:
                    result[key] = datetime.strptime(value, '%Y-%m-%d').date()
                except:
                    result[key] = value
            else:
                result[key] = value

    return result

def get_review_nodes(create_date: date, today: date) -> list:
    """计算已经到达的复习节点"""
    days_passed = (today - create_date).days
    reached_nodes = []

    for i, interval in enumerate(REVIEW_INTERVALS):
        if days_passed >= interval:
            # 检查今天是否正好是这个节点（允许±1天容差）
            if abs(days_passed - interval) <= 1:
                reached_nodes.append({
                    'node': i + 1,
                    'interval': interval,
                    'days_passed': days_passed
                })

    return reached_nodes

def scan_cards(vault_path: Path) -> list:
    """扫描卡片目录，返回需要复习的笔记列表"""
    cards_dir = vault_path / '卡片'
    if not cards_dir.exists():
        return []

    today = date.today()
    review_cards = []

    for md_file in cards_dir.glob('**/*.md'):
        try:
            content = md_file.read_text(encoding='utf-8')
            frontmatter = parse_frontmatter(content)

            if 'date' not in frontmatter:
                continue

            create_date = frontmatter['date']
            if not isinstance(create_date, date):
                continue

            nodes = get_review_nodes(create_date, today)
            if nodes:
                review_cards.append({
                    'path': str(md_file.relative_to(vault_path)),
                    'title': frontmatter.get('title', md_file.stem),
                    'create_date': create_date.isoformat(),
                    'review_nodes': nodes,
                    'content': content
                })
        except Exception as e:
            continue

    # 按复习节点排序（优先复习更早的节点）
    review_cards.sort(key=lambda x: x['review_nodes'][0]['interval'])
    return review_cards

def main():
    """主函数"""
    vault_path = find_obsidian_vault()
    if not vault_path:
        print(json.dumps({'error': '未找到 Obsidian Vault'}))
        return

    review_cards = scan_cards(vault_path)

    result = {
        'vault_path': str(vault_path),
        'today': date.today().isoformat(),
        'total_cards': len(review_cards),
        'cards': review_cards
    }

    print(json.dumps(result, ensure_ascii=False, indent=2))

if __name__ == '__main__':
    main()
