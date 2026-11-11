#!/usr/bin/env python3
"""
Clip-Process 输出质量评估脚本

用法：
  python3 check_output.py --file "剪藏/xxx.md"           # 评估单个文件
  python3 check_output.py --dir "剪藏/"                    # 评估目录下所有已整理的文件
  python3 check_output.py --file "剪藏/xxx.md" --report reports/  # 输出报告
"""

import json
import re
import sys
from pathlib import Path
from datetime import datetime

def load_json(file_path):
    """加载 JSON 文件"""
    with open(file_path, 'r', encoding='utf-8') as f:
        return json.load(f)

def read_file(file_path):
    """读取文件内容"""
    with open(file_path, 'r', encoding='utf-8') as f:
        return f.read()

def extract_section(content, section_name):
    """提取指定章节内容"""
    pattern = rf'## {re.escape(section_name)}\s*\n(.*?)(?=\n## |\Z)'
    match = re.search(pattern, content, re.DOTALL)
    return match.group(1).strip() if match else ''

def extract_wikilinks(content):
    """提取所有 wikilinks"""
    pattern = r'\[\[([^\]]+)\]\]'
    return re.findall(pattern, content)

def check_structure(content):
    """检查结构完整性"""

    required_sections = ['常青笔记', '连接', '行动']
    optional_sections = ['闪念', '入库思考']

    results = {
        'passed': True,
        'required': {},
        'optional': {},
        'score': 0.0
    }

    # 检查必需章节
    for section in required_sections:
        section_content = extract_section(content, section)
        exists = bool(section_content)
        results['required'][section] = {
            'exists': exists,
            'content_length': len(section_content)
        }
        if not exists:
            results['passed'] = False

    # 检查可选章节
    for section in optional_sections:
        section_content = extract_section(content, section)
        results['optional'][section] = {
            'exists': bool(section_content),
            'content_length': len(section_content)
        }

    # 计算得分
    required_passed = sum(1 for v in results['required'].values() if v['exists'])
    results['score'] = required_passed / len(required_sections)

    return results

def check_evergreen_quality(content):
    """检查常青笔记质量"""

    evergreen_content = extract_section(content, '常青笔记')

    forbidden_phrases = [
        '文章认为', '作者提出', '本文总结',
        '文章介绍了', '作者认为', '这篇文章讲了',
        '原文提到', '文中指出'
    ]

    results = {
        'passed': True,
        'forbidden_phrases_found': [],
        'score': 1.0
    }

    # 检查禁止的短语
    for phrase in forbidden_phrases:
        if phrase in evergreen_content:
            results['forbidden_phrases_found'].append(phrase)
            results['passed'] = False

    # 计算得分
    if results['forbidden_phrases_found']:
        results['score'] = max(0, 1 - len(results['forbidden_phrases_found']) * 0.2)

    return results

def check_connection_accuracy(content, cards_dir):
    """检查关联准确性"""

    connection_content = extract_section(content, '连接')
    wikilinks = extract_wikilinks(connection_content)

    results = {
        'passed': True,
        'total_links': len(wikilinks),
        'existing_cards': [],
        'missing_cards': [],
        'score': 1.0
    }

    # 检查每个链接是否存在
    for link in wikilinks:
        card_path = Path(cards_dir) / f"{link}.md"
        if card_path.exists():
            results['existing_cards'].append(link)
        else:
            results['missing_cards'].append(link)
            results['passed'] = False

    # 计算得分
    if results['total_links'] > 0:
        results['score'] = len(results['existing_cards']) / results['total_links']

    return results

def check_action_executability(content):
    """检查行动可执行性"""

    action_content = extract_section(content, '行动')

    vague_phrases = [
        '深入学习', '了解更多', '研究一下',
        '继续关注', '后续跟进', '进一步'
    ]

    results = {
        'passed': True,
        'total_actions': 0,
        'vague_actions': [],
        'specific_actions': [],
        'score': 1.0
    }

    # 提取行动项
    action_pattern = r'- \[ \] (.+)'
    actions = re.findall(action_pattern, action_content)

    results['total_actions'] = len(actions)

    # 检查每个行动项
    for action in actions:
        is_vague = any(phrase in action for phrase in vague_phrases)
        if is_vague:
            results['vague_actions'].append(action)
            results['passed'] = False
        else:
            results['specific_actions'].append(action)

    # 计算得分
    if results['total_actions'] > 0:
        results['score'] = len(results['specific_actions']) / results['total_actions']

    return results

