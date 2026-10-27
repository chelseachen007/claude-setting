#!/usr/bin/env python3
"""倒余额分析器 - 从 Buff 买入 + Steam 卖出数据计算折扣和收益"""

import json, csv, re, argparse, sys
from collections import defaultdict
from pathlib import Path

try:
    from openpyxl import Workbook
    from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
    from openpyxl.utils import get_column_letter
except ImportError:
    print("需要安装 openpyxl: pip3 install openpyxl")
    sys.exit(1)

STEAM_FEE_DEFAULT = 0.15  # Valve 5% + game 10%

# ============ Styles ============
HEADER_FONT = Font(bold=True, color="FFFFFF", size=11)
HEADER_FILL = PatternFill(start_color="4472C4", end_color="4472C4", fill_type="solid")
GREEN_FILL = PatternFill(start_color="E2EFDA", end_color="E2EFDA", fill_type="solid")
RED_FILL = PatternFill(start_color="FCE4EC", end_color="FCE4EC", fill_type="solid")
YELLOW_FILL = PatternFill(start_color="FFF2CC", end_color="FFF2CC", fill_type="solid")
SUMMARY_FONT = Font(bold=True, size=11)
THIN_BORDER = Border(
    left=Side(style='thin'), right=Side(style='thin'),
    top=Side(style='thin'), bottom=Side(style='thin')
)
MONEY_FMT = '¥#,##0.00'


def normalize_name(name):
    """归一化饰品名称用于匹配"""
    n = name.strip()
    n = re.sub(r'\s*\(.*?\)\s*$', '', n)      # English condition suffix
    n = re.sub(r'\s*（.*?）\s*$', '', n)       # Chinese condition suffix
    n = re.sub(r'\(StatTrak™\)\s*\|?\s*', '', n)
    n = re.sub(r'（StatTrak™）\s*\|?\s*', '', n)
    n = re.sub(r'\|\s*StatTrak™\s*', '', n)
    n = re.sub(r'（纪念品）\s*\|?\s*', '', n)
    n = re.sub(r'^铭刻\s+', '', n)
    n = re.sub(r'\s+', ' ', n).strip()
    return n


def parse_steam(json_path):
    """Parse Steam market history JSON"""
    with open(json_path, 'r') as f:
        data = json.load(f)

    html = data.get('results_html', '')
    rows = html.split('market_listing_row market_recent_listing_row')

    records = []
    for row in rows[1:]:
        gainarea = re.search(r'market_listing_gainorloss[^>]*>(.*?)</div>', row, re.DOTALL)
        gain = '?'
        if gainarea:
            t = gainarea.group(1).strip()
            if '+' in t: gain = '+'
            elif '-' in t: gain = '-'

        price_match = re.search(r'market_listing_price[^>]*>\s*([\w¥\$]+)\s*([\d,.]+)\s*', row)
        currency = price_match.group(1).strip() if price_match else '?'
        price = float(price_match.group(2).replace(',', '')) if price_match else 0

        name_span = re.search(r'<span[^>]*class="market_listing_item_name"[^>]*>(.*?)</span>', row, re.DOTALL)
        item = re.sub(r'<[^>]+>', '', name_span.group(1)).strip() if name_span else '?'

        game_match = re.search(r'market_listing_game_name[^>]*>([^<]+)<', row)
        game = game_match.group(1).strip() if game_match else '?'

        date_match = re.search(r'market_listing_listed_date[^>]*>\s*([^<]+)<', row)
        date = date_match.group(1).strip() if date_match else '?'

        records.append({
            'gain': gain, 'price': price, 'currency': currency,
            'item': item, 'game': game, 'date': date
        })
    return records


def parse_buff(csv_path):
    """Parse Buff buy history CSV (HYPERLINK format)"""
    records = []
    with open(csv_path, 'r') as f:
        content = f.read()

    lines = content.strip().split('\n')
    for line in lines[1:]:  # skip header
        game = line.split(',', 1)[0].strip()
        m = re.search(r',\s*""([^""]+?)""\s*\)', line)
        item_name = m.group(1) if m else '?'
        time_match = re.search(r'(\d{4}-\d{2}-\d{2}\s+\d{2}:\d{2}:\d{2})', line)
        price_match = re.search(r'¥\s*([\d,.]+)', line)
        time_str = time_match.group(1) if time_match else '?'
        price = float(price_match.group(1).replace(',', '')) if price_match else 0
        records.append({'game': game, 'item': item_name, 'time': time_str, 'price': price})
    return records


