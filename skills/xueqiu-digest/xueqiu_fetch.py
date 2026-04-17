#!/usr/bin/env python3
"""
雪球日报数据抓取脚本
抓取并预筛选雪球帖子，供 Claude skill 进一步处理

用法:
    python xueqiu_fetch.py                       # 使用默认配置
    python xueqiu_fetch.py --config path.json    # 指定配置文件
    python xueqiu_fetch.py --date 2026-04-16     # 指定日期
    python xueqiu_fetch.py --setup-cookies       # 引导设置 cookies
"""

import argparse
import json
import re
import sys
import time
from datetime import datetime, timedelta, timezone
from html import unescape
from pathlib import Path

try:
    import requests
except ImportError:
    print("请先安装依赖: pip install requests")
    sys.exit(1)

# === 默认路径 ===
SKILL_DIR = Path(__file__).parent
DEFAULT_CONFIG = SKILL_DIR / "config.json"
DEFAULT_OUTPUT = Path("/tmp/xueqiu_digest")

# === 评分关键词 ===
VALUATION_KW = [
    "PE", "PB", "PS", "DCF", "估值", "市值", "净利润", "营收",
    "毛利", "净利率", "目标价", "市盈率", "市净率", "ROE",
    "EPS", "股息率", "自由现金流",
]
INDUSTRY_KW = [
    "产能", "出货量", "良率", "客户", "订单", "供应链", "技术路线",
    "工艺", "产线", "量产", "爬坡", "渗透率", "市占率", "ASP",
    "进口替代", "国产化", "TAM", "SAM",
]
VIEWPOINT_KW = ["目标价", "看", "预计", "有望", "我认为", "预判", "判断", "观点", "看好", "看空"]
EMOTION_KW = [
    "暴涨", "暴跌", "暴富", "完了", "垃圾", "骗子", "起飞", "凉凉",
    "血亏", "傻逼", "牛b", "卧槽", "绝了", "疯了",
]
MACRO_KW = [
    "GDP", "CPI", "PPI", "PMI", "LPR", "MLF", "降息", "降准", "加息",
    "美联储", "央行", "财政", "货币", "社融", "M2", "汇率", "国债",
    "通缩", "通胀", "衰退", "复苏",
]

# === 板块股票池 ===
SECTOR_STOCKS = {
    "AI/算力": [
        "SZ300308",  # 中际旭创
        "SZ300502",  # 新易盛
        "SH688041",  # 海光信息
        "SZ300474",  # 景嘉微
        "SH603019",  # 中科曙光
        "SZ002049",  # 紫光国微
        "SZ002230",  # 科大讯飞
        "SH688787",  # 海天瑞声
    ],
    "光模块/CPO": [
        "SZ300308",  # 中际旭创
        "SZ300502",  # 新易盛
        "SZ002281",  # 光迅科技
        "SH603118",  # 共进股份
        "SZ300628",  # 亿联网络
    ],
    "半导体": [
        "SH688981",  # 中芯国际
        "SZ002371",  # 北方华创
        "SH688012",  # 中微公司
        "SZ300661",  # 圣邦股份
        "SH688256",  # 寒武纪
    ],
    "新能源车/锂电": [
        "SZ300750",  # 宁德时代
        "SZ002594",  # 比亚迪
        "SZ300014",  # 亿纬锂能
        "SZ002460",  # 赣锋锂业
        "SH688006",  # 杭可科技
    ],
    "光伏/储能": [
        "SH601012",  # 隆基绿能
        "SZ002459",  # 晶澳科技
        "SZ300274",  # 阳光电源
        "SH688599",  # 天合光能
    ],
    "创新药/CXO": [
        "SH603259",  # 药明康德
        "SZ300347",  # 泰格医药
        "SZ300760",  # 迈瑞医疗
        "SZ300122",  # 智飞生物
        "SH688180",  # 君实生物
        "SZ300003",  # 乐普医疗
        "SZ002007",  # 华兰生物
        "SH603127",  # 昭衍新药
    ],
    "医疗器械": [
        "SZ300760",  # 迈瑞医疗
        "SZ300832",  # 新产业
        "SH688317",  # 之江生物
        "SZ300861",  # 美迪西
    ],
}

# === 雪球 API ===
API = {
    "hot": "https://xueqiu.com/statuses/hot/listV2.json",
    "stock_timeline": "https://xueqiu.com/query/v1/symbol/search/status.json",
    "user_timeline": "https://xueqiu.com/statuses/original/show.json",
}


# ──────────────────────── 工具函数 ────────────────────────