def check_frontmatter(content):
    """检查 frontmatter"""

    results = {
        'passed': True,
        'has_frontmatter': False,
        'has_status_updated': False,
        'has_lastmod': False,
        'score': 0.0
    }

    # 检查是否有 frontmatter
    if content.startswith('---'):
        results['has_frontmatter'] = True

        # 提取 frontmatter
        frontmatter_match = re.search(r'^---\s*\n(.*?)\n---', content, re.DOTALL)
        if frontmatter_match:
            frontmatter = frontmatter_match.group(1)

            # 检查状态是否更新
            if '状态/已整理' in frontmatter:
                results['has_status_updated'] = True

            # 检查是否有 lastmod
            if 'lastmod:' in frontmatter:
                results['has_lastmod'] = True

    # 计算得分
    checks = [results['has_frontmatter'], results['has_status_updated'], results['has_lastmod']]
    results['score'] = sum(checks) / len(checks)
    results['passed'] = results['score'] == 1.0

    return results

def evaluate_file(file_path, cards_dir):
    """评估单个文件"""

    content = read_file(file_path)

    results = {
        'file': str(file_path),
        'timestamp': datetime.now().isoformat(),
        'checks': {},
        'overall_score': 0.0,
        'passed': False
    }

    # 运行所有检查
    results['checks']['structure'] = check_structure(content)
    results['checks']['evergreen'] = check_evergreen_quality(content)
    results['checks']['connections'] = check_connection_accuracy(content, cards_dir)
    results['checks']['actions'] = check_action_executability(content)
    results['checks']['frontmatter'] = check_frontmatter(content)

    # 计算总体得分
    weights = {
        'structure': 0.25,
        'evergreen': 0.20,
        'connections': 0.30,
        'actions': 0.15,
        'frontmatter': 0.10
    }

    total_score = sum(
        results['checks'][check]['score'] * weights[check]
        for check in weights
    )

    results['overall_score'] = total_score
    results['passed'] = total_score >= 0.7  # 70% 通过率

    return results

def generate_report(results_list, output_dir=None):
    """生成评估报告"""

    total_files = len(results_list)
    passed_files = sum(1 for r in results_list if r['passed'])
    overall_score = sum(r['overall_score'] for r in results_list) / total_files if total_files > 0 else 0

    report = {
        'timestamp': datetime.now().isoformat(),
        'total_files': total_files,
        'passed_files': passed_files,
        'failed_files': total_files - passed_files,
        'overall_score': overall_score,
        'details': results_list
    }

    print("\n" + "="*60)
    print("Clip-Process 输出质量评估报告")
    print("="*60)
    print(f"时间: {report['timestamp']}")
    print(f"总文件数: {total_files}")
    print(f"通过: {passed_files}")
    print(f"失败: {total_files - passed_files}")
    print(f"总体得分: {overall_score:.2%}")

    # 输出失败文件
    failed_files = [r for r in results_list if not r['passed']]
    if failed_files:
        print(f"\n失败文件 ({len(failed_files)} 个):")
        for i, result in enumerate(failed_files, 1):
            print(f"  {i}. {result['file']}")
            print(f"     得分: {result['overall_score']:.2%}")

            # 输出具体失败原因
            for check_name, check_result in result['checks'].items():
                if not check_result['passed']:
                    print(f"     - {check_name}: {check_result.get('score', 0):.2%}")

    # 保存报告
    if output_dir:
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)

        report_file = output_path / f"output_eval_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(report_file, 'w', encoding='utf-8') as f:
            json.dump(report, f, ensure_ascii=False, indent=2)

        print(f"\n报告已保存: {report_file}")

    print("\n" + "="*60)

    return report

def main():
    """主函数"""

    import argparse
    parser = argparse.ArgumentParser(description='Clip-Process 输出质量评估')
    parser.add_argument('--file', type=str, help='评估单个文件')
    parser.add_argument('--dir', type=str, help='评估目录下所有已整理的文件')
    parser.add_argument('--cards-dir', type=str, default='卡片/', help='卡片目录')
    parser.add_argument('--report', type=str, help='报告输出目录')
    args = parser.parse_args()

    if not args.file and not args.dir:
        print("错误：必须指定 --file 或 --dir")
        sys.exit(1)

    results_list = []

    if args.file:
        # 评估单个文件
        result = evaluate_file(args.file, args.cards_dir)
        results_list.append(result)
    else:
        # 评估目录下所有已整理的文件
        dir_path = Path(args.dir)
        for md_file in dir_path.rglob('*.md'):
            content = read_file(md_file)
            if '状态/已整理' in content:
                result = evaluate_file(md_file, args.cards_dir)
                results_list.append(result)

    # 生成报告
    report = generate_report(results_list, args.report)

    # 返回退出码
    if report['overall_score'] >= 0.7:
        print(f"\n✅ 输出质量评估通过 (得分: {report['overall_score']:.2%})")
        sys.exit(0)
    else:
        print(f"\n❌ 输出质量评估未通过 (得分: {report['overall_score']:.2%})")
        sys.exit(1)

if __name__ == '__main__':
    main()
