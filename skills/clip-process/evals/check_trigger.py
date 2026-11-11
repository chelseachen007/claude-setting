#!/usr/bin/env python3
"""
Clip-Process 触发评估脚本

用法：
  python3 check_trigger.py                    # 运行所有触发用例
  python3 check_trigger.py --threshold 0.35   # 指定阈值
  python3 check_trigger.py --report reports/  # 输出报告到目录
"""

import json
import sys
from pathlib import Path
from datetime import datetime

def load_json(file_path):
    """加载 JSON 文件"""
    with open(file_path, 'r', encoding='utf-8') as f:
        return json.load(f)

def calculate_trigger_score(text, semantic_config):
    """计算触发分数"""

    score = 0.0
    matched_concepts = []

    # 正向概念匹配
    for concept in semantic_config['positive_concepts']:
        for phrase in concept['phrases']['zh'] + concept['phrases']['en']:
            if phrase in text:
                score += concept['weight']
                matched_concepts.append({
                    'type': 'positive',
                    'name': concept['name'],
                    'phrase': phrase,
                    'weight': concept['weight']
                })
                break

    # 负向概念匹配
    for concept in semantic_config['negative_concepts']:
        for phrase in concept['phrases']['zh'] + concept['phrases']['en']:
            if phrase in text:
                if concept.get('exclusive', False):
                    return 0.0, [{
                        'type': 'negative_exclusive',
                        'name': concept['name'],
                        'phrase': phrase
                    }]
                else:
                    score -= concept['weight']
                    matched_concepts.append({
                        'type': 'negative',
                        'name': concept['name'],
                        'phrase': phrase,
                        'weight': concept['weight']
                    })
                break

    score = max(0.0, min(1.0, score))
    return score, matched_concepts

def run_trigger_evaluation(trigger_cases, semantic_config, threshold):
    """运行触发评估"""

    results = {
        'should_trigger': {'passed': 0, 'failed': 0, 'cases': []},
        'should_not_trigger': {'passed': 0, 'failed': 0, 'cases': []},
        'near_neighbor': {'passed': 0, 'failed': 0, 'cases': []}
    }

    # 测试 should_trigger
    for case in trigger_cases['should_trigger']:
        score, concepts = calculate_trigger_score(case['text'], semantic_config)
        passed = score >= threshold

        results['should_trigger']['cases'].append({
            'text': case['text'],
            'family': case.get('family', 'unknown'),
            'score': score,
            'passed': passed,
            'concepts': concepts
        })

        if passed:
            results['should_trigger']['passed'] += 1
        else:
            results['should_trigger']['failed'] += 1

    # 测试 should_not_trigger
    for case in trigger_cases['should_not_trigger']:
        score, concepts = calculate_trigger_score(case['text'], semantic_config)
        passed = score < threshold

        results['should_not_trigger']['cases'].append({
            'text': case['text'],
            'family': case.get('family', 'unknown'),
            'score': score,
            'passed': passed,
            'concepts': concepts
        })

        if passed:
            results['should_not_trigger']['passed'] += 1
        else:
            results['should_not_trigger']['failed'] += 1

    # 测试 near_neighbor
    for case in trigger_cases['near_neighbor']:
        score, concepts = calculate_trigger_score(case['text'], semantic_config)
        expected_trigger = case.get('expected_trigger', False)
        passed = (score >= threshold) == expected_trigger

        results['near_neighbor']['cases'].append({
            'text': case['text'],
            'family': case.get('family', 'unknown'),
            'score': score,
            'expected_trigger': expected_trigger,
            'passed': passed,
            'concepts': concepts,
            'risk': case.get('risk', '')
        })

        if passed:
            results['near_neighbor']['passed'] += 1
        else:
            results['near_neighbor']['failed'] += 1

    return results

def generate_report(results, threshold, output_dir=None):
    """生成评估报告"""

    total_passed = (
        results['should_trigger']['passed'] +
        results['should_not_trigger']['passed'] +
        results['near_neighbor']['passed']
    )
    total_cases = (
        results['should_trigger']['passed'] + results['should_trigger']['failed'] +
        results['should_not_trigger']['passed'] + results['should_not_trigger']['failed'] +
        results['near_neighbor']['passed'] + results['near_neighbor']['failed']
    )
    overall_score = total_passed / total_cases if total_cases > 0 else 0.0

    report = {
        'timestamp': datetime.now().isoformat(),
        'threshold': threshold,
        'overall_score': overall_score,
        'summary': {
            'should_trigger': f"{results['should_trigger']['passed']}/{results['should_trigger']['passed'] + results['should_trigger']['failed']}",
            'should_not_trigger': f"{results['should_not_trigger']['passed']}/{results['should_not_trigger']['passed'] + results['should_not_trigger']['failed']}",
            'near_neighbor': f"{results['near_neighbor']['passed']}/{results['near_neighbor']['passed'] + results['near_neighbor']['failed']}"
        },
        'details': results
    }

    print("\n" + "="*60)
    print("Clip-Process 触发评估报告")
    print("="*60)
    print(f"时间: {report['timestamp']}")
    print(f"阈值: {threshold}")
    print(f"总体得分: {overall_score:.2%}")
    print("\n分项得分:")
    print(f"  should_trigger:     {report['summary']['should_trigger']}")
    print(f"  should_not_trigger: {report['summary']['should_not_trigger']}")
    print(f"  near_neighbor:      {report['summary']['near_neighbor']}")

    failed_cases = []
    for category in ['should_trigger', 'should_not_trigger', 'near_neighbor']:
        for case in results[category]['cases']:
            if not case['passed']:
                failed_cases.append({
                    'category': category,
                    'text': case['text'],
                    'score': case['score'],
                    'family': case.get('family', 'unknown')
                })

    if failed_cases:
        print(f"\n失败用例 ({len(failed_cases)} 个):")
        for i, case in enumerate(failed_cases, 1):
            print(f"  {i}. [{case['category']}] {case['text']}")
            print(f"     分数: {case['score']:.2f}, 家族: {case['family']}")

    if output_dir:
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)
        report_file = output_path / f"trigger_eval_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(report_file, 'w', encoding='utf-8') as f:
            json.dump(report, f, ensure_ascii=False, indent=2)
        print(f"\n报告已保存: {report_file}")

    print("\n" + "="*60)
    return report

def main():
    """主函数"""

    import argparse
    parser = argparse.ArgumentParser(description='Clip-Process 触发评估')
    parser.add_argument('--threshold', type=float, default=0.35, help='触发阈值')
    parser.add_argument('--report', type=str, help='报告输出目录')
    args = parser.parse_args()

    eval_dir = Path(__file__).parent
    trigger_cases = load_json(eval_dir / 'trigger_cases.json')
    semantic_config = load_json(eval_dir / 'semantic_config.json')

    results = run_trigger_evaluation(trigger_cases, semantic_config, args.threshold)
    report = generate_report(results, args.threshold, args.report)

    if report['overall_score'] >= 0.95:
        print("\n✅ 触发评估通过")
        sys.exit(0)
    else:
        print(f"\n❌ 触发评估未通过 (得分: {report['overall_score']:.2%})")
        sys.exit(1)

if __name__ == '__main__':
    main()