def load_config(path: Path) -> dict:
    if not path.exists():
        print(f"配置文件不存在: {path}")
        print(f"请复制 config.example.json 为 config.json 并填写 cookies")
        sys.exit(1)
    with open(path, encoding="utf-8") as f:
        cfg = json.load(f)
    if not cfg.get("cookies"):
        print("请在 config.json 中填写 cookies")
        sys.exit(1)
    return cfg


def make_session(cookies_str: str) -> requests.Session:
    s = requests.Session()
    for item in cookies_str.split(";"):
        item = item.strip()
        if "=" in item:
            k, v = item.split("=", 1)
            s.cookies.set(k.strip(), v.strip(), domain=".xueqiu.com")
    s.headers.update(
        {
            "User-Agent": (
                "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/131.0.0.0 Safari/537.36"
            ),
            "X-Requested-With": "XMLHttpRequest",
            "Referer": "https://xueqiu.com/",
            "Origin": "https://xueqiu.com",
        }
    )
    return s


def clean_html(text: str) -> str:
    text = re.sub(r"<[^>]+>", "", text)
    text = unescape(text)
    text = re.sub(r"\s+", " ", text).strip()
    text = re.sub(r"来源：雪球App.*$", "", text)
    return text


def extract_stocks(text: str) -> list[str]:
    return list(set(re.findall(r"(SH|SZ)\d{6}", text)))


def tz_now():
    return datetime.now(timezone(timedelta(hours=8)))


# ──────────────────────── 抓取 ────────────────────────


def fetch_hot(session, size=30):
    print("  热门帖子...")
    try:
        r = session.get(API["hot"], params={"since_id": -1, "max_id": -1, "size": size}, timeout=15)
        data = r.json()
        items = data.get("items") or data.get("list") or []
        for p in items:
            p["_source"] = "hot"
        return items
    except Exception as e:
        print(f"    ⚠ {e}")
        return []


def fetch_stock(session, symbol, pages=2):
    print(f"  个股 {symbol}...")
    posts = []
    for page in range(1, pages + 1):
        try:
            r = session.get(
                API["stock_timeline"],
                params={"symbol": symbol, "count": 20, "comment": 0, "page": page},
                timeout=15,
            )
            data = r.json()
            items = data.get("list") or data.get("statuses") or []
            if not items:
                break
            for p in items:
                p["_source"] = f"stock:{symbol}"
            posts.extend(items)
            time.sleep(0.3)
        except Exception as e:
            print(f"    ⚠ {symbol} page {page}: {e}")
            break
    return posts


# ──────────────────────── 评分 ────────────────────────


def score_post(text: str) -> dict:
    s = {}
    length = len(text)

    # 1) 长度 (0-15)
    if length < 200:
        s["length"] = 0
    elif length < 500:
        s["length"] = 5
    elif length < 1000:
        s["length"] = 10
    elif length < 2000:
        s["length"] = 12
    else:
        s["length"] = 15

    # 2) 数据密度 (0-20)
    nums = re.findall(r"\d+\.?\d*", text)
    density = len(nums) / max(length / 100, 1)
    s["data_density"] = min(int(density * 5), 20)

    # 3) 结构 (0-15)
    struct = 0
    if re.search(r"[•\-]\s", text):
        struct += 3
    if re.search(r"\d+[\.、]\s", text):
        struct += 3
    if re.search(r"[：:]\s*$", text, re.MULTILINE):
        struct += 3
    if re.search(r"(首先|其次|最后|综上|因此|所以|结论|总计)", text):
        struct += 3
    if re.search(r"(假设|计算|推算|预计|估算|测算)", text):
        struct += 3
    s["structure"] = min(struct, 15)

    # 4) 估值模型 (0-15)
    s["valuation"] = min(sum(3 for kw in VALUATION_KW if kw.lower() in text.lower()), 15)

    # 5) 产业深度 (0-15)
    s["industry_depth"] = min(sum(3 for kw in INDUSTRY_KW if kw in text), 15)

    # 6) 明确观点 (0-10)
    vp = 0
    for p in VIEWPOINT_KW:
        if re.search(p, text):
            vp += 3
    s["viewpoint"] = min(vp, 10)

    # 7) 宏观分析加分 (0-10)
    macro = sum(2 for kw in MACRO_KW if kw in text)
    s["macro"] = min(macro, 10)

    # 8) 情绪惩罚 (0 to -10)
    emo = 0
    emo += len(re.findall(r"[！!]{2,}", text)) * 2
    emo += sum(2 for kw in EMOTION_KW if kw in text)
    emo += len(re.findall(r"[？?]{3,}", text))
    s["emotion_penalty"] = -min(emo, 10)

    total = sum(v for v in s.values())
    s["total"] = max(total, 0)
    return s


