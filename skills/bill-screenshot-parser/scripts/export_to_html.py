#!/usr/bin/env python3
"""
账单截图解析 - HTML 导出脚本（带图片分类）

将账单数据导出为带图片预览的 HTML 文件，按月份分文件夹
"""

import argparse
import json
import os
import sys
import base64
import shutil
from datetime import datetime
from collections import defaultdict

try:
    from openpyxl import load_workbook
    from openpyxl.drawing.image import Image as XLImage
except ImportError:
    pass  # Excel 功能可选


# 类型映射
TYPE_MAP = {
    "expense": "支出",
    "income": "收入",
}

# 平台映射
PLATFORM_MAP = {
    "alipay": "支付宝",
    "wechat": "微信",
}

# 类别颜色
CATEGORY_COLORS = {
    "餐饮": "#FFE4E1",
    "交通": "#E0FFFF",
    "购物": "#FFF0F5",
    "娱乐": "#F0FFF0",
    "医疗": "#FFFACD",
    "教育": "#E6E6FA",
    "公益": "#F5F5DC",
    "通讯": "#E0FFFF",
    "订阅": "#FFE4B5",
    "转账": "#D3D3D3",
    "生活": "#98FB98",
    "其他": "#FFFFFF",
}


def get_month_key(date_str):
    """从日期字符串提取月份键"""
    try:
        for fmt in ["%Y-%m-%d %H:%M:%S", "%Y-%m-%d", "%Y/%m/%d %H:%M:%S", "%Y/%m/%d"]:
            try:
                dt = datetime.strptime(date_str[:19], fmt)
                return dt.strftime("%Y-%m")
            except ValueError:
                continue
        if len(date_str) >= 7:
            return date_str[:7]
    except:
        pass
    return "未知月份"


def get_month_display(month_key):
    """获取月份显示名称"""
    try:
        if month_key and "-" in month_key:
            year, month = month_key.split("-")
            return f"{year}年{int(month)}月"
    except:
        pass
    return month_key


def get_category_color(category):
    """获取类别对应的背景色"""
    return CATEGORY_COLORS.get(category, "#FFFFFF")


def image_to_base64(image_path):
    """将图片转换为 base64 编码"""
    try:
        with open(image_path, "rb") as f:
            data = f.read()
        ext = os.path.splitext(image_path)[1].lower()
        mime_type = "image/png" if ext == ".png" else "image/jpeg"
        return f"data:{mime_type};base64,{base64.b64encode(data).decode()}"
    except:
        return ""


