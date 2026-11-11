#!/usr/bin/env python3
"""
Clip-Process 样本收集脚本

用法：
  python3 collect_samples.py --file "剪藏/xxx.md" --result success/failure
  python3 collect_samples.py --file "剪藏/xxx.md" --result failure --family summary_as_evergreen
  python3 collect_samples.py --report samples/
"""

import json
import sys
from pathlib import Path
from datetime import datetime

def load_json(file_path):
    """加载 JSON 文件"""
    with open(file_path, 'r', encoding='utf-8') as f:
        return json.load(f)

def save_json(file_path, data):
    """保存 JSON 文件"""
    with open(file_path, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

def collect_sample(file_path, result, family=None, details=None):
    """收集样本"""

    sample = {
        'timestamp': datetime.now().isoformat(),
        'input': file_path,
        'result': result,
        'failure_family': family,
        'details': details or {},
        'evaluated': False
    }

    return sample

def identify_failure_family(content):
    """识别失败家族"""

    failure_indicators = {
        'summary_as_evergreen': [
            '文章认为', '作者提出', '本文总结',
            '文章介绍了', '作者认为'
        ],
        'non_existent_cards': [
            '卡片不存在', '空页面', '创建新笔记'
        ],
        'vague_actions': [
            '深入学习', '了解更多', '研究一下',
            '继续关注', '后续跟进'
        ],
        'ignore_user_anchor': [
            '未覆盖打动点', '未呼应当下关联'
        ],
        'forced_connections': [
            '强行关联', '泛泛关联', '主题相关'
        ]
    }

    for family, indicators in failure_indicators.items():
        for indicator in indicators:
            if indicator in content:
                return family

    return 'unknown'

def save_sample(sample, output_dir):
    """保存样本"""

    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)

    # 生成样本文件名
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    result = sample['result']

    filename = f"clip_process_{result}_{timestamp}.json"

    # 如果是失败样本，保存到对应的失败家族目录
    if result == 'failure' and sample.get('failure_family'):
        family_dir = output_path / sample['failure_family']
        family_dir.mkdir(parents=True, exist_ok=True)
        sample_file = family_dir / filename
    else:
        sample_file = output_path / filename

    save_json(sample_file, sample)
    print(f"样本已保存: {sample_file}")

    return sample_file

def generate_sample_report(output_dir):
    """生成样本统计报告"""

    output_path = Path(output_dir)

    stats = {
        'total': 0,
        'success': 0,
        'failure': 0,
        'by_family': {},
        'recent_samples': []
    }

    # 遍历所有样本文件
    for sample_file in output_path.rglob('*.json'):
        try:
            sample = load_json(sample_file)
            stats['total'] += 1

            if sample['result'] == 'success':
                stats['success'] += 1
            else:
                stats['failure'] += 1

            if sample.get('failure_family'):
                family = sample['failure_family']
                stats['by_family'][family] = stats['by_family'].get(family, 0) + 1

            stats['recent_samples'].append({
                'file': str(sample_file),
                'timestamp': sample['timestamp'],
                'result': sample['result'],
                'family': sample.get('failure_family', '')
            })
        except:
            continue

    # 按时间排序，取最近 10 个
    stats['recent_samples'].sort(key=lambda x: x['timestamp'], reverse=True)
    stats['recent_samples'] = stats['recent_samples'][:10]

    return stats

def main():
    """主函数"""

    import argparse
    parser = argparse.ArgumentParser(description='Clip-Process 样本收集')
    parser.add_argument('--file', type=str, required=True, help='剪藏文件路径')
    parser.add_argument('--result', type=str, required=True, choices=['success', 'failure'],
                       help='处理结果')
    parser.add_argument('--family', type=str, help='失败家族（可选，自动识别）')
    parser.add_argument('--details', type=str, help='详细信息（JSON 格式）')
    parser.add_argument('--output', type=str, default='samples', help='输出目录')
    parser.add_argument('--report', action='store_true', help='生成统计报告')
    args = parser.parse_args()

    # 生成报告
    if args.report:
        stats = generate_sample_report(args.output)

        print("\n" + "="*60)
        print("Clip-Process 样本统计报告")
        print("="*60)
        print(f"总样本数: {stats['total']}")
        print(f"成功: {stats['success']}")
        print(f"失败: {stats['failure']}")

        if stats['by_family']:
            print(f"\n失败家族:")
            for family, count in stats['by_family'].items():
                print(f"  {family}: {count}")

        if stats['recent_samples']:
            print(f"\n最近样本:")
            for sample in stats['recent_samples']:
                print(f"  {sample['timestamp']}: {sample['result']} ({sample['family']})")

        print("\n" + "="*60)
        return

    # 收集样本
    details = {}
    if args.details:
        try:
            details = json.loads(args.details)
        except:
            details = {'raw': args.details}

    # 自动识别失败家族
    family = args.family
    if args.result == 'failure' and not family:
        try:
            content = Path(args.file).read_text()
            family = identify_failure_family(content)
        except:
            family = 'unknown'

    sample = collect_sample(args.file, args.result, family, details)

    # 保存样本
    save_sample(sample, args.output)

if __name__ == '__main__':
    main()
