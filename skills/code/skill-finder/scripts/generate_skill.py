#!/usr/bin/env python3
"""
Generate a new skill from a GitHub repository.
Analyzes a GitHub repo and creates a skill with auto-generated content.

Usage:
    generate_skill.py <repo-url> [--skill-name <name>] [--skills-dir <path>]

Examples:
    generate_skill.py https://github.com/user/repo
    generate_skill.py https://github.com/user/repo --skill-name my-custom-name
"""

import json
import os
import re
import subprocess
import sys
import tempfile
from pathlib import Path
from urllib.parse import urlparse

# Import the init_skill function from skill-creator
SKILL_CREATOR_INIT = Path.home() / ".claude" / "skills" / "skill-creator" / "scripts" / "init_skill.py"
sys.path.insert(0, str(SKILL_CREATOR_INIT.parent))

try:
    from init_skill import title_case_skill_name
except ImportError:
    def title_case_skill_name(skill_name):
        return ' '.join(word.capitalize() for word in skill_name.split('-'))


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


def analyze_repo(repo_dir: Path) -> dict:
    """Analyze repository structure and content."""
    info = {
        "readme": "",
        "package_file": None,
        "package_content": None,
        "main_language": None,
        "dependencies": [],
        "scripts": {},
        "examples": [],
        "topics": [],
    }

    # Find README
    for readme_name in ["README.md", "README.rst", "README.txt"]:
        readme = repo_dir / readme_name
        if readme.exists():
            info["readme"] = readme.read_text(encoding="utf-8", errors="ignore")
            break

    # Find package/config file and detect language
    package_files = {
        "package.json": ("javascript", "npm"),
        "pyproject.toml": ("python", "python"),
        "setup.py": ("python", "python"),
        "requirements.txt": ("python", "pip"),
        "Cargo.toml": ("rust", "cargo"),
        "go.mod": ("go", "go"),
        "pom.xml": ("java", "maven"),
        "build.gradle": ("java", "gradle"),
        "composer.json": ("php", "composer"),
        "Gemfile": ("ruby", "bundler"),
    }

    for pkg_file, (lang, _) in package_files.items():
        pkg = repo_dir / pkg_file
        if pkg.exists():
            info["package_file"] = pkg_file
            info["package_content"] = pkg.read_text(encoding="utf-8", errors="ignore")
            info["main_language"] = lang
            break

    # Parse package file for dependencies
    if info["package_content"]:
        info.update(parse_package_file(info["package_content"], info["package_file"]))

    # Find examples
    for examples_dir in ["examples", "example", "docs", "demos"]:
        if (repo_dir / examples_dir).is_dir():
            for f in (repo_dir / examples_dir).glob("*"):
                if f.is_file() and not f.name.startswith("."):
                    info["examples"].append(f"{examples_dir}/{f.name}")

    return info


def parse_package_file(content: str, filename: str) -> dict:
    """Parse package file for dependencies and metadata."""
    result = {"dependencies": [], "scripts": {}}

    if filename == "package.json":
        try:
            data = json.loads(content)
            deps = data.get("dependencies", {})
            dev_deps = data.get("devDependencies", {})
            result["dependencies"] = list(deps.keys())[:10] + list(dev_deps.keys())[:5]
            result["scripts"] = data.get("scripts", {})
        except json.JSONDecodeError:
            pass

    elif filename in ["pyproject.toml", "setup.py", "requirements.txt"]:
        # Simple Python dependency extraction
        for line in content.split("\n"):
            line = line.strip()
            if line and not line.startswith("#") and "=" in line.lower():
                # Extract package name (before >=, <=, ==, etc.)
                pkg = re.split(r'[>=<~=]', line)[0].strip()
                if pkg and pkg.lower() not in ["python", "python-version"]:
                    result["dependencies"].append(pkg)

    elif filename == "Cargo.toml":
        for line in content.split("\n"):
            if line.strip().startswith("=") and '"' in line:
                pkg = line.split('=')[0].strip()
                result["dependencies"].append(pkg)

    return result


