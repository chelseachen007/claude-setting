---
name: skill-finder
description: 从本地技能目录或 GitHub 高星仓库自动发现和生成技能。当以下情况使用：(1) 用户请求的任务可能受益于现有技能，(2) 用户想要基于热门 GitHub 项目创建新技能，(3) 本地没有相关技能需要 GitHub 搜索找到参考实现。
---

# Skill 查找器

Automatically discovers existing skills or generates new ones from GitHub repositories.

## When to Use This Skill

This skill activates when:
- A task might have an existing skill solution
- User needs to find reference implementations from GitHub
- Generating reusable skills from popular open-source projects

## Workflow

### Step 1: Search Local Skills

First, search for relevant skills in `~/.claude/skills/`:

```bash
# List all skill names and descriptions
grep -r "^name:\|^description:" ~/.claude/skills/*/SKILL.md | paste - - | column -t
```

### Step 2: Analyze Relevance

If potential matches are found, read their SKILL.md files to determine if they're relevant:

```bash
cat ~/.claude/skills/<skill-name>/SKILL.md
```

### Step 3: GitHub Search (if no local match)

If no relevant skill exists locally, search GitHub for high-star repositories:

```bash
# Search by topic/language with star count filter
gh search repos "<query> language:python" --limit 10 --json name,description,url,stargazerCount --jq 'sort_by(-.stargazerCount) | .[:10]'
```

Search strategies by task type:
- **CLI tools**: `"<task> cli tool" language:python`
- **Libraries**: `"<task> library" language:javascript`
- **Frameworks**: `"<task> framework"`
- **API clients**: `"<api> client sdk"`
- **Automation**: `"<task> automation"`

### Step 4: Analyze Repository

For selected repositories, gather key information:

```bash
# Clone the repository (shallow clone for speed)
git clone --depth 1 <repo-url> /tmp/repo-analysis

# Read README and key files
cat /tmp/repo-analysis/README.md
cat /tmp/repo-analysis/package.json  # or pyproject.toml, Cargo.toml, etc.
ls -la /tmp/repo-analysis/
```

Focus on:
- **README.md**: Overview, usage examples, API documentation
- **Configuration files**: Dependencies, entry points, scripts
- **Source code structure**: Main modules, key functions/classes
- **Examples**: Usage patterns from examples/ or demo code

### Step 5: Generate New Skill (Automated)

Use the automated script to create a skill directly from a GitHub repository:

```bash
# Generate skill from repo (auto-generates name and content)
python3 ~/.claude/skills/skill-finder/scripts/generate_skill.py <repo-url>

# Generate with custom name
python3 ~/.claude/skills/skill-finder/scripts/generate_skill.py <repo-url> --skill-name <custom-name>
```

The script will:
1. Clone and analyze the repository
2. Extract README, installation, and usage information
3. Generate a complete SKILL.md with proper frontmatter
4. Create scripts/ and references/ directories
5. Save the original README as a reference

**Example:**
```bash
python3 ~/.claude/skills/skill-finder/scripts/generate_skill.py https://github.com/psf/requests
```

### Step 6: Manual Skill Creation (Alternative)

If you need more control, use skill-creator:

```bash
# Use skill-creator to initialize
python3 ~/.claude/skills/skill-creator/scripts/init_skill.py <new-skill-name> --path ~/.claude/skills/
```

Then manually populate based on your analysis.

## Output Pattern

After completing the workflow, report:

```
## Skill Discovery Results

### Local Skills Found: <count>
- <skill-name>: <brief description>
- ...

### GitHub Repositories Analyzed: <count>
- <repo-name> (<stars> stars): <url>
  - Key features: ...
  - Used for: ...

### New Skill Created: <skill-name>
- Location: ~/.claude/skills/<skill-name>/
- Triggered by: <description of when to use>
- Key capabilities: ...
```

## Best Practices

1. **Search thoroughly**: Use multiple search terms and combinations
2. **Prefer quality**: Focus on repositories with >1000 stars and active maintenance
3. **Extract patterns**: Look for reusable patterns, not just specific implementations
4. **Keep skills focused**: One skill per domain/use case
5. **Validate**: Test the generated skill on sample tasks before packaging
