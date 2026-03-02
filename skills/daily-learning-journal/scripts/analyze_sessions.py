#!/usr/bin/env python3
"""
分析Claude Code会话记录，提取今日学习内容
"""

import json
import os
import glob
from datetime import datetime, date
from collections import defaultdict
import argparse


def get_session_files(base_path: str) -> list:
    """获取所有会话jsonl文件"""
    projects_dir = os.path.expanduser(base_path)
    files = []

    for project_dir in os.listdir(projects_dir):
        project_path = os.path.join(projects_dir, project_dir)
        if os.path.isdir(project_path):
            jsonl_files = glob.glob(os.path.join(project_path, "*.jsonl"))
            files.extend(jsonl_files)

    return files


def parse_session_file(filepath: str, target_date: date) -> list:
    """解析单个会话文件，提取指定日期的消息"""
    messages = []

    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            for line in f:
                try:
                    data = json.loads(line.strip())
                    timestamp = data.get('timestamp', '')

                    if timestamp:
                        msg_date = datetime.fromisoformat(timestamp.replace('Z', '+00:00')).date()
                        if msg_date == target_date:
                            messages.append(data)
                except (json.JSONDecodeError, ValueError):
                    continue
    except Exception as e:
        print(f"Error reading {filepath}: {e}")

    return messages


def extract_user_messages(messages: list) -> list:
    """提取用户消息"""
    user_msgs = []

    for msg in messages:
        if msg.get('type') == 'user':
            content = msg.get('message', {}).get('content', '')
            if isinstance(content, str):
                user_msgs.append(content)
            elif isinstance(content, list):
                for item in content:
                    if isinstance(item, dict) and item.get('type') == 'text':
                        user_msgs.append(item.get('text', ''))

    return user_msgs


def extract_skills_used(messages: list) -> set:
    """提取使用的skills"""
    skills = set()

    for msg in messages:
        content = msg.get('message', {}).get('content', '')

        # 检查command-name标签
        if '<command-name>' in str(content):
            import re
            matches = re.findall(r'<command-name>([^<]+)</command-name>', str(content))
            skills.update(matches)

        # 检查skill加载提示
        if 'skill' in str(content).lower() and 'Base directory' in str(content):
            import re
            matches = re.findall(r'/([^/]+)\n#', str(content))
            skills.update(matches)

    return skills


def extract_assistant_messages(messages: list) -> list:
    """提取助手消息"""
    assistant_msgs = []

    for msg in messages:
        if msg.get('type') == 'assistant':
            content = msg.get('message', {}).get('content', [])
            if isinstance(content, list):
                for item in content:
                    if isinstance(item, dict):
                        if item.get('type') == 'text':
                            assistant_msgs.append(item.get('text', '')[:500])  # 截取前500字符
                        elif item.get('type') == 'thinking':
                            assistant_msgs.append(f"[思考] {item.get('thinking', '')[:300]}")

    return assistant_msgs


def extract_projects(messages: list) -> dict:
    """提取项目活动"""
    projects = defaultdict(list)

    for msg in messages:
        cwd = msg.get('cwd', '')
        if cwd:
            # 提取项目名
            parts = cwd.split('/')
            if parts:
                project_name = parts[-1] if parts[-1] else parts[-2] if len(parts) > 1 else 'unknown'
                projects[project_name].append(msg.get('type', 'unknown'))

    return dict(projects)


def identify_learning_topics(user_msgs: list, assistant_msgs: list) -> list:
    """识别学习主题"""
    topics = []
    combined_text = ' '.join(user_msgs + assistant_msgs).lower()

    # 技术关键词识别
    tech_keywords = {
        'vue': 'Vue.js',
        'react': 'React',
        'typescript': 'TypeScript',
        'javascript': 'JavaScript',
        'python': 'Python',
        'go': 'Go',
        'rust': 'Rust',
        'docker': 'Docker',
        'kubernetes': 'Kubernetes',
        'api': 'API设计',
        'database': '数据库',
        'sql': 'SQL',
        'git': 'Git',
        'testing': '测试',
        'security': '安全',
        'performance': '性能优化',
        'architecture': '架构设计',
        'refactor': '重构',
        'debug': '调试',
        'deployment': '部署',
        'ci/cd': 'CI/CD',
        'claude': 'Claude',
        'skill': 'Skills开发',
        'mcp': 'MCP协议',
        'obsidian': 'Obsidian',
        'nuxt': 'Nuxt.js',
        'tailwind': 'Tailwind CSS',
        'prisma': 'Prisma ORM',
        'sqlite': 'SQLite',
        'fastify': 'Fastify',
    }

    for keyword, topic in tech_keywords.items():
        if keyword in combined_text:
            topics.append(topic)

    return list(set(topics))


