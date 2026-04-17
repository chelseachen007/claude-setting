#!/usr/bin/env python3
"""
雪球帖子确定性评分脚本
读取浏览器端抓取的 JSON，对帖子进行多维度评分，输出带分数的 JSON

用法:
    python3 xueqiu_score.py                           # 评分今天的文件
    python3 xueqiu_score.py --input /tmp/xueqiu_digest/posts_2026-04-16.json
    python3 xueqiu_score.py --date 2026-04-16
"""

import argparse
import json
import re
import sys
from datetime import datetime, timedelta
from pathlib import Path

# === 默认路径 ===
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


def extract_stocks(text: str) -> list[str]:
    return list(set(re.findall(r"(SH|SZ)\d{6}", text)))


def score_file(input_path: Path, output_path: Path | None = None, top_n: int = 50) -> str:
    with open(input_path, encoding="utf-8") as f:
        data = json.load(f)

    posts = data.get("posts", [])
    print(f"📊 读入 {len(posts)} 条帖子")

    for p in posts:
        text = p.get("text", "")
        scores = score_post(text)
        p["scores"] = scores
        p["category"] = classify_post(text, scores)
        p["stocks"] = extract_stocks(text)

    posts.sort(key=lambda x: x["scores"]["total"], reverse=True)
    posts = posts[:top_n]

    data["posts"] = posts
    data["total_scored"] = len(posts)

    out = output_path or input_path
    with open(out, "w", encoding="utf-8") as f:        json.dump(data, f, ensure_ascii=False, indent=2)

    print(f"✅ 已保存 {len(posts)} 条评分结果到 {out}")
    if posts:
        print("📈 Top 5:")
        for p in posts[:5]:
            print(f"  [{p['scores']['total']:3d}分] {p['title'][:40]}  — {p.get('author', '?')}")

    return str(out)


def main():
    parser = argparse.ArgumentParser(description="雪球帖子确定性评分")
    parser.add_argument("--input", help="输入 JSON 路径")
    parser.add_argument("--output", help="输出 JSON 路径（默认覆盖输入）")
    parser.add_argument("--date", help="YYYY-MM-DD")
    parser.add_argument("--top", type=int, default=50, help="保留 Top N 帖子")
    args = parser.parse_args()

    if args.input:
        in_path = Path(args.input)
    elif args.date:
        in_path = DEFAULT_OUTPUT / f"posts_{args.date}.json"
    else:
        date_str = (datetime.now() - timedelta(days=1)).strftime("%Y-%m-%d")
        in_path = DEFAULT_OUTPUT / f"posts_{date_str}.json"

    if not in_path.exists():
        print(f"文件不存在: {in_path}")
        sys.exit(1)

    out_path = Path(args.output) if args.output else None
    score_file(in_path, out_path, args.top)


if __name__ == "__main__":
    main()
