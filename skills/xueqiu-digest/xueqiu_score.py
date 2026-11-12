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

# 股票名称→代码映射（用于从投资日记提取关注个股）
STOCK_NAME_MAP = {
    "海尔智家": "SH600690", "中国神华": "SH601088", "长江电力": "SH600900",
    "贵州茅台": "SH600519", "招商银行": "SH600036", "中国平安": "SH601318",
    "宁德时代": "SZ300750", "比亚迪": "SZ002594", "中际旭创": "SZ300308",
    "新易盛": "SZ300502", "海光信息": "SH688041", "恒瑞医药": "SH600276",
    "迈瑞医疗": "SZ300760", "中芯国际": "SH688981", "赣锋锂业": "SZ002460",
    "牧原股份": "SZ002714", "中远海控": "SH601919", "大秦铁路": "SH601006",
    "工商银行": "SH601398", "建设银行": "SH601939", "中国移动": "SH600941",
    "兖矿能源": "SH600188", "宝钢股份": "SH600019", "江苏银行": "SH600919",
    "农业银行": "SH601288", "中国银行": "SH601988", "中石化": "SH600028",
    "中海油": "SH600938", "中石油": "SH601857", "派能科技": "SZ300014",
    "固德威": "SZ300274", "胜宏科技": "SZ300476", "沪电股份": "SZ002463",
    "深南电路": "SZ002916", "君实生物": "SH688180", "药明康德": "SH603259",
}


def parse_journal_stocks(journal_path: str) -> set[str]:
    """从投资日记中提取关注的个股代码"""
    codes = set()
    p = Path(journal_path)
    if not p.exists():
        return codes
    content = p.read_text(encoding="utf-8")

    # 提取 SH/SZ 代码
    codes.update(re.findall(r"(?:SH|SZ)\d{6}", content))

    # 提取已知股票名称
    for name, code in STOCK_NAME_MAP.items():
        if name in content:
            codes.add(code)

    # 提取 [[...]] 链接中的股票名
    links = re.findall(r"\[\[(.+?)\]\]", content)
    for link in links:
        link_name = link.split("|")[0].strip()
        if link_name in STOCK_NAME_MAP:
            codes.add(STOCK_NAME_MAP[link_name])

    return codes


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
    return list(set(re.findall(r"(?:SH|SZ)\d{6}", text)))


# ── 日报「三问」的原料：关注池 + 触发器命中 ────────────────────

# 关注池用名称匹配而非代码：帖子正文通常只写公司名
FOCUS_POOL = {
    "SH600690": "海尔智家",
    "SH600900": "长江电力",
    "SZ002460": "赣锋锂业",
}

# 关注 ETF（2026-11-05 新增）：这些标的的讨论很少出现完整代码，匹配词组比名称更可靠
# 与 xueqiu_browser_fetch.js 的 FOCUS_ETFS 保持一致；行情在 JSON 的 etf_quotes 里
FOCUS_ETFS = {
    "SH513180": {"name": "恒生科技ETF华夏", "label": "港股科技",
                 "kw": ["恒生科技ETF", "恒生科技", "恒科ETF", "513180"]},
    "SH561550": {"name": "中证500增强ETF华泰柏瑞", "label": "500增强",
                 "kw": ["中证500增强", "500增强", "指增", "561550"]},
}
# ETF 讨论单独成区，不进 Top N 竞争；短于这个长度的没法分析
MIN_ETF_POST_LEN = 200
MAX_ETF_POSTS = 12

# 触发器关键词 → 编号，与 投资/素材/触发器清单.md 的 T1..T7 一一对应
# 只收窄到「能指认方向」的组合词：单写 CPI/PPI 会让几乎每篇宏观贴都命中，失去信号意义
TRIGGER_KW = {
    "T1": ["核心CPI", "核心 CPI"],
    "T2": ["社零", "社会消费品零售", "零售总额"],
    "T3": ["M1增速", "M1同比", "M1-M2"],
    "T4": ["剪刀差"],
    "T5": ["反内卷", "限产", "减产", "停产整顿", "关停"],
    "T6": ["产能出清", "行业出清", "退出产能", "落后产能"],
    "T7": ["碳酸锂", "锂价", "锂矿"],
}