def classify_post(text: str, scores: dict) -> str:
    if scores.get("valuation", 0) >= 6 or scores.get("viewpoint", 0) >= 6:
        return "个股分析"
    if scores.get("macro", 0) >= 4:
        return "宏观政策"
    if any(kw in text for kw in ["板块", "赛道", "产业链", "上下游"]):
        return "行业分析"
    return "其他"


# ──────────────────────── 主流程 ────────────────────────


def parse_and_filter(posts, since_ms, min_len=300):
    seen = set()
    result = []
    for p in posts:
        pid = p.get("id")
        if pid and pid in seen:
            continue
        if pid:
            seen.add(pid)

        # 时间过滤
        created = p.get("created_at", 0)
        if created and created < since_ms:
            continue

        # 文本清洗
        text = clean_html(p.get("text", "") or p.get("title", "") or "")
        if len(text) < min_len:
            continue

        # 标题
        title = p.get("title", "") or ""
        if not title:
            title = text[:50].strip()
            if len(text) > 50:
                title += "..."

        # 作者
        user = p.get("user", {}) or {}
        username = user.get("screen_name", "") or p.get("user_name", "") or "匿名"
        user_id = str(user.get("id", "") or p.get("user_id", ""))

        url = f"https://xueqiu.com/{user_id}/{pid}" if pid and user_id else ""

        scores = score_post(text)
        category = classify_post(text, scores)

        result.append(
            {
                "id": str(pid),
                "title": title,
                "text": text,
                "author": username,
                "author_id": user_id,
                "url": url,
                "created_at": created,
                "created_at_str": (
                    datetime.fromtimestamp(created / 1000, tz=timezone(timedelta(hours=8))).strftime(
                        "%Y-%m-%d %H:%M"
                    )
                    if created
                    else ""
                ),
                "retweet_count": p.get("retweet_count", 0),
                "reply_count": p.get("reply_count", 0),
                "like_count": p.get("like_count", 0),
                "source": p.get("_source", ""),
                "stocks": extract_stocks(text),
                "category": category,
                "scores": scores,
            }
        )

    result.sort(key=lambda x: x["scores"]["total"], reverse=True)
    return result


def main():
    parser = argparse.ArgumentParser(description="雪球日报数据抓取")
    parser.add_argument("--config", default=str(DEFAULT_CONFIG))
    parser.add_argument("--date", help="YYYY-MM-DD，默认昨天")
    parser.add_argument("--output", default=str(DEFAULT_OUTPUT))
    parser.add_argument("--max", type=int, default=50, help="最大帖子数")
    args = parser.parse_args()

    config = load_config(Path(args.config))

    # 日期
    if args.date:
        target = datetime.strptime(args.date, "%Y-%m-%d")
    else:
        target = datetime.now() - timedelta(days=1)
    date_str = target.strftime("%Y-%m-%d")
    since_ms = int(target.replace(hour=0, minute=0, second=0).timestamp() * 1000)

    print(f"📅 抓取日期: {date_str}")

    out = Path(args.output)
    out.mkdir(parents=True, exist_ok=True)

    session = make_session(config["cookies"])

    # 抓取
    all_posts = []

    # 1) 热门帖子
    hot = fetch_hot(session, size=40)
    all_posts.extend(hot)
    time.sleep(0.5)

    # 2) 板块个股
    sectors = config.get("sectors", list(SECTOR_STOCKS.keys()))
    seen_symbols = set()
    for sector in sectors:
        symbols = SECTOR_STOCKS.get(sector, [])
        for sym in symbols:
            if sym in seen_symbols:
                continue
            seen_symbols.add(sym)
            posts = fetch_stock(session, sym, pages=2)
            all_posts.extend(posts)
            time.sleep(0.3)

    print(f"\n📊 共获取 {len(all_posts)} 条帖子")

    # 过滤 + 评分
    filtered = parse_and_filter(all_posts, since_ms, min_len=config.get("filters", {}).get("min_length", 300))
    print(f"📊 过滤后 {len(filtered)} 条")

    # 截断
    filtered = filtered[: args.max]

    # 保存
    out_file = out / f"posts_{date_str}.json"
    payload = {
        "date": date_str,
        "generated_at": tz_now().isoformat(),
        "total_fetched": len(all_posts),
        "total_filtered": len(filtered),
        "posts": filtered,
    }
    with open(out_file, "w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False, indent=2)

    print(f"\n✅ 已保存到 {out_file}")
    if filtered:
        print("📈 Top 5:")
        for p in filtered[:5]:
            print(f"  [{p['scores']['total']:3d}分] {p['title'][:40]}  — {p['author']}")

    return str(out_file)


if __name__ == "__main__":
    main()
