#!/usr/bin/env python3
"""
Clip-and-Process 路由准确性评估脚本

用法：
  python3 check_routing.py                    # 运行所有路由用例
  python3 check_routing.py --platform xiaohongshu  # 只测试小红书
  python3 check_routing.py --report reports/  # 输出报告到目录
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

def identify_platform(url):
    """识别平台（模拟路由逻辑）"""

    # 平台识别规则
    platform_rules = {
        'xiaohongshu': [
            r'xiaohongshu\.com/(explore|discovery|user/profile|note)',
            r'xhslink\.com'
        ],
        'bilibili': [
            r'bilibili\.com/(video|read)',
            r'b23\.tv'
        ],
        'douyin': [
            r'douyin\.com/(video|note)',
            r'v\.douyin\.com'
        ],
        'youtube': [
            r'youtube\.com/watch',
            r'youtu\.be'
        ],
        'twitter': [
            r'twitter\.com/.+/status',
            r'x\.com/.+/status'
        ],
        'wechat': [
            r'mp\.weixin\.qq\.com'
        ],
        'feishu': [
            r'feishu\.cn/(docx|wiki|base)',
            r'my\.feishu\.cn'
        ],
        'generic': []  # 默认
    }

    for platform, patterns in platform_rules.items():
        for pattern in patterns:
            if re.search(pattern, url):
                return platform

    return 'generic'

def identify_content_type(url, platform):
    """识别内容类型"""

    # 内容类型识别规则
    content_type_rules = {
        'xiaohongshu': {
            r'/explore/': 'image-text',
            r'/discovery/': 'image-text',
            r'/note/': 'image-text',
            r'/user/profile': 'profile'
        },
        'bilibili': {
            r'/video/': 'video',
            r'/read/': 'article'
        },
        'douyin': {
            r'/video/': 'video',
            r'/note/': 'image-text'
        },
        'youtube': {
            r'/watch': 'video'
        },
        'twitter': {
            r'/status/': 'tweet'
        },
        'wechat': {
            r'': 'article'
        },
        'feishu': {
            r'/docx/': 'document',
            r'/wiki/': 'wiki',
            r'/base/': 'bitable'
        },
        'generic': {
            r'': 'article'
        }
    }

    if platform in content_type_rules:
        for pattern, content_type in content_type_rules[platform].items():
            if re.search(pattern, url):
                return content_type

    return 'article'

def get_expected_strategy(platform, content_type):
    """获取期望的策略文件"""

    strategy_map = {
        'xiaohongshu': 'strategies/platform-xhs.md',
        'bilibili': 'strategies/platform-bilibili.md',
        'douyin': 'strategies/platform-douyin.md',
        'youtube': 'strategies/platform-youtube.md',
        'twitter': 'strategies/platform-twitter.md',
        'wechat': 'strategies/platform-wechat.md',
        'feishu': None,  # 使用 lark-mcp
        'generic': 'strategies/layer1-direct-fetch.md'
    }

    return strategy_map.get(platform, 'strategies/layer1-direct-fetch.md')

def run_routing_evaluation(routing_cases):
    """运行路由准确性评估"""

    results = {
        'platform_recognition': {'passed': 0, 'failed': 0, 'cases': []},
        'content_type_detection': {'passed': 0, 'failed': 0, 'cases': []},
        'strategy_selection': {'passed': 0, 'failed': 0, 'cases': []}
    }

    # 测试每个平台
    for platform, cases in routing_cases['platforms'].items():
        for case in cases:
            url = case['url']
            expected_platform = case['expected_platform']
            expected_content_type = case['expected_content_type']
            expected_strategy = case.get('expected_strategy')

            # 识别平台
            detected_platform = identify_platform(url)
            platform_passed = detected_platform == expected_platform

            # 识别内容类型
            detected_content_type = identify_content_type(url, detected_platform)
            content_type_passed = detected_content_type == expected_content_type

            # 检查策略选择
            detected_strategy = get_expected_strategy(detected_platform, detected_content_type)
            strategy_passed = detected_strategy == expected_strategy if expected_strategy else True

            # 记录结果
            case_result = {
                'url': url,
                'platform': {
                    'expected': expected_platform,
                    'detected': detected_platform,
                    'passed': platform_passed
                },
                'content_type': {
                    'expected': expected_content_type,
                    'detected': detected_content_type,
                    'passed': content_type_passed
                },
                'strategy': {
                    'expected': expected_strategy,
                    'detected': detected_strategy,
                    'passed': strategy_passed
                },
                'notes': case.get('notes', '')
            }

            # 分类统计
            results['platform_recognition']['cases'].append(case_result)
            if platform_passed:
                results['platform_recognition']['passed'] += 1
            else:
                results['platform_recognition']['failed'] += 1

            results['content_type_detection']['cases'].append(case_result)
            if content_type_passed:
                results['content_type_detection']['passed'] += 1
            else:
                results['content_type_detection']['failed'] += 1

            results['strategy_selection']['cases'].append(case_result)
            if strategy_passed:
                results['strategy_selection']['passed'] += 1
            else:
                results['strategy_selection']['failed'] += 1

    return results

def generate_report(results, output_dir=None):
    """生成评估报告"""

    # 计算总体得分
    total_passed = (
        results['platform_recognition']['passed'] +
        results['content_type_detection']['passed'] +
        results['strategy_selection']['passed']
    )
    total_cases = (
        results['platform_recognition']['passed'] + results['platform_recognition']['failed'] +
        results['content_type_detection']['passed'] + results['content_type_detection']['failed'] +
        results['strategy_selection']['passed'] + results['strategy_selection']['failed']
    )
    overall_score = total_passed / total_cases if total_cases > 0 else 0.0

    report = {
        'timestamp': datetime.now().isoformat(),
        'overall_score': overall_score,
        'summary': {
            'platform_recognition': f"{results['platform_recognition']['passed']}/{results['platform_recognition']['passed'] + results['platform_recognition']['failed']}",
            'content_type_detection': f"{results['content_type_detection']['passed']}/{results['content_type_detection']['passed'] + results['content_type_detection']['failed']}",
            'strategy_selection': f"{results['strategy_selection']['passed']}/{results['strategy_selection']['passed'] + results['strategy_selection']['failed']}"
        },
        'details': results
    }

    # 输出到控制台
    print("\n" + "="*60)
    print("Clip-and-Process 路由准确性评估报告")
    print("="*60)
    print(f"时间: {report['timestamp']}")
    print(f"总体得分: {overall_score:.2%}")
    print("\n分项得分:")
    print(f"  平台识别:     {report['summary']['platform_recognition']}")
    print(f"  内容类型检测: {report['summary']['content_type_detection']}")
    print(f"  策略选择:     {report['summary']['strategy_selection']}")

    # 输出失败用例
    failed_cases = []
    for case in results['platform_recognition']['cases']:
        if not case['platform']['passed']:
            failed_cases.append({
                'type': 'platform',
                'url': case['url'],
                'expected': case['platform']['expected'],
                'detected': case['platform']['detected']
            })
        if not case['content_type']['passed']:
            failed_cases.append({
                'type': 'content_type',
                'url': case['url'],
                'expected': case['content_type']['expected'],
                'detected': case['content_type']['detected']
            })

    if failed_cases:
        print(f"\n失败用例 ({len(failed_cases)} 个):")
        for i, case in enumerate(failed_cases, 1):
            print(f"  {i}. [{case['type']}] {case['url']}")
            print(f"     期望: {case['expected']}, 检测: {case['detected']}")

    # 保存报告
    if output_dir:
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)

        report_file = output_path / f"routing_eval_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(report_file, 'w', encoding='utf-8') as f:
            json.dump(report, f, ensure_ascii=False, indent=2)

        print(f"\n报告已保存: {report_file}")

    print("\n" + "="*60)

    return report

def main():
    """主函数"""

    # 解析参数
    import argparse
    parser = argparse.ArgumentParser(description='Clip-and-Process 路由准确性评估')
    parser.add_argument('--platform', type=str, help='只测试指定平台')
    parser.add_argument('--report', type=str, help='报告输出目录')
    args = parser.parse_args()

    # 加载配置
    eval_dir = Path(__file__).parent
    routing_cases = load_json(eval_dir / 'routing_cases.json')

    # 过滤平台
    if args.platform:
        filtered_cases = {
            'platforms': {
                args.platform: routing_cases['platforms'].get(args.platform, [])
            }
        }
        routing_cases = filtered_cases

    # 运行评估
    results = run_routing_evaluation(routing_cases)

    # 生成报告
    report = generate_report(results, args.report)

    # 返回退出码
    if report['overall_score'] >= 0.95:  # 95% 通过率
        print("\n✅ 路由准确性评估通过")
        sys.exit(0)
    else:
        print(f"\n❌ 路由准确性评估未通过 (得分: {report['overall_score']:.2%})")
        sys.exit(1)

if __name__ == '__main__':
    main()