def scan_three_questions(posts: list[dict], daily_dir: Path, today: str) -> dict:
    """扫描**全部**帖子（含被筛掉的），回答日报三问所需的事实。

    只看 Top 50 会漏掉低位帖子里的关注股提及——这正是过去「0 命中」误判的来源之一。
    """
    focus = {code: {"name": name, "count": 0, "sample": ""} for code, name in FOCUS_POOL.items()}
    etf_focus = {
        code: {"name": v["name"], "label": v["label"], "count": 0, "sample": ""}
        for code, v in FOCUS_ETFS.items()
    }
    triggers = {tid: {"count": 0, "sample": ""} for tid in TRIGGER_KW}

    for p in posts:
        text = f"{p.get('title', '')}\n{p.get('text', '')}"
        upper = text.upper()
        for code, name in FOCUS_POOL.items():
            if name in text or code in text:
                focus[code]["count"] += 1
                if not focus[code]["sample"]:
                    focus[code]["sample"] = (p.get("title") or "")[:40]
        for code, v in FOCUS_ETFS.items():
            # 命中条件：抓取侧打了 etf_hits 标记，或正文提到关键词
            hit = code in (p.get("etf_hits") or []) or any(k in text for k in v["kw"])
            if hit:
                etf_focus[code]["count"] += 1
                if not etf_focus[code]["sample"]:
                    etf_focus[code]["sample"] = (p.get("title") or "")[:40]
        for tid, kws in TRIGGER_KW.items():
            if any(kw.upper() in upper for kw in kws):
                triggers[tid]["count"] += 1
                if not triggers[tid]["sample"]:
                    triggers[tid]["sample"] = (p.get("title") or "")[:40]

    # 连续 0 命中天数：回看历史日报
    streak = {code: 0 for code in FOCUS_POOL}
    for f in sorted(daily_dir.glob("*.md"), reverse=True):
        if f.stem >= today:
            continue
        try:
            content = f.read_text(encoding="utf-8")
        except Exception:
            continue
        frozen = True
        for code, name in FOCUS_POOL.items():
            if streak[code] != len([x for x in []]) and content.count(name) > 3:
                frozen = False
        if not frozen:
            break
        for code, name in FOCUS_POOL.items():
            if content.count(name) <= 3:
                streak[code] += 1

    return {"focus": focus, "etf_focus": etf_focus, "triggers": triggers, "streak": streak}


