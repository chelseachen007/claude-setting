import json
def ld(p): return {x["SECURITY_CODE"]:x for x in json.load(open(p))}
bs=ld("bs_2026Q3.json"); cf=ld("cf_2026Q3.json")
for c,n in [("002466","天齐"),("002460","赣锋"),("002709","天赐"),("002812","恩捷"),("300750","宁德"),("603986","兆易"),("601869","长飞"),("603259","药明"),("601012","隆基")]:
    a=bs.get(c) or {}; f=cf.get(c) or {}
    t=a.get("TOTAL_ASSETS"); l=a.get("TOTAL_LIABILITIES")
    print(n,"资产负债率",round(l/t*100,1) if (l and t) else "n/a")