def match_records(buff_records, steam_records):
    """Match Buff buys with Steam sells by normalized item name.
    Note: Steam market history shows NET price (already after 15% fee)."""
    # Steam: "-" means sold (lost item)
    game_sells = [r for r in steam_records if r['gain'] == '-' and '集换式卡牌' not in r['game']]
    sells_idx = defaultdict(list)
    for r in game_sells:
        sells_idx[normalize_name(r['item'])].append(r)

    matched = []
    unmatched_buff = []
    used_ids = set()

    for r in buff_records:
        n = normalize_name(r['item'])
        if n in sells_idx and sells_idx[n]:
            s = sells_idx[n].pop(0)
            used_ids.add(id(s))
            steam_net = s['price']  # Steam 已扣除手续费，显示的就是到手净值
            discount_pct = (r['price'] / steam_net * 100) if steam_net > 0 else 0
            matched.append({
                'buff_item': r['item'],
                'steam_item': s['item'],
                'buff_price': r['price'],
                'steam_net': steam_net,
                'profit': steam_net - r['price'],
                'discount_pct': discount_pct,
                'buff_time': r['time'],
                'steam_date': s['date'],
                'game': r['game'],
            })
        else:
            unmatched_buff.append(r)

    steam_unmatched = []
    for n, items in sells_idx.items():
        for s in items:
            if id(s) not in used_ids and '集换式卡牌' not in s['game']:
                steam_unmatched.append(s)

    return matched, unmatched_buff, steam_unmatched


def style_header(ws, row, cols):
    for c in range(1, cols + 1):
        cell = ws.cell(row=row, column=c)
        cell.font = HEADER_FONT
        cell.fill = HEADER_FILL
        cell.alignment = Alignment(horizontal='center', vertical='center', wrap_text=True)
        cell.border = THIN_BORDER


def style_row(ws, row, cols, fill=None):
    for c in range(1, cols + 1):
        cell = ws.cell(row=row, column=c)
        cell.border = THIN_BORDER
        if fill:
            cell.fill = fill


