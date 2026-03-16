#!/usr/bin/env python3
# /// script
# requires-python = ">=3.10"
# dependencies = [
#     "httpx",
#     "beautifulsoup4",
# ]
# ///
"""
微博热搜和搜索工具

直接调用微博移动端 API，获取热搜榜、搜索用户、搜索内容、获取用户动态等。

使用方法:
    uv run weibo_cli.py trending --limit 10
    uv run weibo_cli.py search-users --keyword "雷军" --limit 5
    uv run weibo_cli.py search-content --keyword "AI" --limit 10
    uv run weibo_cli.py user-profile --uid 1749127163
    uv run weibo_cli.py user-feeds --uid 1749127163 --limit 10
    uv run weibo_cli.py comments --feed-id 5167970394572058 --page 1
"""

from __future__ import annotations

import argparse
import asyncio
import json
import re
import sys
from dataclasses import dataclass, asdict
from typing import Optional
from urllib.parse import urlencode

import httpx


# API URLs
PROFILE_URL = "https://m.weibo.cn/api/container/getIndex?type=uid&value={userId}"
FEEDS_URL = "https://m.weibo.cn/api/container/getIndex?type=uid&value={userId}&containerid={containerId}&since_id={sinceId}"
SEARCH_URL = "https://m.weibo.cn/api/container/getIndex"
COMMENTS_URL = "https://m.weibo.cn/api/comments/show?id={feed_id}&page={page}"

DEFAULT_HEADERS = {
    "Content-Type": "application/json",
}


@dataclass
class UserProfile:
    id: int
    screen_name: str
    profile_image_url: str
    profile_url: str
    description: str
    follow_count: int
    followers_count: str
    avatar_hd: str
    verified: bool
    verified_reason: str
    gender: str


@dataclass
class FeedItem:
    id: str
    text: str
    source: str
    created_at: str
    user: dict
    comments_count: int
    attitudes_count: int
    reposts_count: int
    raw_text: str
    region_name: str
    pics: list
    videos: dict


@dataclass
class TrendingItem:
    id: int
    trending: int
    description: str
    url: str


@dataclass
class CommentItem:
    id: str
    text: str
    created_at: str
    user: dict
    source: str
    reply_id: Optional[str]
    reply_text: str


