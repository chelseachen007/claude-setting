#!/bin/bash
# Skill Vetter Hook - 在安装 skill 时自动执行安全审查

TOOL_INPUT="$1"

# 检查是否是写入 skills 目录的 SKILL.md 文件
if echo "$TOOL_INPUT" | grep -q '\.claude/skills/.*SKILL\.md'; then
    # 提取文件路径
    FILE_PATH=$(echo "$TOOL_INPUT" | grep -oE '/[^"]*\.claude/skills/[^"]+SKILL\.md' | head -1)

    # 提取 skill 名称
    SKILL_NAME=$(echo "$FILE_PATH" | grep -oE 'skills/[^/]+/' | sed 's/skills\///; s/\///')

    # 提取 skill 内容
    CONTENT=$(echo "$TOOL_INPUT" | grep -oE '"content":"[^"]*"' | sed 's/"content":"//; s/"$//' | head -1)

    echo ""
    echo "╔════════════════════════════════════════════════════════════════╗"
    echo "║  🔒 SKILL VETTER - 检测到新 Skill 安装                          ║"
    echo "╚════════════════════════════════════════════════════════════════╝"
    echo ""
    echo "Skill 名称: $SKILL_NAME"
    echo "文件路径: $FILE_PATH"
    echo ""

    # 检查危险模式
    RED_FLAGS=""

    # 检查 curl/wget 到未知 URL
    if echo "$CONTENT" | grep -qiE 'curl.*http|wget.*http'; then
        RED_FLAGS="${RED_FLAGS}⚠️  发现 curl/wget 网络请求\n"
    fi

    # 检查发送数据到外部服务器
    if echo "$CONTENT" | grep -qiE 'fetch\(|axios|XMLHttpRequest|\.post\(|\.get\('; then
        RED_FLAGS="${RED_FLAGS}⚠️  可能发送数据到外部服务器\n"
    fi

    # 检查请求凭据
    if echo "$CONTENT" | grep -qiE 'password|credential|token|api_key|secret|auth'; then
        RED_FLAGS="${RED_FLAGS}⚠️  涉及凭据/密钥相关内容\n"
    fi

    # 检查访问敏感文件
    if echo "$CONTENT" | grep -qiE '\.ssh|\.aws|\.config|MEMORY\.md|USER\.md|SOUL\.md|IDENTITY\.md'; then
        RED_FLAGS="${RED_FLAGS}⚠️  访问敏感配置文件\n"
    fi

    # 检查 base64 解码
    if echo "$CONTENT" | grep -qiE 'base64|atob|btoa'; then
        RED_FLAGS="${RED_FLAGS}⚠️  使用 base64 编码/解码\n"
    fi

    # 检查 eval/exec
    if echo "$CONTENT" | grep -qiE 'eval\(|exec\(|Function\('; then
        RED_FLAGS="${RED_FLAGS}⚠️  使用 eval/exec 动态执行\n"
    fi

    # 检查 sudo/权限提升
    if echo "$CONTENT" | grep -qiE 'sudo|chmod.*777|chown'; then
        RED_FLAGS="${RED_FLAGS}⚠️  请求提升权限\n"
    fi

    # 输出审查结果
    if [ -z "$RED_FLAGS" ]; then
        echo "─────────────────────────────────────────────────────────────────"
        echo "✅ 安全检查: 未发现明显危险模式"
        echo "─────────────────────────────────────────────────────────────────"
        echo ""
    else
        echo "─────────────────────────────────────────────────────────────────"
        echo "🚨 发现以下潜在风险:"
        echo "─────────────────────────────────────────────────────────────────"
        echo -e "$RED_FLAGS"
        echo "⚠️  建议在安装前仔细审查此 Skill 的完整内容"
        echo ""
    fi

    echo "💡 提示: 使用 /skill-vetter 命令可进行更详细的安全审查"
    echo ""
fi