def generate_excel(matched, unmatched_buff, steam_unmatched, steam_all, buff_all, output_path):
    """Generate the Excel report. Steam price is already net (fee deducted)."""
    wb = Workbook()

    # ===== Sheet 1: Matched details =====
    ws1 = wb.active
    ws1.title = "倒余额明细"
    headers = [
        "序号", "游戏", "饰品名称", "Buff 买入价", "Steam 到手净值",
        "差额(净值-买入)", "几折优惠", "Buff 日期", "Steam 日期"
    ]
    ws1.append(headers)
    style_header(ws1, 1, len(headers))

    total_buff = total_net = total_profit = 0

    for i, m in enumerate(sorted(matched, key=lambda x: x['buff_time']), 1):
        ws1.append([
            i, m['game'], m['buff_item'],
            m['buff_price'], m['steam_net'],
            m['profit'], m['discount_pct'] / 100,
            m['buff_time'][:10], m['steam_date']
        ])
        r = ws1.max_row
        for c in [4, 5, 6]:
            ws1.cell(row=r, column=c).number_format = MONEY_FMT
        ws1.cell(row=r, column=7).number_format = '0.0"折"'
        fill = GREEN_FILL if m['profit'] > 0 else RED_FILL
        style_row(ws1, r, len(headers), fill)

        total_buff += m['buff_price']
        total_net += m['steam_net']
        total_profit += m['profit']

    # Summary
    sr = ws1.max_row + 2
    ws1.cell(row=sr, column=3, value="合计").font = SUMMARY_FONT
    for col, val in [(4, total_buff), (5, total_net), (6, total_profit)]:
        ws1.cell(row=sr, column=col, value=val).number_format = MONEY_FMT
    avg_discount = (total_buff / total_net * 100) if total_net > 0 else 0
    ws1.cell(row=sr, column=7, value=avg_discount / 100).number_format = '0.0"折"'
    style_row(ws1, sr, len(headers), YELLOW_FILL)
    for c in range(3, len(headers) + 1):
        ws1.cell(row=sr, column=c).font = SUMMARY_FONT

    # KPI
    kr = sr + 2
    ws1.cell(row=kr, column=3, value="核心指标").font = Font(bold=True, size=13, color="4472C4")
    kpis = [
        ("总投入 (Buff)", total_buff),
        ("总到账 (Steam净值，已扣手续费)", total_net),
        ("净利润", total_profit),
        ("综合折扣", avg_discount / 100),
        ("每¥100真钱 → Steam余额", total_net / total_buff * 100 if total_buff else 0),
    ]
    for j, (label, val) in enumerate(kpis):
        ws1.cell(row=kr + 1 + j, column=3, value=label)
        cell = ws1.cell(row=kr + 1 + j, column=4, value=val)
        if label == "净利润":
            cell.number_format = MONEY_FMT
            cell.font = Font(bold=True, color="00B050" if val > 0 else "FF0000")
        elif label == "综合折扣":
            cell.number_format = '0.0"折"'
            cell.font = Font(bold=True, size=14, color="4472C4")
        elif "¥100" in label:
            cell.number_format = '¥"#,##0.0"'
        else:
            cell.number_format = MONEY_FMT

    for i, w in enumerate([5, 8, 35, 12, 14, 16, 10, 12, 12], 1):
        ws1.column_dimensions[get_column_letter(i)].width = w

    # ===== Sheet 2: Unmatched =====
    ws2 = wb.create_sheet("未匹配记录")
    ws2.append(["来源", "游戏", "饰品名称", "价格", "日期"])
    style_header(ws2, 1, 5)
    for r in unmatched_buff:
        ws2.append(["Buff买入", r['game'], r['item'], r['price'], r['time'][:10]])
        ws2.cell(row=ws2.max_row, column=4).number_format = MONEY_FMT
    for s in sorted(steam_unmatched, key=lambda x: -x['price']):
        ws2.append(["Steam卖出", s['game'], s['item'], s['price'], s['date']])
        ws2.cell(row=ws2.max_row, column=4).number_format = MONEY_FMT
    for i, w in enumerate([10, 10, 35, 12, 12], 1):
        ws2.column_dimensions[get_column_letter(i)].width = w

    # ===== Sheet 3: All Steam =====
    ws3 = wb.create_sheet("Steam全部记录")
    ws3.append(["序号", "类型", "游戏", "饰品名称", "价格", "日期"])
    style_header(ws3, 1, 6)
    for i, r in enumerate(steam_all, 1):
        type_str = "卖出(-)" if r['gain'] == '-' else "买入(+)" if r['gain'] == '+' else '?'
        ws3.append([i, type_str, r['game'], r['item'], r['price'], r['date']])
        ws3.cell(row=ws3.max_row, column=5).number_format = MONEY_FMT
        fill = GREEN_FILL if r['gain'] == '-' else RED_FILL
        style_row(ws3, ws3.max_row, 6, fill)
    for i, w in enumerate([5, 8, 20, 35, 12, 12], 1):
        ws3.column_dimensions[get_column_letter(i)].width = w

    # ===== Sheet 4: All Buff =====
    ws4 = wb.create_sheet("Buff全部记录")
    ws4.append(["序号", "游戏", "饰品名称", "买入价", "日期"])
    style_header(ws4, 1, 5)
    for i, r in enumerate(sorted(buff_all, key=lambda x: x['time']), 1):
        ws4.append([i, r['game'], r['item'], r['price'], r['time'][:10]])
        ws4.cell(row=ws4.max_row, column=4).number_format = MONEY_FMT
    for i, w in enumerate([5, 8, 40, 12, 12], 1):
        ws4.column_dimensions[get_column_letter(i)].width = w

    wb.save(output_path)
    return total_buff, total_net, total_profit, avg_discount


def main():
    parser = argparse.ArgumentParser(description='倒余额分析器')
    parser.add_argument('--steam-json', required=True, help='Steam 市场历史 JSON')
    parser.add_argument('--buff-csv', required=True, help='Buff 买入记录 CSV')
    parser.add_argument('--output', default=str(Path.home() / 'Downloads/倒余额分析报告.xlsx'), help='输出 Excel 路径')
    args = parser.parse_args()

    print("📥 解析 Steam 数据...")
    steam_records = parse_steam(args.steam_json)
    sold = [r for r in steam_records if r['gain'] == '-']
    print(f"  总记录: {len(steam_records)}, 卖出: {len(sold)}")

    print("📥 解析 Buff 数据...")
    buff_records = parse_buff(args.buff_csv)
    print(f"  买入记录: {len(buff_records)}")

    print("🔄 匹配中...")
    matched, unmatched_buff, steam_unmatched = match_records(buff_records, steam_records)
    print(f"  匹配: {len(matched)}/{len(buff_records)}")

    print("📊 生成 Excel...")
    total_buff, total_net, total_profit, avg_discount = generate_excel(
        matched, unmatched_buff, steam_unmatched,
        steam_records, buff_records, args.output
    )

    print(f"\n{'═' * 50}")
    print(f"  ✅ 报告已保存: {args.output}")
    print(f"  综合折扣: {avg_discount:.1f}折")
    print(f"  总投入: ¥{total_buff:.2f}")
    print(f"  总到账: ¥{total_net:.2f}")
    print(f"  净利润: ¥{total_profit:+.2f}")
    print(f"  每¥100 → ¥{total_net/total_buff*100:.1f} Steam余额")
    print(f"{'═' * 50}")


if __name__ == '__main__':
    main()
