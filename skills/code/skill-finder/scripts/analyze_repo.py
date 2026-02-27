#!/usr/bin/env python3
"""
Analyze a GitHub repository to extract key information for skill generation.
Usage: python3 analyze_repo.py <repo-url> [output-dir]
"""

import os
import subprocess
import sys
import tempfile
from pathlib import Path
from urllib.parse import urlparse
import json

def clone_repo(repo_url: str, dest: str) -> bool:
    """Shallow clone a repository."""
    try:
        subprocess.run(
            ["git", "clone", "--depth", "1", "--quiet", repo_url, dest],
            check=True,
            capture_output=True
        )
        return True
    except subprocess.CalledProcessError as e:
        print(f"Error cloning repo: {e.stderr.decode()}")
        return False

def analyze_structure(repo_dir: Path) -> dict:
    """Analyze repository structure."""
    info = {
        "readme": "",
        "package_file": None,
        "main_files": [],
        "examples": [],
        "docs": [],
    }

    # Find README
    for readme_name in ["README.md", "README.rst", "README.txt"]:
        readme = repo_dir / readme_name
        if readme.exists():
            info["readme"] = readme.read_text(encoding="utf-8", errors="ignore")
            break

    # Find package/config file
    for pkg_file in ["package.json", "pyproject.toml", "Cargo.toml", "go.mod", "pom.xml", "build.gradle"]:
        pkg = repo_dir / pkg_file
        if pkg.exists():
            info["package_file"] = pkg.name
            info["package_content"] = pkg.read_text(encoding="utf-8", errors="ignore")
            break

    # Find source directories
    src_dirs = []
    for d in ["src", "lib", "app", "main"]:
        if (repo_dir / d).is_dir():
            src_dirs.append(d)

    # Find main entry files
    for ext in [".py", ".js", ".ts", ".go", ".rs"]:
        for f in repo_dir.glob(f"index{ext}"):
            info["main_files"].append(f.name)
        for f in repo_dir.glob(f"main{ext}"):
            info["main_files"].append(f.name)
        for f in repo_dir.glob(f"cli{ext}"):
            info["main_files"].append(f.name)

    # Find examples
    for examples_dir in ["examples", "example", "docs", "examples"]:
        if (repo_dir / examples_dir).is_dir():
            for f in (repo_dir / examples_dir).glob("*"):
                if f.is_file() and not f.name.startswith("."):
                    info["examples"].append(f"{examples_dir}/{f.name}")

    return info

def extract_key_info(info: dict) -> dict:
    """Extract key information for skill generation."""
    readme = info.get("readme", "")

    return {
        "description": extract_section(readme, ["About", "Description", "What is", "Overview"]),
        "installation": extract_section(readme, ["Install", "Installation", "Setup", "Getting Started"]),
        "usage": extract_section(readme, ["Usage", "How to use", "Example", "Examples", "Quick start"]),
        "api": extract_section(readme, ["API", "Documentation", "Reference"]),
        "package_info": parse_package_file(info.get("package_content"), info.get("package_file")),
    }

def extract_section(readme: str, headings: list) -> str:
    """Extract a section from README by heading."""
    lines = readme.split("\n")
    start = -1
    end = len(lines)

    # Find section start
    for i, line in enumerate(lines):
        for heading in headings:
            if line.strip().lower().startswith(("# " + heading.lower(), "## " + heading.lower(), heading.lower() + ":")):
                start = i
                break
        if start >= 0:
            break

    if start < 0:
        return ""

    # Find section end (next heading at same or higher level)
    start_level = lines[start].count("#") if lines[start].startswith("#") else 0
    for i in range(start + 1, len(lines)):
        if lines[i].startswith("#"):
            level = lines[i].count("#")
            if level <= start_level:
                end = i
                break

    section = "\n".join(lines[start:end])
    # Remove leading heading
    lines = section.split("\n")
    if lines[0].startswith("#"):
        lines = lines[1:]
    return "\n".join(lines).strip()

def parse_package_file(content: str, filename: str) -> dict:
    """Parse package file for dependencies and metadata."""
    if not content or not filename:
        return {}

    if filename == "package.json":
        try:
            data = json.loads(content)
            return {
                "name": data.get("name"),
                "version": data.get("version"),
                "dependencies": list(data.get("dependencies", {}).keys())[:10],
                "scripts": data.get("scripts", {})
            }
        except json.JSONDecodeError:
            pass

    return {}

def generate_skill_suggestion(repo_url: str, info: dict, key_info: dict) -> dict:
    """Generate skill suggestion based on repository analysis."""
    from urllib.parse import urlparse

    repo_name = urlparse(repo_url).path.strip("/").split("/")[-1]
    package_info = key_info.get("package_info", {})

    return {
        "suggested_name": repo_name.lower().replace("-", "-").replace("_", "-"),
        "suggested_description": f"Integration with {repo_name} for {package_info.get('name', repo_name)}. Use when working with {repo_name} {package_info.get('description', 'capabilities')}.",
        "installation": key_info.get("installation", ""),
        "usage_examples": key_info.get("usage", ""),
    }

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python3 analyze_repo.py <repo-url> [output-dir]")
        sys.exit(1)

    repo_url = sys.argv[1]
    output_dir = sys.argv[2] if len(sys.argv) > 2 else None

    with tempfile.TemporaryDirectory() as tmpdir:
        repo_name = urlparse(repo_url).path.strip("/").replace("/", "_")
        dest = Path(tmpdir) / repo_name

        print(f"Cloning {repo_url}...")
        if not clone_repo(repo_url, str(dest)):
            sys.exit(1)

        print("Analyzing repository structure...")
        info = analyze_structure(dest)

        print("Extracting key information...")
        key_info = extract_key_info(info)

        print("\n" + "="*60)
        print("Repository Analysis")
        print("="*60)

        if info["readme"]:
            print("\n[README Preview - first 500 chars]")
            print(info["readme"][:500] + "...")

        if key_info["installation"]:
            print("\n[Installation]")
            print(key_info["installation"][:500])

        if key_info["usage"]:
            print("\n[Usage]")
            print(key_info["usage"][:500])

        suggestion = generate_skill_suggestion(repo_url, info, key_info)

        print("\n" + "="*60)
        print("Suggested Skill")
        print("="*60)
        print(f"Name: {suggestion['suggested_name']}")
        print(f"Description: {suggestion['suggested_description']}")
        print("\nNext steps:")
        print(f"1. Create skill: python3 ~/.claude/skills/skill-creator/scripts/init_skill.py {suggestion['suggested_name']} --path ~/.claude/skills/")
        print(f"2. Edit ~/.claude/skills/{suggestion['suggested_name']}/SKILL.md")
        print(f"3. Package: python3 ~/.claude/skills/skill-creator/scripts/package_skill.py ~/.claude/skills/{suggestion['suggested_name']}")
