#!/usr/bin/env python3
"""
Clip-and-Process 样本收集脚本

用法：
  python3 collect_samples.py --url "https://xxx" --result success/failure
  python3 collect_samples.py --file "剪藏/xxx.md" --result success/failure
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

def collect_url_sample(url, result, details=None):
    """收集 URL 样本"""

    sample = {
        'timestamp': datetime.now().isoformat(),
        'type': 'url',
        'input': url,
        'result': result,
        'details': details or {},
        'evaluated': False
    }

    return sample

def collect_file_sample(file_path, result, details=None):
    """收集文件样本"""

    sample = {
        'timestamp': datetime.now().isoformat(),
        'type': 'file',
        'input': file_path,
        'result': result,
        'details': details or {},
        'evaluated': False
    }

    return sample

def identify_failure_family(details):
    """识别失败家族"""

    failure_indicators = {
        'wrong_platform_routing': [
            'platform_mismatch',
            'wrong_strategy_loaded',
            'generic_fallback'
        ],
        'extraction_failure': [
            'layer1_failed',
            'layer2_failed',
            'layer3_failed',
            'paywall_detected',
            'empty_content'
        ],
        'translation_missed': [
            'english_not_detected',
            'translation_skipped',
            'translation_failed'
        ],
        'content_type_misclassification': [
            'video_as_article',
            'article_as_video',
            'image_text_misclassified'
        ]
    }

    for family, indicators in failure_indicators.items():
        for indicator in indicators:
            if indicator in str(details):
                return family

    return 'unknown'

def save_sample(sample, output_dir):
    """保存样本"""

    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)

    # 生成样本文件名
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    sample_type = sample['type']
    result = sample['result']

    filename = f"{sample_type}_{result}_{timestamp}.json"
    sample_file = output_path / filename

    # 如果是失败样本，识别失败家族
    if result == 'failure':
        family = identify_failure_family(sample.get('details', {}))
        sample['failure_family'] = family

        # 保存到对应的失败家族目录
        family_dir = output_path / family
        family_dir.mkdir(parents=True, exist_ok=True)
        sample_file = family_dir / filename

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
        'by_type': {'url': 0, 'file': 0},
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

            stats['by_type'][sample['type']] += 1

            if 'failure_family' in sample:
                family = sample['failure_family']
                stats['by_family'][family] = stats['by_family'].get(family, 0) + 1

            stats['recent_samples'].append({
                'file': str(sample_file),
                'timestamp': sample['timestamp'],
                'result': sample['result']
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
    parser = argparse.ArgumentParser(description='Clip-and-Process 样本收集')
    parser.add_argument('--url', type=str, help='URL 样本')
    parser.add_argument('--file', type=str, help='文件样本')
    parser.add_argument('--result', type=str, required=True, choices=['success', 'failure'],
                       help='处理结果')
    parser.add_argument('--details', type=str, help='详细信息（JSON 格式）')
    parser.add_argument('--output', type=str, default='samples', help='输出目录')
    parser.add_argument('--report', action='store_true', help='生成统计报告')
    args = parser.parse_args()

    # 生成报告
    if args.report:
        stats = generate_sample_report(args.output)

        print("\n" + "="*60)
        print("样本统计报告")
        print("="*60)
        print(f"总样本数: {stats['total']}")
        print(f"成功: {stats['success']}")
        print(f"失败: {stats['failure']}")
        print(f"\n按类型:")
        print(f"  URL: {stats['by_type']['url']}")
        print(f"  文件: {stats['by_type']['file']}")

        if stats['by_family']:
            print(f"\n失败家族:")
            for family, count in stats['by_family'].items():
                print(f"  {family}: {count}")

        if stats['recent_samples']:
            print(f"\n最近样本:")
            for sample in stats['recent_samples']:
                print(f"  {sample['timestamp']}: {sample['result']}")

        print("\n" + "="*60)
        return

    # 收集样本
    details = {}
    if args.details:
        try:
            details = json.loads(args.details)
        except:
            details = {'raw': args.details}

    if args.url:
        sample = collect_url_sample(args.url, args.result, details)
    elif args.file:
        sample = collect_file_sample(args.file, args.result, details)
    else:
        print("错误：必须指定 --url 或 --file")
        sys.exit(1)

    # 保存样本
    save_sample(sample, args.output)

if __name__ == '__main__':
    main()
