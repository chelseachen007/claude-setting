#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
小红书内容适配器
将长文章转换为小红书格式：标题 ≤20字、正文 ≤1000字、emoji 风格
"""

import re
import os
import json
import argparse


class XHSAdapter:
    """小红书内容适配器"""

    # 小红书限制
    MAX_TITLE_LENGTH = 20
    MAX_CONTENT_LENGTH = 1000

    # emoji 映射
    SECTION_EMOJIS = ['🔥', '💡', '👇', '🎯', '⚡', '📌', '✨', '🚀', '💪', '🌟']

    def adapt_title(self, title: str) -> str:
        """适配标题：截断到20字"""
        # 移除冒号后缀
        title = re.sub(r'[：:].+$', '', title).strip()
        # 移除末尾标点
        title = re.sub(r'[？！!?]+$', '', title).strip()
        # 截断
        if len(title) > self.MAX_TITLE_LENGTH:
            title = title[:self.MAX_TITLE_LENGTH - 1] + '…'
        return title

    def adapt_content(self, content: str, title: str = "") -> dict:
        """
        将 HTML/Markdown 内容适配为小红书格式

        Returns:
            {"title": str, "content": str, "original_length": int, "adapted_length": int}
        """
        original_length = len(content)

        # 1. 清理 HTML 标签
        text = self._strip_html(content)

        # 2. 提取核心要点（取前3-5个段落）
        paragraphs = [p.strip() for p in text.split('\n') if p.strip()]
        core_points = paragraphs[:5] if len(paragraphs) > 5 else paragraphs

        # 3. 构建 emoji 风格内容
        sections = []

        # 开头引子
        xhs_title = self.adapt_title(title) if title else "分享"
        sections.append(f"📌 {xhs_title}\n")

        # 核心内容
        for i, point in enumerate(core_points):
            emoji = self.SECTION_EMOJIS[i % len(self.SECTION_EMOJIS)]
            # 每段不超过150字
            if len(point) > 150:
                point = point[:147] + '...'
            sections.append(f"{emoji} {point}")

        # CTA
        sections.append("\n💬 欢迎评论点赞收藏～")

        xhs_content = '\n\n'.join(sections)

        # 4. 截断到1000字
        if len(xhs_content) > self.MAX_CONTENT_LENGTH:
            xhs_content = xhs_content[:self.MAX_CONTENT_LENGTH - 3] + '...'

        return {
            "title": xhs_title,
            "content": xhs_content,
            "original_length": original_length,
            "adapted_length": len(xhs_content)
        }

    def _strip_html(self, html: str) -> str:
        """清理 HTML 标签，保留纯文本"""
        # 移除 style/script 标签
        text = re.sub(r'<style[^>]*>.*?</style>', '', html, flags=re.DOTALL | re.IGNORECASE)
        text = re.sub(r'<script[^>]*>.*?</script>', '', text, flags=re.DOTALL | re.IGNORECASE)
        # 移除 HTML 标签
        text = re.sub(r'<[^>]+>', '', text)
        # 解码 HTML 实体
        text = text.replace('&nbsp;', ' ').replace('&amp;', '&').replace('&lt;', '<').replace('&gt;', '>')
        # 压缩空白
        text = re.sub(r'\n{3,}', '\n\n', text)
        text = text.strip()
        return text


def main():
    parser = argparse.ArgumentParser(description='小红书内容适配器')
    parser.add_argument('-t', '--title', required=True, help='原标题')
    parser.add_argument('-c', '--content', required=True, help='内容文件路径或直接文本')
    parser.add_argument('-o', '--output', default='', help='输出文件路径（默认 stdout）')

    args = parser.parse_args()

    content = args.content
    if os.path.exists(content):
        with open(content, 'r', encoding='utf-8') as f:
            content = f.read()

    adapter = XHSAdapter()
    result = adapter.adapt_content(content, args.title)

    output = json.dumps(result, ensure_ascii=False, indent=2)

    if args.output:
        with open(args.output, 'w', encoding='utf-8') as f:
            f.write(output)
        print(f"[小红书] 适配结果已保存到: {args.output}")
    else:
        print(output)


if __name__ == '__main__':
    main()