def generate_html(month_key, records, image_map=None, output_dir=None):
    """
    生成单月的 HTML 表格

    Args:
        month_key: 月份键，如 "2026-02"
        records: 该月的记录列表
        image_map: 记录描述到图片路径的映射
        output_dir: 输出目录

    Returns:
        HTML 文件路径
    """
    month_display = get_month_display(month_key)

    # 创建月份目录
    month_dir = os.path.join(output_dir, month_key)
    os.makedirs(month_dir, exist_ok=True)

    # 复制图片到月份目录
    local_image_map = {}
    if image_map:
        images_dir = os.path.join(month_dir, "images")
        os.makedirs(images_dir, exist_ok=True)
        for desc, img_path in image_map.items():
            if os.path.exists(img_path):
                img_name = os.path.basename(img_path)
                dest_path = os.path.join(images_dir, img_name)
                if not os.path.exists(dest_path):
                    shutil.copy2(img_path, dest_path)
                local_image_map[desc] = f"images/{img_name}"

    # 计算汇总
    total_expense = sum(r.get("amount", 0) for r in records if r.get("type") == "expense")
    total_income = sum(r.get("amount", 0) for r in records if r.get("type") == "income")
    net = total_expense - total_income

    # 生成 HTML
    html = f'''<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{month_display} 账单</title>
    <style>
        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }}
        body {{
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif;
            background: #f5f5f5;
            padding: 20px;
        }}
        .container {{
            max-width: 1200px;
            margin: 0 auto;
        }}
        h1 {{
            text-align: center;
            color: #333;
            margin-bottom: 20px;
        }}
        .summary {{
            display: flex;
            justify-content: center;
            gap: 40px;
            margin-bottom: 20px;
            padding: 15px;
            background: white;
            border-radius: 8px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }}
        .summary-item {{
            text-align: center;
        }}
        .summary-label {{
            font-size: 14px;
            color: #666;
        }}
        .summary-value {{
            font-size: 24px;
            font-weight: bold;
            margin-top: 5px;
        }}
        .expense {{ color: #e74c3c; }}
        .income {{ color: #27ae60; }}
        table {{
            width: 100%;
            border-collapse: collapse;
            background: white;
            border-radius: 8px;
            overflow: hidden;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }}
        th {{
            background: #3498db;
            color: white;
            padding: 12px 8px;
            text-align: left;
            font-weight: 500;
        }}
        td {{
            padding: 10px 8px;
            border-bottom: 1px solid #eee;
            vertical-align: middle;
        }}
        tr:hover {{
            background: #f8f9fa;
        }}
        .type-expense {{ color: #e74c3c; }}
        .type-income {{ color: #27ae60; }}
        .amount {{
            font-weight: bold;
            text-align: right;
        }}
        .category {{
            padding: 4px 8px;
            border-radius: 4px;
            font-size: 12px;
        }}
        .img-cell {{
            width: 60px;
            text-align: center;
        }}
        .img-cell img {{
            max-width: 50px;
            max-height: 50px;
            border-radius: 4px;
            cursor: pointer;
        }}
        .img-cell img:hover {{
            transform: scale(2);
            position: relative;
            z-index: 10;
        }}
        .no-img {{
            width: 50px;
            height: 50px;
            background: #f0f0f0;
            border-radius: 4px;
            display: flex;
            align-items: center;
            justify-content: center;
            color: #999;
            font-size: 10px;
        }}
        .note {{
            color: #666;
            font-size: 12px;
        }}
    </style>
</head>
<body>
    <div class="container">
        <h1>{month_display} 账单明细</h1>
        <div class="summary">
            <div class="summary-item">
                <div class="summary-label">本月合计</div>
                <div class="summary-value expense">-{net:.2f}</div>
            </div>
            <div class="summary-item">
                <div class="summary-label">支出</div>
                <div class="summary-value expense">{total_expense:.2f}</div>
            </div>
            <div class="summary-item">
                <div class="summary-label">收入</div>
                <div class="summary-value income">{total_income:.2f}</div>
            </div>
            <div class="summary-item">
                <div class="summary-label">记录数</div>
                <div class="summary-value" style="color: #333;">{len(records)}</div>
            </div>
        </div>
        <table>
            <thead>
                <tr>
                    <th style="width:60px;">图片</th>
                    <th style="width:160px;">日期</th>
                    <th style="width:60px;">类型</th>
                    <th style="width:100px;">金额</th>
                    <th style="width:80px;">类别</th>
                    <th>描述</th>
                    <th style="width:80px;">平台</th>
                    <th style="width:100px;">备注</th>
                </tr>
            </thead>
            <tbody>
'''

    # 添加记录行
    for r in records:
        date = r.get("date", "")
        type_str = TYPE_MAP.get(r.get("type", ""), r.get("type", ""))
        amount = r.get("amount", 0)
        category = r.get("category", "其他")
        description = r.get("description", "")
        platform = PLATFORM_MAP.get(r.get("platform", ""), r.get("platform", ""))
        note = r.get("note", "")

        type_class = "type-expense" if r.get("type") == "expense" else "type-income"
        amount_prefix = "-" if r.get("type") == "expense" else "+"
        bg_color = get_category_color(category)

        # 图片
        img_html = '<div class="no-img">无图</div>'
        if local_image_map and description in local_image_map:
            img_path = local_image_map[description]
            img_html = f'<img src="{img_path}" alt="{description}">'

        note_html = f'<span class="note">{note}</span>' if note else ""

        html += f'''                <tr>
                    <td class="img-cell">{img_html}</td>
                    <td>{date}</td>
                    <td class="{type_class}">{type_str}</td>
                    <td class="amount {type_class}">{amount_prefix}{amount:.2f}</td>
                    <td><span class="category" style="background:{bg_color}">{category}</span></td>
                    <td>{description}</td>
                    <td>{platform}</td>
                    <td>{note_html}</td>
                </tr>
'''

    html += '''            </tbody>
        </table>
    </div>
</body>
</html>'''

    # 写入文件
    html_path = os.path.join(month_dir, f"{month_key}_账单.html")
    with open(html_path, "w", encoding="utf-8") as f:
        f.write(html)

    return html_path


