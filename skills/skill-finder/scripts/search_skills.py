#!/usr/bin/env python3
"""
Search local skills directory for skills matching a query.
Usage: python3 search_skills.py "<query>"
"""

import os
import re
import sys
from pathlib import Path

SKILLS_DIR = Path.home() / ".claude" / "skills"

def parse_frontmatter(file_path):
    """Parse YAML frontmatter from a markdown file."""
    with open(file_path, "r", encoding="utf-8") as f:
        content = f.read()

    match = re.match(r"^---\n(.*?)\n---\n", content, re.DOTALL)
    if not match:
        return None

    # Simple YAML parser for name and description
    frontmatter = {}
    for line in match.group(1).split("\n"):
        if ":" in line:
            key, value = line.split(":", 1)
            frontmatter[key.strip()] = value.strip()

    return frontmatter

def search_skills(query: str):
    """Search for skills matching the query."""
    query = query.lower()
    results = []

    for skill_dir in SKILLS_DIR.iterdir():
        if not skill_dir.is_dir():
            continue

        skill_md = skill_dir / "SKILL.md"
        if not skill_md.exists():
            continue

        frontmatter = parse_frontmatter(skill_md)
        if not frontmatter:
            continue

        name = frontmatter.get("name", "")
        description = frontmatter.get("description", "")

        # Calculate relevance score
        score = 0
        if query in name.lower():
            score += 10
        if query in description.lower():
            score += 5

        # Word overlap scoring
        query_words = set(query.split())
        name_words = set(name.lower().split())
        desc_words = set(description.lower().split())

        score += len(query_words & name_words) * 3
        score += len(query_words & desc_words)

        if score > 0:
            results.append({
                "name": name,
                "description": description[:100] + "..." if len(description) > 100 else description,
                "path": skill_dir,
                "score": score
            })

    return sorted(results, key=lambda x: x["score"], reverse=True)

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python3 search_skills.py '<query>'")
        sys.exit(1)

    query = " ".join(sys.argv[1:])
    results = search_skills(query)

    if not results:
        print(f"No skills found matching '{query}'")
        print("\nAll available skills:")
        for skill_dir in sorted(SKILLS_DIR.iterdir()):
            if skill_dir.is_dir():
                skill_md = skill_dir / "SKILL.md"
                if skill_md.exists():
                    fm = parse_frontmatter(skill_md)
                    if fm:
                        print(f"  - {fm.get('name', skill_dir.name)}")
    else:
        print(f"Found {len(results)} skill(s) matching '{query}':\n")
        for i, r in enumerate(results, 1):
            print(f"{i}. {r['name']}")
            print(f"   {r['description']}")
            print(f"   Path: {r['path']}")
            print()
