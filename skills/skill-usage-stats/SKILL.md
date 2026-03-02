# Skill 使用统计

统计 Claude Code 中 Skills 和 Agents 的使用情况，帮助清理未使用的 skill。

## 触发条件

当用户请求以下内容时使用此 skill：
- "统计 skill 使用情况"
- "查看哪些 skill 没用过"
- "清理多余的 skill"
- "skill 使用报告"
- "/skill-usage-stats"

## 数据源

1. **history.jsonl** - 用户命令历史（`~/.claude/history.jsonl`）
2. **会话文件** - 所有项目目录下的 `.jsonl` 文件（`~/.claude/projects/**/*.jsonl`）
3. **skills 目录** - 已安装的 skills（`~/.claude/skills/`）
4. **commands 目录** - 已安装的命令（`~/.claude/commands/`）

## 统计方法

### 1. 统计用户显式调用的 Skills

从 `history.jsonl` 中提取以 `/` 开头的命令：

```bash
cat ~/.claude/history.jsonl | python3 -c "
import sys
import json
from collections import Counter

skills = []
for line in sys.stdin:
    try:
        data = json.loads(line.strip())
        display = data.get('display', '')
        if display.startswith('/'):
            parts = display.split()
            skill = parts[0][1:]  # 去掉 /
            # 过滤非 skill 命令
            if skill and not skill.startswith(('api', 'Users', 'bin', 'var', 'settings')):
                skills.append(skill)
    except:
        pass

counter = Counter(skills)
for skill, count in counter.most_common():
    print(f'{count:4d}  /{skill}')
"
```

### 2. 统计自动调用的 Agents

从所有会话文件中提取 agent 调用记录：

```bash
find ~/.claude/projects -name "*.jsonl" -type f 2>/dev/null | \
  xargs grep -ohE 'claude-code-guide|go-reviewer|python-reviewer|code-reviewer|build-error-resolver|tdd-guide|e2e-runner|doc-updater|refactor-cleaner|architect|security-reviewer|database-reviewer|planner|Explore|Plan|general-purpose' 2>/dev/null | \
  sort | uniq -c | sort -rn
```

### 3. 统计 Skill Tool 调用

```bash
find ~/.claude/projects -name "*.jsonl" -type f 2>/dev/null | \
  xargs grep -ohE '"skill":\s*"[^"]+"' 2>/dev/null | \
  sort | uniq -c | sort -rn
```

### 4. 列出已安装的 Skills

```bash
ls ~/.claude/skills/
```

## 输出格式

生成报告应包含以下部分：

### 📊 数据来源概览
- history.jsonl 记录数
- 会话文件数量

### 🎯 用户显式调用的 Skills
表格形式：次数 | Skill 名称

### 🤖 自动调用的 Agents
表格形式：次数 | Agent 名称 | 说明

### 📦 已安装 Skills 清单
分类显示：
- ✅ 已使用 - 建议保留
- ❌ 未使用 - 可考虑清理

### 💡 清理建议
提供删除命令：
```bash
rm -rf ~/.claude/skills/<skill-name>
```

## 内置 Agents 列表

| Agent | 说明 |
|-------|------|
| Plan | 规划代理 |
| Explore | 代码库探索 |
| architect | 架构设计 |
| code-reviewer | 代码审查 |
| tdd-guide | TDD 指导 |
| security-reviewer | 安全审查 |
| build-error-resolver | 构建错误解决 |
| refactor-cleaner | 重构清理 |
| e2e-runner | E2E 测试 |
| doc-updater | 文档更新 |
| python-reviewer | Python 审查 |
| go-reviewer | Go 审查 |
| database-reviewer | 数据库审查 |
| claude-code-guide | Claude Code 指南 |
| general-purpose | 通用代理 |
| planner | 规划器 |

## 注意事项

1. **数据完整性**：history.jsonl 可能只记录部分历史，统计结果仅供参考
2. **自动调用**：某些 skills 可能被自动调用而非用户显式调用
3. **内置命令**：`/init`、`/model`、`/help` 等是内置命令，非 skills
4. **依赖关系**：删除 skill 前确认没有其他 skill 依赖它

## 示例用法

```
用户: 统计我的 skill 使用情况
用户: 帮我清理没用过的 skill
用户: 哪些 skill 我从来没调用过
```