def export_to_html(data_list, output_dir, image_map=None):
    """
    导出数据到 HTML（按月份分文件夹）

    Args:
        data_list: 数据列表
        output_path: 输出目录
        image_map: 记录描述到图片路径的映射
    """
    if not data_list:
        print("没有数据需要导出")
        return False

    # 创建输出目录
    os.makedirs(output_dir, exist_ok=True)

    # 按月份分组
    monthly_data = defaultdict(list)
    for data in data_list:
        month_key = get_month_key(data.get("date", ""))
        monthly_data[month_key].append(data)

    # 按月份排序（倒序）
    sorted_months = sorted(monthly_data.keys(), reverse=True)

    html_files = []
    for month_key in sorted_months:
        records = monthly_data[month_key]
        html_path = generate_html(month_key, records, image_map, output_dir)
        html_files.append(html_path)
        print(f"生成: {html_path} ({len(records)} 条记录)")

    # 生成索引页
    index_path = os.path.join(output_dir, "index.html")
    index_html = '''<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <title>账单索引</title>
    <style>
        body { font-family: sans-serif; padding: 40px; background: #f5f5f5; }
        h1 { color: #333; margin-bottom: 20px; }
        .month-list { display: flex; flex-direction: column; gap: 10px; }
        .month-item {
            background: white;
            padding: 15px 20px;
            border-radius: 8px;
            text-decoration: none;
            color: #333;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
            transition: transform 0.2s;
        }
        .month-item:hover { transform: translateX(10px); }
        .month-name { font-size: 18px; font-weight: bold; }
        .month-count { color: #666; font-size: 14px; margin-top: 5px; }
    </style>
</head>
<body>
    <h1>账单目录</h1>
    <div class="month-list">
'''
    for month_key in sorted_months:
        month_display = get_month_display(month_key)
        count = len(monthly_data[month_key])
        index_html += f'''        <a class="month-item" href="{month_key}/{month_key}_账单.html">
            <div class="month-name">{month_display}</div>
            <div class="month-count">{count} 条记录</div>
        </a>
'''
    index_html += '''    </div>
</body>
</html>'''

    with open(index_path, "w", encoding="utf-8") as f:
        f.write(index_html)

    print(f"\n导出完成: {output_dir}")
    print(f"  月份: {len(sorted_months)} 个")
    print(f"  索引: {index_path}")

    return True


def main():
    parser = argparse.ArgumentParser(description="导出账单数据到 HTML（带图片分类，按月份分文件夹）")
    parser.add_argument("--data", required=True, help="JSON 格式的账单数据")
    parser.add_argument("--output", required=True, help="输出目录")
    parser.add_argument("--images", help="图片目录（包含分割后的账单图片）")

    args = parser.parse_args()

    try:
        data_list = json.loads(args.data)
        if not isinstance(data_list, list):
            data_list = [data_list]
    except json.JSONDecodeError as e:
        print(f"JSON 解析错误: {e}")
        sys.exit(1)

    # 构建图片映射
    image_map = None
    if args.images and os.path.isdir(args.images):
        image_map = {}
        for f in os.listdir(args.images):
            if f.endswith((".png", ".jpg", ".jpeg")):
                image_map[f] = os.path.join(args.images, f)

    export_to_html(data_list, args.output, image_map)


if __name__ == "__main__":
    main()
