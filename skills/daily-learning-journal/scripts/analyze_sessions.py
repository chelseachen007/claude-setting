#!/usr/bin/env python3
"""Claude Code 会话分析脚本"""

import argparse
import json
import os
import re
from collections import defaultdict
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any


def get_date_filter(date_arg: str) -> str:
    if date_arg == "today":
        return datetime.now().strftime("%Y-%m-%d")
    elif date_arg == "yesterday":
        return (datetime.now() - timedelta(days=1)).strftime("%Y-%m-%d")
    try:
        return datetime.strptime(date_arg, "%Y-%m-%d").strftime("%Y-%m-%d")
    except ValueError:
        return date_arg


def find_session_files(projects_dir: Path, target_date: str) -> list[Path]:
    session_files = []
    for jsonl_file in projects_dir.rglob("*.jsonl"):
        if "subagents" in str(jsonl_file):
            continue
        try:
            mtime = datetime.fromtimestamp(jsonl_file.stat().st_mtime)
            if mtime.strftime("%Y-%m-%d") == target_date:
                session_files.append(jsonl_file)
        except Exception:
            continue
    return session_files


def extract_user_messages(jsonl_path: Path) -> list[dict]:
    messages = []
    try:
        with open(jsonl_path, "r", encoding="utf-8") as f:
            for line in f:
                try:
                    data = json.loads(line.strip())
                    if data.get("type") == "user" and "message" in data:
                        msg = data["message"]
                        messages.append({
                            "content": msg.get("content", ""),
                            "timestamp": data.get("timestamp", ""),
                            "cwd": data.get("cwd", "")
                        })
                except json.JSONDecodeError:
                    continue
    except Exception:
        pass
    return messages


def extract_skills_used(messages: list[dict]) -> dict[str, int]:
    skills_count = defaultdict(int)
    skill_patterns = [
        r'<command-name>/([a-zA-Z0-9_-]+)</command-name>',
        r'<command-message>([a-zA-Z0-9_-]+)</command-message>',
    ]
    exclude = {'null', 'project', 'Mobile', 'upgrade', 'env', 'plugin', 'Everything',
               'Learn', 'Claude', 'prompt', 'API', 'http', 'true', 'false', 'async'}
    
    for msg in messages:
        content = str(msg.get("content", ""))
        for pattern in skill_patterns:
            for match in re.findall(pattern, content):
                if match and len(match) > 2 and match not in exclude:
                    skills_count[match] += 1
    return dict(sorted(skills_count.items(), key=lambda x: -x[1]))


def extract_projects(messages: list[dict]) -> dict[str, int]:
    projects = defaultdict(int)
    for msg in messages:
        cwd = msg.get("cwd", "")
        if cwd:
            name = Path(cwd).name
            if name and name not in ["", "/", "home"]:
                projects[name] += 1
    return dict(sorted(projects.items(), key=lambda x: -x[1]))


def extract_tech_topics(messages: list[dict]) -> list[str]:
    topics = set()
    keywords = ["React", "Vue", "TypeScript", "Python", "Go", "Docker", "Git",
                "Playwright", "Jest", "PostgreSQL", "Redis", "API", "HTTP",
                "CSS", "HTML", "Node.js", "Claude", "GPT", "LLM", "AI", "Agent",
                "Hook", "Skill", "MCP", "Plugin", "Test", "Debug", "Build"]
    for msg in messages:
        content = str(msg.get("content", "")).lower()
        for kw in keywords:
            if kw.lower() in content:
                topics.add(kw)
    return sorted(list(topics))


def count_messages(jsonl_path: Path) -> dict[str, int]:
    counts = {"total": 0, "user": 0, "assistant": 0}
    try:
        with open(jsonl_path, "r", encoding="utf-8") as f:
            for line in f:
                try:
                    data = json.loads(line.strip())
                    counts["total"] += 1
                    if data.get("type") == "user":
                        counts["user"] += 1
                    elif data.get("type") == "assistant":
                        counts["assistant"] += 1
                except json.JSONDecodeError:
                    continue
    except Exception:
        pass
    return counts


