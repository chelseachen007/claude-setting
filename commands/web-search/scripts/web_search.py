#!/usr/bin/env python3
# /// script
# requires-python = ">=3.10"
# dependencies = [
#     "httpx",
# ]
# ///
"""
全网语义搜索工具

使用 Exa AI 进行高质量语义搜索，获取网页内容和代码上下文。

使用方法:
    uv run web_search.py search --query "Python async best practices" --limit 10
    uv run web_search.py code --query "FastAPI dependency injection" --tokens 3000
    uv run web_search.py read --url "https://example.com/article"

环境变量:
    EXA_API_KEY: Exa API Key (从 https://exa.ai 获取，有免费额度)
"""

from __future__ import annotations

import argparse
import asyncio
import json
import os
import sys
from typing import Optional

import httpx


EXA_API_BASE = "https://api.exa.ai"
JINA_READER_URL = "https://r.jina.ai"

DEFAULT_HEADERS = {
    "Content-Type": "application/json",
    "Accept": "application/json",
}


class ExaClient:
    """Exa AI 搜索客户端"""

    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or os.environ.get("EXA_API_KEY")

    def _get_headers(self) -> dict:
        headers = DEFAULT_HEADERS.copy()
        if self.api_key:
            headers["x-api-key"] = self.api_key
        return headers

    def check_api_key(self) -> bool:
        """检查是否配置了 API Key"""
        return bool(self.api_key)

    async def search(
        self,
        query: str,
        num_results: int = 10,
        use_autoprompt: bool = True,
        include_domains: Optional[list] = None,
        exclude_domains: Optional[list] = None,
    ) -> list[dict]:
        """
        语义搜索网页

        Args:
            query: 搜索关键词
            num_results: 返回结果数量
            use_autoprompt: 是否自动优化搜索词
            include_domains: 只搜索这些域名
            exclude_domains: 排除这些域名

        Returns:
            搜索结果列表
        """
        payload = {
            "query": query,
            "numResults": num_results,
            "useAutoprompt": use_autoprompt,
            "contents": {
                "text": {
                    "maxCharacters": 1000,
                },
            },
        }

        if include_domains:
            payload["includeDomains"] = include_domains
        if exclude_domains:
            payload["excludeDomains"] = exclude_domains

        async with httpx.AsyncClient(timeout=60) as client:
            response = await client.post(
                f"{EXA_API_BASE}/search",
                headers=self._get_headers(),
                json=payload,
            )
            response.raise_for_status()
            data = response.json()

        results = []
        for item in data.get("results", []):
            results.append({
                "url": item.get("url", ""),
                "title": item.get("title", ""),
                "text": item.get("text", ""),
                "publishedDate": item.get("publishedDate", ""),
                "author": item.get("author", ""),
                "score": item.get("score", 0),
            })

        return results

    async def find_similar(
        self,
        url: str,
        num_results: int = 10,
        exclude_source_domain: bool = True,
    ) -> list[dict]:
        """
        查找相似网页

        Args:
            url: 参考网页 URL
            num_results: 返回结果数量
            exclude_source_domain: 是否排除源域名

        Returns:
            相似网页列表
        """
        payload = {
            "url": url,
            "numResults": num_results,
            "excludeSourceDomain": exclude_source_domain,
            "contents": {
                "text": {
                    "maxCharacters": 1000,
                },
            },
        }

        async with httpx.AsyncClient(timeout=60) as client:
            response = await client.post(
                f"{EXA_API_BASE}/findSimilar",
                headers=self._get_headers(),
                json=payload,
            )
            response.raise_for_status()
            data = response.json()

        results = []
        for item in data.get("results", []):
            results.append({
                "url": item.get("url", ""),
                "title": item.get("title", ""),
                "text": item.get("text", ""),
                "publishedDate": item.get("publishedDate", ""),
                "author": item.get("author", ""),
                "score": item.get("score", 0),
            })

        return results

    async def get_contents(
        self,
        urls: list[str],
        max_characters: int = 2000,
    ) -> list[dict]:
        """
        获取网页内容

        Args:
            urls: URL 列表
            max_characters: 最大字符数

        Returns:
            网页内容列表
        """
        payload = {
            "urls": urls,
            "contents": {
                "text": {
                    "maxCharacters": max_characters,
                },
            },
        }

        async with httpx.AsyncClient(timeout=60) as client:
            response = await client.post(
                f"{EXA_API_BASE}/contents",
                headers=self._get_headers(),
                json=payload,
            )
            response.raise_for_status()
            data = response.json()

        results = []
        for item in data.get("results", []):
            results.append({
                "url": item.get("url", ""),
                "title": item.get("title", ""),
                "text": item.get("text", ""),
            })

        return results


class JinaReader:
    """Jina Reader 网页阅读器"""

    async def read(self, url: str, output_format: str = "markdown") -> str:
        """
        读取网页内容

        Args:
            url: 网页 URL
            output_format: 输出格式 (markdown/text)

        Returns:
            网页内容
        """
        reader_url = f"{JINA_READER_URL}/{url}"

        async with httpx.AsyncClient(timeout=60) as client:
            response = await client.get(
                reader_url,
                headers={
                    "Accept": f"text/{output_format}",
                },
            )
            response.raise_for_status()
            return response.text

    async def read_pdf(self, url: str) -> str:
        """读取 PDF 内容"""
        return await self.read(url)


