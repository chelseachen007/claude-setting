#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
微信公众号草稿箱发布工具
支持封面图上传、HTML 内容适配微信编辑器、草稿创建
基于 solar-luna/fully-automatic-article-generation-skill 改造
"""

import os
import sys
import json
import time
import re
import requests
import argparse
import tempfile
from pathlib import Path
from typing import Dict, Any


class WeChatPublisher:
    """微信公众号草稿发布器"""

    BASE_URL = "https://api.weixin.qq.com/cgi-bin"
    CONFIG_DIR = os.path.expanduser("~/.multi-publish")
    TOKEN_CACHE_FILE = os.path.expanduser("~/.multi-publish/wechat_token.json")
    CONFIG_FILE = os.path.expanduser("~/.multi-publish/wechat_config.json")

    ERROR_CODES = {
        40001: "AppSecret错误或者AppSecret不属于这个AppID",
        40002: "请确保grant_type字段值为client_credential",
        40013: "不合法的AppID，请检查AppID是否正确",
        40125: "无效的appsecret",
        40164: "调用接口的IP地址不在白名单中",
        41001: "缺少access_token参数",
        42001: "access_token超时",
        45009: "接口调用超过限制",
        47003: "参数错误",
        48001: "api功能未授权",
        -1: "系统繁忙，请稍后重试"
    }

    def __init__(self):
        self.appid = None
        self.appsecret = None
        self.access_token = None
        self._load_config()

    def _load_config(self):
        """加载微信配置"""
        if not os.path.exists(self.CONFIG_FILE):
            raise FileNotFoundError(
                f"微信配置文件不存在: {self.CONFIG_FILE}\n"
                f"请先运行: python wechat_publisher.py --setup\n"
                f"或手动创建配置文件，格式: {{\"appid\": \"wx...\", \"appsecret\": \"...\"}}"
            )

        with open(self.CONFIG_FILE, 'r', encoding='utf-8') as f:
            config = json.load(f)

        self.appid = config.get('appid', '').strip()
        self.appsecret = config.get('appsecret', '').strip()

        if not self.appid or not self.appid.startswith('wx'):
            raise ValueError(f"无效的AppID，请检查配置文件: {self.CONFIG_FILE}")
        if not self.appsecret:
            raise ValueError(f"无效的AppSecret，请检查配置文件: {self.CONFIG_FILE}")

        print(f"[微信] 配置加载成功 (AppID: {self.appid[:6]}***)")

    def setup(self):
        """交互式配置向导"""
        print("=" * 50)
        print("  微信公众号草稿发布 - 配置向导")
        print("=" * 50)
        print("\n获取凭证步骤：")
        print("  1. 登录 https://mp.weixin.qq.com")
        print("  2. 设置与开发 → 基本配置")
        print("  3. 复制 AppID 和 AppSecret\n")

        appid = input("AppID (wx开头): ").strip()
        appsecret = input("AppSecret: ").strip()

        if not appid.startswith('wx'):
            print("[警告] AppID 通常以 wx 开头")

        os.makedirs(os.path.dirname(self.CONFIG_FILE), exist_ok=True)
        with open(self.CONFIG_FILE, 'w', encoding='utf-8') as f:
            json.dump({"appid": appid, "appsecret": appsecret}, f, indent=2, ensure_ascii=False)
        os.chmod(self.CONFIG_FILE, 0o600)
        print(f"\n[微信] 配置已保存到: {self.CONFIG_FILE}")

    def _handle_error(self, errcode: int, errmsg: str, context: str = "") -> str:
        """统一错误处理"""
        cn_msg = self.ERROR_CODES.get(errcode, errmsg)
        detail = f"{context}失败 (错误码{errcode}): {cn_msg}"

        if errcode == 40164:
            detail += "\n解决: 登录 mp.weixin.qq.com → 设置 → 基本配置 → IP白名单 → 添加当前IP"
        elif errcode in [40001, 40125, 40013]:
            detail += f"\n解决: 检查配置文件 {self.CONFIG_FILE} 中的 AppID 和 AppSecret"
        elif errcode == 45009:
            detail += "\n解决: API调用次数已达上限，请明天再试"
        return detail

    def get_access_token(self, force_refresh: bool = False) -> str:
        """获取 access_token，带缓存"""
        if not force_refresh and os.path.exists(self.TOKEN_CACHE_FILE):
            try:
                with open(self.TOKEN_CACHE_FILE, 'r') as f:
                    cache = json.load(f)
                if time.time() < cache.get('expires_at', 0) - 300:
                    return cache['access_token']
            except Exception:
                pass

        url = f"{self.BASE_URL}/token"
        params = {
            'grant_type': 'client_credential',
            'appid': self.appid,
            'secret': self.appsecret
        }

        resp = requests.get(url, params=params)
        result = resp.json()

        if 'errcode' in result:
            raise Exception(self._handle_error(result['errcode'], result.get('errmsg', ''), "获取access_token"))

        token = result['access_token']
        expires_in = result.get('expires_in', 7200)

        os.makedirs(os.path.dirname(self.TOKEN_CACHE_FILE), exist_ok=True)
        with open(self.TOKEN_CACHE_FILE, 'w') as f:
            json.dump({
                'access_token': token,
                'expires_at': time.time() + expires_in,
                'updated_at': time.strftime('%Y-%m-%d %H:%M:%S')
            }, f, indent=2)

        print(f"[微信] access_token 获取成功")
        return token

    def _convert_to_jpg(self, image_path: str) -> str:
        """转换图片为 JPG 格式（微信要求）"""
        try:
            from PIL import Image
        except ImportError:
            raise ImportError("需要安装 Pillow: pip install Pillow")

        file_size = os.path.getsize(image_path)
        img = Image.open(image_path)

        if img.format == 'JPEG' and file_size <= 1024 * 1024:
            return image_path

        fd, temp_path = tempfile.mkstemp(suffix='.jpg')
        os.close(fd)

        if img.mode in ('RGBA', 'LA', 'P'):
            bg = Image.new('RGB', img.size, (255, 255, 255))
            if img.mode == 'P':
                img = img.convert('RGBA')
            bg.paste(img, mask=img.split()[-1] if img.mode in ('RGBA', 'LA') else None)
            img = bg
        elif img.mode != 'RGB':
            img = img.convert('RGB')

        img.save(temp_path, 'JPEG', quality=85, optimize=True)
        return temp_path

    def upload_image(self, image_path: str, return_url: bool = False):
        """上传图片到微信服务器"""
        if not os.path.exists(image_path):
            raise FileNotFoundError(f"图片不存在: {image_path}")

        print(f"[微信] 上传图片: {os.path.basename(image_path)}")
        converted_path = self._convert_to_jpg(image_path)

        token = self.get_access_token()
        url = f"{self.BASE_URL}/material/add_material"
        params = {'access_token': token, 'type': 'image'}

        with open(converted_path, 'rb') as f:
            files = {'media': (os.path.basename(converted_path), f, 'image/jpeg')}
            resp = requests.post(url, params=params, files=files)

        if converted_path != image_path:
            os.unlink(converted_path)

        result = resp.json()
        if 'errcode' in result and result['errcode'] != 0:
            raise Exception(self._handle_error(result['errcode'], result.get('errmsg', ''), "上传图片"))

        media_id = result.get('media_id')
        image_url = result.get('url', '')
        print(f"[微信] 图片上传成功 (media_id: {media_id})")

        return (media_id, image_url) if return_url else media_id

    def _upload_content_images(self, content: str, base_dir: str = ".") -> str:
        """上传 HTML 中的本地图片并替换为微信 URL"""
        img_pattern = r'<img([^>]*?)src=["\']([^"\']+)["\']([^>]*?)>'
        uploaded = 0

        def replace_image(match):
            nonlocal uploaded
            before, src, after = match.group(1), match.group(2), match.group(3)
            if src.startswith(('http://', 'https://')) or 'cover' in src.lower():
                return match.group(0)

            image_path = Path(base_dir) / src
            if not image_path.exists():
                return match.group(0)

            try:
                _, wechat_url = self.upload_image(str(image_path), return_url=True)
                if wechat_url:
                    uploaded += 1
                    return f'<img{before}src="{wechat_url}"{after}>'
            except Exception as e:
                print(f"[微信] 上传图片失败 {src}: {e}")
            return match.group(0)

        content = re.sub(img_pattern, replace_image, content)
        if uploaded > 0:
            print(f"[微信] 成功上传 {uploaded} 张内容图片")
        return content

    def _fix_wechat_styles(self, content: str) -> str:
        """修复微信编辑器样式破坏问题"""

        def add_important(style):
            parts = style.split(';')
            return ';'.join(
                p.strip() + '!important' if p.strip() and '!important' not in p else p
                for p in parts
            ) + ';'

        # 带背景色的 div 转为 table（微信保留 table 背景色）
        def convert_bg_to_table(match):
            style = match.group(2)
            inner = match.group(3)
            if 'font-family' in style and 'ffffff' in style.lower():
                return match.group(0)
            if 'background' not in style.lower():
                return match.group(0)
            margin_m = re.search(r'margin[^:]*:\s*([^;!]+)', style)
            margin = margin_m.group(1).strip() if margin_m else '0'
            style_imp = add_important(style)
            return (
                f'<table style="width:100%!important;border-collapse:separate!important;'
                f'border-spacing:0!important;border-radius:10px!important;'
                f'overflow:hidden!important;margin:{margin}!important;">'
                f'<tr><td style="{style_imp}">{inner}</td></tr></table>'
            )

        content = re.sub(
            r'<(div|section)\s+style="([^"]*background[^"]*)"[^>]*>(.*?)</\1>',
            convert_bg_to_table, content, flags=re.DOTALL | re.IGNORECASE
        )

        # 压缩空白
        content = re.sub(r'>\s+<', '><', content)

        # 移除不支持的 CSS
        content = re.sub(r'box-shadow:\s*[^;]+;\s*', '', content)
        content = re.sub(r'text-shadow:\s*[^;]+;\s*', '', content)
        content = re.sub(r'background:\s*linear-gradient[^;]+;', '', content)

        # 统一 background 为 background-color
        content = re.sub(r'\bbackground:\s*([#a-fA-F0-9]+);', r'background-color:\1!important;', content)
        content = re.sub(r'background-color:\s*([^;!]+);', r'background-color:\1!important;', content)

        # section → div
        content = content.replace('<section', '<div').replace('</section>', '</div>')

        # 关键属性添加 !important
        for prop in ['font-size', 'line-height', 'padding', 'text-align', 'display', 'vertical-align']:
            content = re.sub(
                rf'{prop}:\s*([^;!]+);',
                rf'{prop}: \1 !important;',
                content
            )

        # 禁用缩进
        content = re.sub(r'text-indent:\s*[^;!]+;', 'text-indent: 0 !important;', content)
        content = re.sub(
            r'style="(?![^"]*text-indent)([^"]*)"',
            r'style="\1 text-indent: 0 !important;"',
            content
        )

        # 图片圆角
        content = re.sub(
            r'<img([^>]*style="[^"]*)"',
            r'<img\1;border-radius:8px!important;"',
            content
        )

        return content

    def _remove_cover_image(self, content: str) -> str:
        """移除 HTML 中的封面图"""
        patterns = [
            r'<img[^>]*src=["\']cover\.(png|jpg|jpeg|gif)["\'][^>]*>',
            r'<img[^>]*alt=["\'][^"\']*封面[^"\']*["\'][^>]*>',
        ]
        for p in patterns:
            content = re.sub(p, '', content, flags=re.IGNORECASE)
        return content

    def create_draft(self, title: str, content: str, author: str = "",
                     thumb_media_id: str = "", digest: str = "",
                     content_base_dir: str = ".") -> Dict[str, Any]:
        """创建微信草稿"""
        content = self._remove_cover_image(content)
        content = self._upload_content_images(content, content_base_dir)
        content = self._fix_wechat_styles(content)

        # 字段截断
        def truncate(text, max_bytes):
            for i in range(len(text), 0, -1):
                if len(text[:i].encode('utf-8')) <= max_bytes:
                    return text[:i]
            return ""

        if len(title) > 64:
            title = title[:64]
            print(f"[微信] 标题已截断为: {title}")
        if author:
            author = truncate(author, 20)
        if not digest:
            digest = truncate(title, 54)
        else:
            digest = truncate(digest, 120)

        token = self.get_access_token()
        url = f"{self.BASE_URL}/draft/add?access_token={token}"

        article_data = {
            "title": title,
            "author": author,
            "digest": digest,
            "content": content,
            "content_source_url": "",
            "show_cover_pic": 1,
            "need_open_comment": 1,
            "only_fans_can_comment": 0
        }
        if thumb_media_id:
            article_data["thumb_media_id"] = thumb_media_id

        data = json.dumps({"articles": [article_data]}, ensure_ascii=False).encode('utf-8')
        headers = {'Content-Type': 'application/json; charset=utf-8'}
        resp = requests.post(url, data=data, headers=headers)
        result = resp.json()

        if 'errcode' in result and result['errcode'] != 0:
            if result['errcode'] in [40001, 42001]:
                token = self.get_access_token(force_refresh=True)
                url = f"{self.BASE_URL}/draft/add?access_token={token}"
                resp = requests.post(url, data=data, headers=headers)
                result = resp.json()
            if 'errcode' in result and result['errcode'] != 0:
                raise Exception(self._handle_error(result['errcode'], result.get('errmsg', ''), "创建草稿"))

        print(f"[微信] 草稿创建成功! media_id: {result.get('media_id')}")
        return result

    def publish(self, title: str, content: str, cover_path: str = "",
                author: str = "", digest: str = "") -> Dict[str, Any]:
        """完整发布流程：上传封面 + 创建草稿"""
        thumb_media_id = ""
        if cover_path and os.path.exists(cover_path):
            uploaded = self.upload_image(cover_path)
            thumb_media_id = uploaded if isinstance(uploaded, str) else uploaded[0]

        return self.create_draft(
            title=title,
            content=content,
            author=author,
            thumb_media_id=thumb_media_id,
            digest=digest,
            content_base_dir=os.path.dirname(os.path.abspath(cover_path)) if cover_path else "."
        )


def main():
    parser = argparse.ArgumentParser(description='微信公众号草稿发布工具')
    parser.add_argument('--setup', action='store_true', help='运行配置向导')
    parser.add_argument('-t', '--title', help='文章标题')
    parser.add_argument('-c', '--content', help='HTML内容文件路径')
    parser.add_argument('-a', '--author', default='', help='作者')
    parser.add_argument('--cover', default='', help='封面图路径')
    parser.add_argument('-d', '--digest', default='', help='摘要')

    args = parser.parse_args()

    try:
        if args.setup:
            WeChatPublisher().setup()
            return

        if not args.title or not args.content:
            parser.print_help()
            print("\n错误: 需要 --title 和 --content 参数，或使用 --setup 配置")
            sys.exit(1)

        with open(args.content, 'r', encoding='utf-8') as f:
            content = f.read()

        publisher = WeChatPublisher()
        publisher.publish(
            title=args.title,
            content=content,
            cover_path=args.cover,
            author=args.author,
            digest=args.digest
        )
        print(f"\n[微信] 发布成功! 请前往 mp.weixin.qq.com 草稿箱查看")
    except Exception as e:
        print(f"\n[微信] 错误: {e}")
        sys.exit(1)


if __name__ == '__main__':
    main()