def extract_readme_section(readme: str, headings: list) -> str:
    """Extract a section from README by heading."""
    lines = readme.split("\n")
    start = -1
    end = len(lines)

    for i, line in enumerate(lines):
        for heading in headings:
            if line.strip().lower().startswith(("# " + heading.lower(), "## " + heading.lower(), heading.lower() + ":")):
                start = i
                break
        if start >= 0:
            break

    if start < 0:
        return ""

    start_level = lines[start].count("#") if lines[start].startswith("#") else 0
    for i in range(start + 1, len(lines)):
        if lines[i].startswith("#"):
            level = lines[i].count("#")
            if level <= start_level:
                end = i
                break

    section = "\n".join(lines[start:end])
    lines = section.split("\n")
    if lines[0].startswith("#"):
        lines = lines[1:]
    return "\n".join(lines).strip()


def generate_skill_description(repo_name: str, repo_info: dict) -> tuple:
    """Generate skill name and description from repo analysis."""
    readme = repo_info.get("readme", "")

    # Extract first paragraph from README as base description
    description = ""
    for line in readme.split("\n"):
        line = line.strip()
        if line and not line.startswith("#") and not line.startswith("!"):
            description = line
            break

    # Get features/benefits from README
    features_section = extract_readme_section(readme, ["Features", "Why", "What", "Highlights", "Key"])

    # Create comprehensive description
    if features_section:
        features_preview = features_section[:300] + "..." if len(features_section) > 300 else features_section
        full_description = f"{description}\n\nKey features:\n{features_preview}"
    else:
        full_description = description

    # Generate skill name from repo name
    skill_name = repo_name.lower().replace("_", "-").replace(".", "-")
    # Remove common suffixes
    for suffix in ["-js", ".js", "-ts", ".ts", "-py", ".py", "-go", ".go"]:
        skill_name = skill_name.replace(suffix, "")

    return skill_name, full_description


def generate_skill_content(repo_url: str, repo_name: str, repo_info: dict) -> str:
    """Generate the SKILL.md content from repository analysis."""
    readme = repo_info.get("readme", "")
    skill_name = repo_name.lower().replace("_", "-")
    skill_title = title_case_skill_name(skill_name)

    # Extract key sections
    overview = extract_readme_section(readme, ["About", "Description", "What is", "Overview"])
    installation = extract_readme_section(readme, ["Install", "Installation", "Setup", "Getting Started", "Quick Start"])
    usage = extract_readme_section(readme, ["Usage", "How to use", "Example", "Examples"])
    api = extract_readme_section(readme, ["API", "Documentation", "Reference"])

    # Get dependencies list
    deps = repo_info.get("dependencies", [])[:5]

    # Build description
    _, description = generate_skill_description(repo_name, repo_info)

    # Create SKILL.md content
    content = f"""---
name: {skill_name}
description: {description[:200]}{'...' if len(description) > 200 else ''}. Use when working with {repo_name} or when tasks involve {repo_info.get('main_language', 'this tool')} capabilities related to {skill_name.replace('-', ' ')}.
---

# {skill_title}

Integration with [{repo_name}]({repo_url}) for {skill_name.replace('-', ' ')} capabilities.

## Overview

This skill provides integration with **{repo_name}**, a {repo_info.get('main_language', 'software')} tool."""

    if overview:
        content += f"\n\n{overview[:500]}"
    else:
        content += f"\n\nUse this skill when working with {repo_name} or performing similar tasks."

    content += f"""

## Quick Start

### Installation

"""

    if installation:
        content += f"{installation[:600]}\n"
    else:
        content += f"```bash\n# Add installation instructions here based on {repo_info.get('package_file', 'the project')}\n```\n"

    if usage:
        content += f"\n### Usage Examples\n\n{usage[:800]}\n"

    if api:
        content += f"\n## API Reference\n\n{api[:500]}\n"

    if deps:
        content += f"\n## Key Dependencies\n\n"
        for dep in deps:
            content += f"- {dep}\n"

    content += """
## Resources

### scripts/
Helper scripts for working with this tool.

### references/
Documentation and reference materials.

---

**Source:** Generated from GitHub repository """ + repo_url + """
"""

    return content


