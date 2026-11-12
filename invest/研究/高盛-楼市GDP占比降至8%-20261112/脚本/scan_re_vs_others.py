"""扫描全市场：地产链 vs 非地产，2026Q3 累计营收/净利同比分布。
口径：东财 fin 接口 RPT_LICO_FN_CPD，2026-09-30 累计（三季报）。
"""
import json, statistics as st
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
FIN = ROOT / "数据" / "fin-2026Q3.json"

# 东财行业分类里与地产链直接相关的 BOARD_NAME（按名称匹配，容忍“Ⅱ”后缀）
CHAIN_KEYWORDS = ["房地产", "装修建材", "水泥", "玻璃玻纤", "工程机械", "工程建设",
                  "家电", "家居", "厨卫电器", "钢铁", "有色", "煤炭", "银行", "保险"]

def is_chain(b):
    return any(k in b for k in CHAIN_KEYWORDS)

def pct(xs, q):
    xs = sorted(xs)
    if not xs: return None
    i = min(len(xs) - 1, max(0, int(round(q * (len(xs) - 1)))))
    return xs[i]

rows = json.load(open(FIN))
def agg(sel):
    rev = [r["YSTZ"] for r in sel if isinstance(r.get("YSTZ"), (int, float))]
    prof = [r["SJLTZ"] for r in sel if isinstance(r.get("SJLTZ"), (int, float))]
    # 用净利加权口径：Σ净利同比（按归母净利加权）
    wp = [(r["SJLTZ"], r["PARENT_NETPROFIT"]) for r in sel
          if isinstance(r.get("SJLTZ"), (int, float)) and isinstance(r.get("PARENT_NETPROFIT"), (int, float))
          and r["PARENT_NETPROFIT"] > 0]
    tot = sum(w for _, w in wp) or 1
    wavg = sum(v * w for v, w in wp) / tot
    return {
        "n": len(sel),
        "revenue_median": round(st.median(rev), 1) if rev else None,
        "revenue_lt0": round(100 * sum(1 for v in rev if v < 0) / len(rev), 1) if rev else None,
        "profit_median": round(st.median(prof), 1) if prof else None,
        "profit_lt0": round(100 * sum(1 for v in prof if v < 0) / len(prof), 1) if prof else None,
        "profit_weighted": round(wavg, 1),
        "profit_p10": round(pct(prof, 0.10), 1) if prof else None,
        "profit_p90": round(pct(prof, 0.90), 1) if prof else None,
    }

chain = [r for r in rows if is_chain(r.get("BOARD_NAME") or "")]
others = [r for r in rows if not is_chain(r.get("BOARD_NAME") or "")]

by_board = {}
for r in rows:
    b = r.get("BOARD_NAME") or "未知"
    by_board.setdefault(b, []).append(r)

focus = ["房地产开发", "房地产服务", "装修建材", "水泥", "玻璃玻纤", "家电行业",
         "工程建设", "工程机械", "银行", "煤炭行业", "钢铁行业"]
out = {"总体": {"地产链": agg(chain), "非地产链": agg(others)}}
for b in focus:
    cand = [r for r in rows if (r.get("BOARD_NAME") or "").startswith(b)]
    if cand:
        out[b] = agg(cand)

out_path = ROOT / "数据" / "scan-re-vs-others-2026Q3.json"
json.dump(out, open(out_path, "w"), ensure_ascii=False, indent=2)
print(json.dumps(out, ensure_ascii=False, indent=2))