class WeiboClient:
    """微博 API 客户端"""

    def __init__(self):
        pass

    def _to_user_profile(self, user: dict) -> UserProfile:
        return UserProfile(
            id=user.get("id", 0),
            screen_name=user.get("screen_name", ""),
            profile_image_url=user.get("profile_image_url", ""),
            profile_url=user.get("profile_url", ""),
            description=user.get("description", ""),
            follow_count=user.get("follow_count", 0),
            followers_count=str(user.get("followers_count", "")),
            avatar_hd=user.get("avatar_hd", ""),
            verified=user.get("verified", False),
            verified_reason=user.get("verified_reason", ""),
            gender=user.get("gender", ""),
        )

    def _to_feed_item(self, mblog: dict) -> FeedItem:
        pics = []
        if mblog.get("pics"):
            pics = [
                {"thumbnail": pic.get("url", ""), "large": pic.get("large", {}).get("url", "")}
                for pic in mblog["pics"]
                if "url" in pic
            ]

        videos = {}
        page_info = mblog.get("page_info")
        if page_info and page_info.get("type") == "video":
            if "media_info" in page_info:
                videos["stream_url"] = page_info["media_info"].get("stream_url", "")
                videos["stream_url_hd"] = page_info["media_info"].get("stream_url_hd", "")

        user = asdict(self._to_user_profile(mblog.get("user", {}))) if mblog.get("user") else {}

        return FeedItem(
            id=mblog.get("id", ""),
            text=mblog.get("text", ""),
            source=mblog.get("source", ""),
            created_at=mblog.get("created_at", ""),
            user=user,
            comments_count=mblog.get("comments_count", 0),
            attitudes_count=mblog.get("attitudes_count", 0),
            reposts_count=mblog.get("reposts_count", 0),
            raw_text=mblog.get("raw_text", ""),
            region_name=mblog.get("region_name", ""),
            pics=pics,
            videos=videos,
        )

    def _to_trending_item(self, item: dict) -> TrendingItem:
        extr_values = re.findall(r"\d+", str(item.get("desc_extr", "")))
        trending = int(extr_values[0]) if extr_values else 0
        return TrendingItem(
            id=item.get("id", 0),
            trending=trending,
            description=item.get("desc", ""),
            url=item.get("scheme", ""),
        )

    def _to_comment_item(self, item: dict) -> CommentItem:
        user = asdict(self._to_user_profile(item.get("user", {}))) if item.get("user") else {}
        return CommentItem(
            id=item.get("id", ""),
            text=item.get("text", ""),
            created_at=item.get("created_at", ""),
            user=user,
            source=item.get("source", ""),
            reply_id=item.get("reply_id"),
            reply_text=item.get("reply_text", ""),
        )

    async def get_trendings(self, limit: int = 15) -> list[dict]:
        """获取微博热搜榜"""
        params = {
            "containerid": "106003type=25&t=3&disable_hot=1&filter_type=realtimehot",
        }
        encoded_params = urlencode(params)

        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{SEARCH_URL}?{encoded_params}",
                headers=DEFAULT_HEADERS,
                timeout=30,
            )
            data = response.json()

        cards = data.get("data", {}).get("cards", [])
        if not cards:
            return []

        hot_search_card = next(
            (card for card in cards if "card_group" in card and isinstance(card["card_group"], list)),
            None,
        )
        if not hot_search_card:
            return []

        items = [item for item in hot_search_card["card_group"] if item.get("desc")]
        trending_items = [
            asdict(self._to_trending_item({**item, "id": idx}))
            for idx, item in enumerate(items[:limit])
        ]
        return trending_items

    async def search_users(self, keyword: str, limit: int = 5, page: int = 1) -> list[dict]:
        """搜索微博用户"""
        params = {
            "containerid": f"100103type=3&q={keyword}",
            "page_type": "searchall",
            "page": page,
        }
        encoded_params = urlencode(params)

        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{SEARCH_URL}?{encoded_params}",
                headers=DEFAULT_HEADERS,
                timeout=30,
            )
            result = response.json()

        cards = result.get("data", {}).get("cards", [])
        if len(cards) < 2:
            return []

        card_group = cards[1].get("card_group", [])
        users = [asdict(self._to_user_profile(item["user"])) for item in card_group if "user" in item]
        return users[:limit]

    async def search_content(self, keyword: str, limit: int = 15, page: int = 1) -> list[dict]:
        """搜索微博内容"""
        params = {
            "containerid": f"100103type=1&q={keyword}",
            "page_type": "searchall",
            "page": page,
        }
        encoded_params = urlencode(params)

        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{SEARCH_URL}?{encoded_params}",
                headers=DEFAULT_HEADERS,
                timeout=30,
            )
            data = response.json()

        cards = data.get("data", {}).get("cards", [])
        content_cards = []

        for card in cards:
            if card.get("card_type") == 9:
                content_cards.append(card)
            elif "card_group" in card and isinstance(card["card_group"], list):
                content_group = [
                    item for item in card["card_group"] if item.get("card_type") == 9
                ]
                content_cards.extend(content_group)

        results = []
        for card in content_cards[:limit]:
            mblog = card.get("mblog")
            if mblog:
                results.append(asdict(self._to_feed_item(mblog)))

        return results

    async def get_profile(self, uid: int) -> dict:
        """获取用户资料"""
        async with httpx.AsyncClient() as client:
            response = await client.get(
                PROFILE_URL.format(userId=uid),
                headers=DEFAULT_HEADERS,
                timeout=30,
            )
            result = response.json()

        user_info = result.get("data", {}).get("userInfo", {})
        return asdict(self._to_user_profile(user_info)) if user_info else {}

    async def get_feeds(self, uid: int, limit: int = 15) -> list[dict]:
        """获取用户微博动态"""
        feeds = []
        since_id = ""

        async with httpx.AsyncClient() as client:
            # 获取 container ID
            response = await client.get(
                PROFILE_URL.format(userId=uid),
                headers=DEFAULT_HEADERS,
                timeout=30,
            )
            data = response.json()

            tabs_info = data.get("data", {}).get("tabsInfo", {}).get("tabs", [])
            container_id = None
            for tab in tabs_info:
                if tab.get("tabKey") == "weibo":
                    container_id = tab.get("containerid")
                    break

            if not container_id:
                return []

            # 获取微博
            while len(feeds) < limit:
                url = FEEDS_URL.format(
                    userId=uid,
                    containerId=container_id,
                    sinceId=since_id,
                )
                response = await client.get(url, headers=DEFAULT_HEADERS, timeout=30)
                data = response.json()

                new_since_id = data.get("data", {}).get("cardlistInfo", {}).get("since_id", "")
                cards = data.get("data", {}).get("cards", [])

                for card in cards:
                    if len(feeds) >= limit:
                        break
                    mblog = card.get("mblog")
                    if mblog:
                        feeds.append(asdict(self._to_feed_item(mblog)))

                since_id = new_since_id
                if not since_id:
                    break

        return feeds[:limit]

    async def get_comments(self, feed_id: str, page: int = 1) -> list[dict]:
        """获取微博评论"""
        async with httpx.AsyncClient() as client:
            url = COMMENTS_URL.format(feed_id=feed_id, page=page)
            response = await client.get(url, headers=DEFAULT_HEADERS, timeout=30)
            data = response.json()

        comments = data.get("data", {}).get("data", [])
        return [asdict(self._to_comment_item(c)) for c in comments]