def generate_skill_from_repo(repo_url: str, skill_name: str = None, skills_dir: str = None) -> Path:
    """Main function to generate a skill from a GitHub repository."""
    if skills_dir is None:
        skills_dir = Path.home() / ".claude" / "skills"

    skills_dir = Path(skills_dir)

    # Extract repo name from URL
    path = urlparse(repo_url).path.strip("/")
    parts = path.split("/")
    if len(parts) < 2:
        print(f"Invalid repository URL: {repo_url}")
        return None

    repo_name = parts[-1]
    repo_full_name = "/".join(parts[-2:])

    print(f"🔍 Analyzing repository: {repo_full_name}")

    with tempfile.TemporaryDirectory() as tmpdir:
        dest = Path(tmpdir) / repo_name

        # Clone repository
        print(f"📥 Cloning repository...")
        if not clone_repo(repo_url, str(dest)):
            return None

        # Analyze repository
        print(f"🔬 Analyzing repository structure...")
        repo_info = analyze_repo(dest)

        # Generate skill name if not provided
        if skill_name is None:
            skill_name, _ = generate_skill_description(repo_name, repo_info)

        # Check if skill already exists
        skill_dir = skills_dir / skill_name
        if skill_dir.exists():
            print(f"❌ Skill already exists: {skill_dir}")
            return None

        # Create skill directory
        print(f"📁 Creating skill directory: {skill_dir}")
        skill_dir.mkdir(parents=True, exist_ok=True)

        # Generate and write SKILL.md
        print(f"📝 Generating SKILL.md...")
        skill_content = generate_skill_content(repo_url, repo_name, repo_info)
        (skill_dir / "SKILL.md").write_text(skill_content)

        # Create subdirectories
        scripts_dir = skill_dir / "scripts"
        scripts_dir.mkdir(exist_ok=True)

        references_dir = skill_dir / "references"
        references_dir.mkdir(exist_ok=True)

        # Create a helper script
        helper_script = scripts_dir / "helper.py"
        helper_script.write_text(f"""#!/usr/bin/env python3
\"\"\"
Helper script for {skill_name}.

This script provides utility functions for working with {repo_name}.
\"\"\"

def main():
    print("Helper script for {skill_name}")
    # TODO: Add actual implementation

if __name__ == "__main__":
    main()
""")
        helper_script.chmod(0o755)

        # Save README as reference
        if repo_info.get("readme"):
            (references_dir / "original_readme.md").write_text(repo_info["readme"])

        print(f"\n✅ Skill '{skill_name}' created successfully!")
        print(f"   Location: {skill_dir}")
        print(f"\nNext steps:")
        print(f"   1. Review and edit SKILL.md")
        print(f"   2. Customize scripts/helper.py for your needs")
        print(f"   3. Test the skill with: /{skill_name}")

        return skill_dir


def main():
    if len(sys.argv) < 2:
        print("Usage: generate_skill.py <repo-url> [--skill-name <name>] [--skills-dir <path>]")
        print("\nExamples:")
        print("  generate_skill.py https://github.com/user/repo")
        print("  generate_skill.py https://github.com/user/repo --skill-name my-custom-name")
        sys.exit(1)

    repo_url = sys.argv[1]
    skill_name = None
    skills_dir = None

    # Parse optional arguments
    i = 2
    while i < len(sys.argv):
        if sys.argv[i] == "--skill-name" and i + 1 < len(sys.argv):
            skill_name = sys.argv[i + 1]
            i += 2
        elif sys.argv[i] == "--skills-dir" and i + 1 < len(sys.argv):
            skills_dir = sys.argv[i + 1]
            i += 2
        else:
            i += 1

    result = generate_skill_from_repo(repo_url, skill_name, skills_dir)

    if result:
        sys.exit(0)
    else:
        sys.exit(1)


if __name__ == "__main__":
    main()
