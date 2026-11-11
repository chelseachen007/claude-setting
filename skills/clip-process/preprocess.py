#!/usr/bin/env python3
"""
剪藏排版预处理脚本
处理 ## 原文 章节内的碎片化文字和排版问题。
用法: python3 preprocess.py <剪藏文件路径>
"""
import re
import sys


def _needs_space(a: str, b: str) -> bool:
    """判断两个文本片段之间是否需要加空格。"""
    if not a or not b:
        return False
    ca, cb = a[-1], b[0]
    # Chinese char followed by ASCII (or vice versa)
    if re.match(r"[\u4e00-\u9fff]", ca) and re.match(r"[a-zA-Z0-9\[\(]", cb):
        return True
    if re.match(r"[a-zA-Z0-9\]\)]", ca) and re.match(r"[\u4e00-\u9fff]", cb):
        return True
    return False


def _smart_join(parts: list[str]) -> str:
    """智能拼接文本片段，在需要的地方插入空格。"""
    if not parts:
        return ""
    result = parts[0]
    for p in parts[1:]:
        if _needs_space(result, p):
            result += " "
        result += p
    return result


def is_fragmented(lines: list[str]) -> bool:
    """检测文字是否碎片化（每字/标点独立一行）。
    判断标准：单字符行占比超过 30%。
    """
    text_lines = [l.strip() for l in lines if l.strip()]
    if len(text_lines) < 10:
        return False
    short = sum(1 for l in text_lines if len(l) <= 2)
    return short / len(text_lines) > 0.3


def merge_fragmented_text(original_text: str) -> str:
    """将碎片化的文字（每字/标点独立一行）合并为正常段落。"""
    lines = original_text.split("\n")
    tokens = []

    for line in lines:
        s = line.strip()
        if not s:
            continue
        if s.startswith("#"):
            tokens.append(("header", s))
        elif s.startswith("![]"):
            tokens.append(("image", s))
        elif s.startswith("|"):
            tokens.append(("table_row", s))
        elif s.startswith(">"):
            tokens.append(("callout", s))
        elif re.match(r"^[-*]\s", s) or re.match(r"^\d+[\.\、]", s):
            tokens.append(("list", s))
        else:
            tokens.append(("text", s))

    result_lines = []
    i = 0
    while i < len(tokens):
        typ, txt = tokens[i]

        # Structural elements → standalone lines with paragraph breaks
        if typ in ("header", "image", "table_row", "callout", "list"):
            result_lines.append(txt)
            i += 1
            continue

        # Text: collect consecutive text, but stop before structural elements
        text_parts = []
        while i < len(tokens) and tokens[i][0] == "text":
            text_parts.append(tokens[i][1])
            i += 1

        if not text_parts:
            continue

        full_text = _smart_join(text_parts)
        full_text = re.sub(r"\s+([，。！？；：、）】》])", r"\1", full_text)
        full_text = re.sub(r"([（【《])\s+", r"\1", full_text)

        # Split at sentence-ending punctuation only (。！？)
        sentences = re.split(r"(?<=[。！？])", full_text)
        for sent in sentences:
            sent = sent.strip()
            if sent:
                result_lines.append(sent)

    return "\n\n".join(result_lines)


def fix_bold_artifacts(text: str) -> str:
    """修复合并文字后产生的加粗格式错乱。"""
    # **text****：** → **text**：
    text = re.sub(r"\*\*([^*]+)\*\*\*\*([，。！？；：、])\*\*", r"**\1**\2", text)
    # **...****，****...** → **...，...**
    text = re.sub(
        r"\*\*([^*]+)\*\*\*\*([，。！？；：、])\*\*\*\*([^*]+)\*\*",
        r"**\1\2\3**",
        text,
    )
    # leftover **** → **
    text = re.sub(r"\*\*\*\*", "**", text)
    return text


def normalize_empty_lines(text: str) -> str:
    """连续空行合并为 1 个。"""
    return re.sub(r"\n{3,}", "\n\n", text)


def trim_lines(text: str) -> str:
    """去除每行首尾空格。"""
    return "\n".join(line.strip() for line in text.split("\n"))


def fix_chinese_punctuation_spacing(text: str) -> str:
    """中文标点后紧跟的空格去除（不跨行，保留换行）。"""
    return re.sub(r"([，。！？；：]) +", r"\1", text)


def fix_headers(text: str) -> str:
    """Markdown 标题：# 后必须有且仅有一个空格，标题内不允许空格。"""

    def _fix(m):
        hashes = m.group(1)
        title = m.group(2).strip()
        title = re.sub(r"\s+", "", title)
        return f"{hashes} {title}"

    return re.sub(r"^(#{1,6})\s*(.+)$", _fix, text, flags=re.MULTILINE)


def preprocess(filepath: str):
    with open(filepath, "r", encoding="utf-8") as f:
        content = f.read()

    # Split frontmatter
    parts = content.split("---", 2)
    if len(parts) >= 3:
        frontmatter = parts[1]
        body = parts[2]
    else:
        frontmatter = ""
        body = content

    # Fix frontmatter title
    frontmatter = re.sub(
        r"^(title:\s*)(.+)$",
        lambda m: m.group(1) + re.sub(r"\s+", "", m.group(2)),
        frontmatter,
        flags=re.MULTILINE,
    )

    # Fix frontmatter tags (remove erroneous quotes/dashes)
    frontmatter = re.sub(r'-\s*"?-\s*状态/', "- 状态/", frontmatter)

    # Find ## 原文 section
    match = re.search(r"(## 原文\s*\n)", body)
    if not match:
        print("ERROR: 未找到 ## 原文 章节")
        sys.exit(1)

    before = body[: match.end()]
    rest = body[match.end():]

    # Find next ## section
    next_match = re.search(
        r"\n## (?:入库思考|金句摘抄|闪念|常青笔记|连接|行动|出处)", rest
    )
    if next_match:
        original_text = rest[: next_match.start()]
        after = rest[next_match.start():]
    else:
        original_text = rest
        after = ""

    old_lines = len(original_text.strip().split("\n"))

    # Pipeline: only merge if text is actually fragmented
    lines = original_text.split("\n")
    if is_fragmented(lines):
        original_text = merge_fragmented_text(original_text)
        original_text = fix_bold_artifacts(original_text)
        merged = True
    else:
        merged = False

    original_text = trim_lines(original_text)
    original_text = fix_chinese_punctuation_spacing(original_text)
    original_text = fix_headers(original_text)
    original_text = normalize_empty_lines(original_text)

    new_lines = len(original_text.strip().split("\n"))

    new_content = "---" + frontmatter + "---" + before + original_text + after
    new_content = normalize_empty_lines(new_content)

    with open(filepath, "w", encoding="utf-8") as f:
        f.write(new_content)

    mode = "碎片合并" if merged else "常规清理"
    print(f"预处理完成（{mode}）：原文 {old_lines} 行 → {new_lines} 行")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("用法: python3 preprocess.py <剪藏文件路径>")
        sys.exit(1)
    preprocess(sys.argv[1])