def identify_pending_tasks(user_msgs: list, assistant_msgs: list) -> list:
    """识别未完成任务"""
    tasks = []
    combined_text = '\n'.join(user_msgs + assistant_msgs)

    import re

    # 查找TODO模式
    todo_patterns = [
        r'TODO[:：]\s*(.+)',
        r'待办[:：]\s*(.+)',
        r'需要(.+)',
        r'接下来(.+)',
        r'然后(.+)',
        r'- \[ \] (.+)',
    ]

    for pattern in todo_patterns:
        matches = re.findall(pattern, combined_text)
        tasks.extend([m.strip() for m in matches if len(m.strip()) > 5])

    return list(set(tasks))[:5]  # 最多返回5个


def analyze_today(date_str: str = None) -> dict:
    """分析今天的会话"""
    if date_str and date_str.lower() == 'today':
        date_str = None
    target_date = datetime.strptime(date_str, '%Y-%m-%d').date() if date_str else date.today()

    session_files = get_session_files('~/.claude/projects/')
    all_messages = []

    for filepath in session_files:
        messages = parse_session_file(filepath, target_date)
        all_messages.extend(messages)

    user_msgs = extract_user_messages(all_messages)
    assistant_msgs = extract_assistant_messages(all_messages)
    skills = extract_skills_used(all_messages)
    projects = extract_projects(all_messages)
    topics = identify_learning_topics(user_msgs, assistant_msgs)
    pending = identify_pending_tasks(user_msgs, assistant_msgs)

    return {
        'date': target_date.isoformat(),
        'total_messages': len(all_messages),
        'user_messages_count': len(user_msgs),
        'skills_used': list(skills),
        'projects': projects,
        'learning_topics': topics,
        'pending_tasks': pending,
        'sample_user_messages': user_msgs[:10],
        'sample_assistant_messages': assistant_msgs[:5],
    }


def get_obsidian_path() -> str:
    """获取Obsidian库路径，优先从环境变量读取"""
    # 优先使用环境变量
    env_path = os.environ.get('OBSIDIAN_VAULT_PATH')
    if env_path:
        return os.path.expanduser(env_path)

    # 常见位置列表
    common_paths = [
        '~/Documents/study/github/Obsidian',
        '~/Obsidian',
        '~/Documents/Obsidian',
        '~/Library/Mobile Documents/iCloud~md~obsidian/Documents/',
    ]

    for path in common_paths:
        expanded = os.path.expanduser(path)
        if os.path.isdir(expanded) and os.path.isdir(os.path.join(expanded, '.obsidian')):
            return expanded

    # 默认返回第一个常见位置
    return os.path.expanduser('~/Documents/study/github/Obsidian')


def write_to_obsidian(journal_content: str, date_str: str = None) -> str:
    """写入Obsidian行思录"""
    target_date = date_str if date_str else date.today().isoformat()
    obsidian_path = get_obsidian_path()
    journal_dir = os.path.join(obsidian_path, '行思录')
    journal_file = os.path.join(journal_dir, f'{target_date}.md')

    os.makedirs(journal_dir, exist_ok=True)

    with open(journal_file, 'w', encoding='utf-8') as f:
        f.write(journal_content)

    return journal_file


def main():
    parser = argparse.ArgumentParser(description='分析Claude Code会话记录')
    parser.add_argument('--date', type=str, default=None, help='指定日期 (YYYY-MM-DD)，默认今天')
    parser.add_argument('--output', type=str, choices=['json', 'markdown'], default='json', help='输出格式')

    args = parser.parse_args()

    result = analyze_today(args.date)

    if args.output == 'json':
        print(json.dumps(result, ensure_ascii=False, indent=2))
    else:
        print(f"# {result['date']} 学习总结\n")
        print(f"## 统计\n- 总消息数: {result['total_messages']}\n")
        print(f"## 使用Skills\n- " + '\n- '.join(result['skills_used']) + '\n')
        print(f"## 学习主题\n- " + '\n- '.join(result['learning_topics']) + '\n')
        print(f"## 项目活动\n")
        for proj, activities in result['projects'].items():
            print(f"- **{proj}**: {len(activities)} 次操作")


if __name__ == '__main__':
    main()
