import json
from pathlib import Path
HERE = Path(__file__).resolve().parent
, urllib.request, sys

UA = {"User-Agent": "Mozilla/5.0"}

def get(url):
    req = urllib.request.Request(url, headers=UA)
    # 明确绕过代理：本机配了 http_proxy
    opener = urllib.request.build_opener(urllib.request.ProxyHandler({}))
    return opener.open(req, timeout=30).read()

def kline(sym, period="day", n=1200, adj="qfq"):
    url = f"https://web.ifzq.gtimg.cn/appstock/app/fqkline/get?param={sym},{period},,,{n},{adj}"
    d = json.loads(get(url))
    k = d["data"][sym]
    key = f"qfq{period}" if f"qfq{period}" in k else period
    return k[key]

def spot(sym):
    raw = get(f"http://qt.gtimg.cn/q={sym}").decode("gbk")
    body = raw.split('"')[1]
    f = body.split("~")
    return f

if __name__ == "__main__":
    out = {}
    for sym, label in [("sh600690","海尔智家"), ("sh000905","中证500")]:
        out[label] = {"sym": sym, "day": kline(sym, "day", 1200), "week": kline(sym, "week", 800)}
        out[label]["spot"] = spot(sym)
    json.dump(out, open(HERE/"raw.json","w"), ensure_ascii=False)
    for k,v in out.items():
        print(k, "day", len(v["day"]), v["day"][0][0], "→", v["day"][-1][0], "| week", len(v["week"]), v["week"][0][0])
