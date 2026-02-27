#!/usr/bin/env python3
"""
Search GitHub for high-star repositories matching a query.
Requires: gh (GitHub CLI) installed and authenticated.
Usage: python3 search_github.py "<query>" [language]
"""

import json
import subprocess
import sys
from typing import List, Dict

def search_github(query: str, language: str = None, limit: int = 10) -> List[Dict]:
    """Search GitHub for repositories."""
    cmd = ["gh", "search", "repos", query, "--limit", str(limit),
           "--json", "name,description,url,stargazerCount,language,repositoryTopics"]

    if language:
        cmd.append(f"language:{language}")

    try:
        result = subprocess.run(cmd, capture_output=True, text=True, check=True)
        repos = json.loads(result.stdout)

        # Sort by star count
        repos.sort(key=lambda x: x.get("stargazerCount", 0), reverse=True)
        return repos
    except subprocess.CalledProcessError as e:
        print(f"Error searching GitHub: {e.stderr}")
        return []
    except json.JSONDecodeError:
        print("Error parsing GitHub response")
        return []

def format_results(repos: List[Dict]) -> str:
    """Format repository results for display."""
    if not repos:
        return "No repositories found."

    output = []
    for i, repo in enumerate(repos, 1):
        stars = repo.get("stargazerCount", 0)
        name = repo.get("name", "unknown")
        url = repo.get("url", "")
        description = repo.get("description", "No description")
        language = repo.get("language", "Unknown")
        topics = repo.get("repositoryTopics", [])
        topic_names = [t.get("topic", {}).get("name", "") for t in topics]

        output.append(f"{i}. **{name}** ({language}) - {stars} stars")
        output.append(f"   {description}")
        output.append(f"   URL: {url}")
        if topic_names:
            output.append(f"   Topics: {', '.join(topic_names)}")
        output.append("")

    return "\n".join(output)

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python3 search_github.py '<query>' [language]")
        print("Example: python3 search_github.py 'pdf parser' python")
        sys.exit(1)

    query = sys.argv[1]
    language = sys.argv[2] if len(sys.argv) > 2 else None

    print(f"Searching GitHub for: {query}" + (f" (language: {language})" if language else ""))
    print()

    repos = search_github(query, language)
    print(format_results(repos))