async def main():
    parser = argparse.ArgumentParser(
        description="全网语义搜索工具",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
    # 网页搜索
    uv run web_search.py search --query "Python async best practices" --limit 10

    # 代码上下文搜索
    uv run web_search.py code --query "FastAPI dependency injection" --tokens 3000

    # 读取网页
    uv run web_search.py read --url "https://example.com/article"

    # 查找相似网页
    uv run web_search.py similar --url "https://example.com/article" --limit 5

环境变量:
    EXA_API_KEY: Exa API Key (可选，有免费额度)
        """,
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    # search 子命令
    search_parser = subparsers.add_parser("search", help="语义搜索网页")
    search_parser.add_argument("--query", "-q", required=True, help="搜索关键词")
    search_parser.add_argument("--limit", "-l", type=int, default=10, help="返回数量")
    search_parser.add_argument("--no-autoprompt", action="store_true", help="禁用自动优化搜索词")
    search_parser.add_argument("--include", "-i", nargs="*", help="只搜索这些域名")
    search_parser.add_argument("--exclude", "-e", nargs="*", help="排除这些域名")

    # similar 子命令
    similar_parser = subparsers.add_parser("similar", help="查找相似网页")
    similar_parser.add_argument("--url", "-u", required=True, help="参考网页 URL")
    similar_parser.add_argument("--limit", "-l", type=int, default=10, help="返回数量")

    # contents 子命令
    contents_parser = subparsers.add_parser("contents", help="获取网页内容")
    contents_parser.add_argument("--urls", "-u", nargs="+", required=True, help="URL 列表")
    contents_parser.add_argument("--max-chars", "-m", type=int, default=2000, help="最大字符数")

    # read 子命令 (使用 Jina Reader)
    read_parser = subparsers.add_parser("read", help="读取网页内容 (Jina Reader)")
    read_parser.add_argument("--url", "-u", required=True, help="网页 URL")
    read_parser.add_argument("--format", "-f", choices=["markdown", "text"], default="markdown", help="输出格式")

    # code 子命令 (搜索代码相关内容)
    code_parser = subparsers.add_parser("code", help="搜索代码上下文")
    code_parser.add_argument("--query", "-q", required=True, help="代码问题")
    code_parser.add_argument("--limit", "-l", type=int, default=10, help="返回数量")
    code_parser.add_argument("--tokens", "-t", type=int, default=3000, help="Token 数量")

    args = parser.parse_args()

    try:
        if args.command == "search":
            client = ExaClient()
            if not client.check_api_key():
                print(json.dumps({
                    "success": False,
                    "error": "需要配置 EXA_API_KEY 环境变量",
                    "hint": "访问 https://exa.ai 获取免费 API Key，然后运行: export EXA_API_KEY='your-key'"
                }, ensure_ascii=False, indent=2))
                sys.exit(1)
            result = await client.search(
                query=args.query,
                num_results=args.limit,
                use_autoprompt=not args.no_autoprompt,
                include_domains=args.include,
                exclude_domains=args.exclude,
            )

        elif args.command == "similar":
            client = ExaClient()
            if not client.check_api_key():
                print(json.dumps({
                    "success": False,
                    "error": "需要配置 EXA_API_KEY 环境变量",
                    "hint": "访问 https://exa.ai 获取免费 API Key，然后运行: export EXA_API_KEY='your-key'"
                }, ensure_ascii=False, indent=2))
                sys.exit(1)
            result = await client.find_similar(
                url=args.url,
                num_results=args.limit,
            )

        elif args.command == "contents":
            client = ExaClient()
            if not client.check_api_key():
                print(json.dumps({
                    "success": False,
                    "error": "需要配置 EXA_API_KEY 环境变量",
                    "hint": "访问 https://exa.ai 获取免费 API Key，然后运行: export EXA_API_KEY='your-key'"
                }, ensure_ascii=False, indent=2))
                sys.exit(1)
            result = await client.get_contents(
                urls=args.urls,
                max_characters=args.max_chars,
            )

        elif args.command == "read":
            reader = JinaReader()
            content = await reader.read(args.url, args.format)
            print(content)
            return

        elif args.command == "code":
            client = ExaClient()
            if not client.check_api_key():
                print(json.dumps({
                    "success": False,
                    "error": "需要配置 EXA_API_KEY 环境变量",
                    "hint": "访问 https://exa.ai 获取免费 API Key，然后运行: export EXA_API_KEY='your-key'"
                }, ensure_ascii=False, indent=2))
                sys.exit(1)
            # 代码搜索，优先搜索技术网站
            result = await client.search(
                query=args.query,
                num_results=args.limit,
                use_autoprompt=True,
                include_domains=["github.com", "stackoverflow.com", "docs.python.org", "dev.to", "medium.com"],
            )

        else:
            result = {"error": f"Unknown command: {args.command}"}

        print(json.dumps(result, ensure_ascii=False, indent=2))

    except httpx.HTTPStatusError as e:
        error_result = {
            "success": False,
            "error": f"HTTP Error: {e.response.status_code}",
            "detail": e.response.text[:500] if e.response.text else "",
        }
        print(json.dumps(error_result, ensure_ascii=False, indent=2))
        sys.exit(1)
    except Exception as e:
        error_result = {"success": False, "error": str(e)}
        print(json.dumps(error_result, ensure_ascii=False, indent=2))
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