def score_file(input_path: Path, output_path: Path | None = None, top_n: int = 50, journal_path: str = "",
               daily_dir: Path | None = None) -> str:
    with open(input_path, encoding="utf-8") as f:
        data = json.load(f)

    posts = data.get("posts", [])
    all_posts = posts            # 截断前保留全量引用，供下面挑 ETF 帖
    print(f"📊 读入 {len(posts)} 条帖子")

    # 提取自选股代码
    watchlist = data.get("watchlist", [])
    watchlist_codes = set(w.get("symbol", "") for w in watchlist if w.get("symbol"))

    # 提取投资日记关注个股
    journal_codes = parse_journal_stocks(journal_path) if journal_path else set()
    all_focus = watchlist_codes | journal_codes

    if watchlist_codes:
        print(f"👀 自选股 {len(watchlist_codes)} 只: {', '.join(sorted(watchlist_codes)[:8])}...")
    if journal_codes:
        print(f"📓 日记关注 {len(journal_codes)} 只: {', '.join(sorted(journal_codes)[:8])}...")

    for p in posts:
        text = p.get("text", "")
        scores = score_post(text)

        # 自选股/日记关注加分 (0-10)
        post_stocks = set(extract_stocks(text))
        overlap = post_stocks & all_focus
        scores["watchlist_bonus"] = min(len(overlap) * 5, 10) if overlap else 0

        # 日记关注标记
        p["journal_focus"] = bool(post_stocks & journal_codes)

        # 关注 ETF 标记：命中就进日报「关注 ETF」区，不被 Top N 截断
        p["etf_hits"] = sorted(set(p.get("etf_hits") or []) |
                               {v["label"] for c, v in FOCUS_ETFS.items()
                                if c in text or any(k in text for k in v["kw"])})

        # 重算总分
        scores["total"] = max(sum(v for k, v in scores.items() if k != "total"), 0)

        p["scores"] = scores
        p["category"] = classify_post(text, scores)
        p["stocks"] = list(post_stocks)

    # 三问原料必须在截断前扫描全量帖子
    three_q = scan_three_questions(posts, daily_dir or Path.cwd(), input_path.stem.replace("posts_", ""))
    all_count = len(posts)

    posts.sort(key=lambda x: x["scores"]["total"], reverse=True)
    posts = posts[:top_n]

    # 关注 ETF 的讨论不参与 Top N 竞争，单独保一份（只留能进日报的长度）
    etf_posts = [
        p for p in all_posts
        if p.get("etf_hits") and len(p.get("text") or "") >= MIN_ETF_POST_LEN
    ][:MAX_ETF_POSTS]

    data["posts"] = posts
    data["total_scored"] = len(posts)
    data["total_input"] = all_count
    data["watchlist_codes"] = sorted(watchlist_codes)
    data["journal_codes"] = sorted(journal_codes)
    data["three_questions"] = three_q
    data["etf_posts"] = etf_posts
    data["etf_posts_count"] = len(etf_posts)

    # 默认写回独立文件，避免覆盖原始全量数据（覆盖后三问只能看到 Top N）
    out = output_path or input_path.with_name(input_path.stem + "_scored.json")
    with open(out, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

    journal_posts = [p for p in posts if p.get("journal_focus")]
    print(f"✅ 已评分 {all_count} 条，保留 Top {len(posts)}，写入 {out}")
    if all_count <= top_n:
        print(f"⚠️  输入仅 {all_count} 条，无法判断是否有帖子被历史截断；三问可能漏检")

    # ── 日报三问 ────────────────────────────────────────────
    print()
    print("═" * 46)
    print("今日三问")
    print("═" * 46)
    focus = three_q["focus"]
    streak = three_q["streak"]
    hit = [f"{v['name']} {v['count']}篇" for v in focus.values() if v["count"] > 0]
    print(f"1. 关注池异动：{('、'.join(hit)) if hit else '全部 0 命中'}")
    for code, v in focus.items():
        if v["count"] == 0:
            print(f"     · {v['name']} 已连续 {streak.get(code, 0)} 天 0 命中")

    fired = [f"{tid} {v['count']}篇" for tid, v in three_q["triggers"].items() if v["count"] > 0]
    print(f"2. 触发器命中：{('、'.join(fired)) if fired else '无'}")
    for tid, v in three_q["triggers"].items():
        if v["count"] > 0 and v["sample"]:
            print(f"     · {tid} 例：{v['sample']}")

    print("3. 动作判定：看上面两问，无命中就不动；有命中按 投资/素材/触发器清单.md 判定")
    print("═" * 46)

    # ── 关注 ETF ────────────────────────────────────────────
    print()
    print("═" * 46)
    print("关注 ETF")
    print("═" * 46)
    for q in data.get("etf_quotes") or []:
        tag = f"{q.get('label', '?'):<4} {q.get('name', '')} ({q.get('symbol', '')})"
        if not q.get("ok"):
            print(f"  {tag}  行情缺失")
            continue
        pct = q.get("percent")
        pct_s = f"{pct:+.2f}%" if isinstance(pct, (int, float)) else "   n/a"
        print(f"  {tag}  {q.get('current')}  {pct_s}")
    ef = three_q["etf_focus"]
    for code, v in ef.items():
        print(f"  · {v['label']} 讨论 {v['count']} 篇" + (f"，例：{v['sample']}" if v["sample"] else ""))
    print(f"  · 收入日报的 ETF 帖 {data.get('etf_posts_count', 0)} 篇（正文 ≥{MIN_ETF_POST_LEN} 字）")
    print("═" * 46)

    if journal_posts:
        print(f"📓 其中 {len(journal_posts)} 条涉及投资日记关注个股")
    if posts:
        print("📈 Top 5:")
        for p in posts[:5]:
            j_mark = " 📓" if p.get("journal_focus") else ""
            print(f"  [{p['scores']['total']:3d}分{j_mark}] {p['title'][:40]}  — {p.get('author', '?')}")

    return str(out)


def main():
    parser = argparse.ArgumentParser(description="雪球帖子确定性评分")
    parser.add_argument("--input", help="输入 JSON 路径")
    parser.add_argument("--output", help="输出 JSON 路径（默认覆盖输入）")
    parser.add_argument("--date", help="YYYY-MM-DD")
    parser.add_argument("--top", type=int, default=50, help="保留 Top N 帖子")
    parser.add_argument("--journal", default="",
                        help="投资日记文件路径（用于提取关注个股）")
    parser.add_argument("--daily-dir", default="/Users/chenjie/ai/invest/素材/雪球日报",
                        help="历史日报目录（用于计算关注池连续 0 命中天数）；2026-11-12 起日报迁到投资工作区")
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
    score_file(in_path, out_path, args.top, args.journal, Path(args.daily_dir))


if __name__ == "__main__":
    main()