def analyze_sessions(target_date: str, projects_dir: Path) -> dict[str, Any]:
    session_files = find_session_files(projects_dir, target_date)
    all_messages = []
    all_counts = {"total": 0, "user": 0, "assistant": 0}
    
    for sf in session_files:
        all_messages.extend(extract_user_messages(sf))
        c = count_messages(sf)
        all_counts["total"] += c["total"]
        all_counts["user"] += c["user"]
        all_counts["assistant"] += c["assistant"]
    
    return {
        "date": target_date,
        "session_files": len(session_files),
        "message_counts": all_counts,
        "skills_used": extract_skills_used(all_messages),
        "projects": extract_projects(all_messages),
        "tech_topics": extract_tech_topics(all_messages),
    }


def generate_journal(analysis: dict[str, Any]) -> str:
    date = analysis["date"]
    lines = [
        "---", "tags:", f'title: "{date}"', f"date: {date}", f"lastmod: {date}",
        "---", "", "#日记", "", "## 事件记录", "", "### 今日学习", "",
        f"- **Claude Code 使用**: 今日共 {analysis['message_counts']['user']} 次交互",
    ]
    if analysis["tech_topics"]:
        lines.append(f"- **技术主题**: {', '.join(analysis['tech_topics'][:10])}")
    
    lines.extend(["", "### 使用的 Skills", ""])
    for skill, count in list(analysis["skills_used"].items())[:10]:
        lines.append(f"- `/{skill}`: {count} 次")
    
    lines.extend(["", "### 项目活动", ""])
    for proj, count in list(analysis["projects"].items())[:5]:
        lines.append(f"- **{proj}**: {count} 条消息")
    
    lines.extend([
        "", "### 未完成事项", "", "- [ ] ", "",
        "## 今日新闻", "", "## 那年今日", "",
        "```dataview", "List",
        'where file.name= dateformat(date(today)-dur(1 year), "yyyy-MM-dd")',
        'or file.name= dateformat(date(today)-dur(2 year), "yyyy-MM-dd")',
        'or file.name= dateformat(date(today)-dur(3 year), "yyyy-MM-dd")',
        "```", ""
    ])
    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(description="分析 Claude Code 会话记录")
    parser.add_argument("--date", default="today")
    parser.add_argument("--projects-dir", default=None)
    parser.add_argument("--obsidian-path", default=None)
    parser.add_argument("--format", choices=["json", "markdown"], default="markdown")
    parser.add_argument("--write-journal", action="store_true")
    args = parser.parse_args()

    target_date = get_date_filter(args.date)
    projects_dir = Path(args.projects_dir) if args.projects_dir else Path.home() / ".claude" / "projects"
    
    if not projects_dir.exists():
        print(f"Error: {projects_dir} not found")
        return 1

    analysis = analyze_sessions(target_date, projects_dir)

    if args.write_journal:
        obsidian = args.obsidian_path or os.environ.get("OBSIDIAN_VAULT_PATH")
        if not obsidian:
            for p in [Path.home() / "Documents" / "study" / "github" / "Obsidian",
                      Path.home() / "Obsidian"]:
                if p.exists() and (p / ".obsidian").exists():
                    obsidian = str(p)
                    break
        if not obsidian:
            print("Error: Obsidian path not found")
            return 1
        
        # 按照年/年-月/日.md 结构组织
        year = target_date[:4]
        month = target_date[5:7]
        journal_dir = Path(obsidian) / "行思录" / year / f"{year}-{month}"
        journal_dir.mkdir(parents=True, exist_ok=True)
        journal_file = journal_dir / f"{target_date}.md"
        
        with open(journal_file, "w", encoding="utf-8") as f:
            f.write(generate_journal(analysis))
        print(f"Journal written to: {journal_file}")
        return 0

    if args.format == "json":
        print(json.dumps(analysis, indent=2, ensure_ascii=False))
    else:
        print(f"# {target_date} 会话分析报告\n")
        print(f"- 会话文件数: {analysis['session_files']}")
        print(f"- 用户消息数: {analysis['message_counts']['user']}")
        print(f"- Skills: {list(analysis['skills_used'].keys())[:10]}")
        print(f"- 项目: {list(analysis['projects'].keys())[:5]}")
    return 0


if __name__ == "__main__":
    exit(main())
