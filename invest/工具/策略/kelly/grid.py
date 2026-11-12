"""静态凯利速查表：按 胜率p × 盈亏比b 算 f* 与 半凯利"""
rows=[]
for p in [0.30,0.35,0.40,0.45,0.50,0.55,0.60,0.65,0.70,0.80]:
    r=[]
    for b in [0.5,1,1.5,2,3,4]:
        f=(p*(b+1)-1)/b
        r.append(f)
    rows.append((p,r))
print("p\\b", [0.5,1,1.5,2,3,4])
for p,r in rows:
    print(f"{p:.2f}", [round(x*100,1) for x in r])