async def main():
    parser = argparse.ArgumentParser(
        description="微博热搜和搜索工具",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    # trending 子命令
    trending_parser = subparsers.add_parser("trending", help="获取微博热搜榜")
    trending_parser.add_argument("--limit", "-l", type=int, default=15, help="返回数量")

    # search-users 子命令
    users_parser = subparsers.add_parser("search-users", help="搜索微博用户")
    users_parser.add_argument("--keyword", "-k", required=True, help="搜索关键词")
    users_parser.add_argument("--limit", "-l", type=int, default=5, help="返回数量")

    # search-content 子命令
    content_parser = subparsers.add_parser("search-content", help="搜索微博内容")
    content_parser.add_argument("--keyword", "-k", required=True, help="搜索关键词")
    content_parser.add_argument("--limit", "-l", type=int, default=15, help="返回数量")
    content_parser.add_argument("--page", "-p", type=int, default=1, help="页码")

    # user-profile 子命令
    profile_parser = subparsers.add_parser("user-profile", help="获取用户资料")
    profile_parser.add_argument("--uid", "-u", type=int, required=True, help="用户ID")

    # user-feeds 子命令
    feeds_parser = subparsers.add_parser("user-feeds", help="获取用户动态")
    feeds_parser.add_argument("--uid", "-u", type=int, required=True, help="用户ID")
    feeds_parser.add_argument("--limit", "-l", type=int, default=15, help="返回数量")

    # comments 子命令
    comments_parser = subparsers.add_parser("comments", help="获取微博评论")
    comments_parser.add_argument("--feed-id", "-f", required=True, help="微博ID")
    comments_parser.add_argument("--page", "-p", type=int, default=1, help="页码")

    args = parser.parse_args()
    client = WeiboClient()

    try:
        if args.command == "trending":
            result = await client.get_trendings(args.limit)
        elif args.command == "search-users":
            result = await client.search_users(args.keyword, args.limit)
        elif args.command == "search-content":
            result = await client.search_content(args.keyword, args.limit, args.page)
        elif args.command == "user-profile":
            result = await client.get_profile(args.uid)
        elif args.command == "user-feeds":
            result = await client.get_feeds(args.uid, args.limit)
        elif args.command == "comments":
            result = await client.get_comments(args.feed_id, args.page)
        else:
            result = {"error": f"Unknown command: {args.command}"}

        print(json.dumps(result, ensure_ascii=False, indent=2))
    except Exception as e:
        error_result = {"success": False, "error": str(e)}
        print(json.dumps(error_result, ensure_ascii=False, indent=2))
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
