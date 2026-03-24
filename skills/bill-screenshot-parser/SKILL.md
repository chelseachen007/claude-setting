---
name: bill-screenshot-parser
description: "触发词：账单截图、解析账单、支付宝截图、微信账单、导出Excel、交易记录。当用户上传支付截图或要求解析账单时触发。"
---

# 账单截图解析器

解析支付宝和微信账单截图，提取交易信息并导出为 Excel 文件。

## 核心流程

### 1. 查找或创建当月账单文件

每次解析时，自动检查当前工作目录是否存在当月账单文件：

```python
from datetime import datetime
import os
import shutil

def get_or_create_monthly_bill(work_dir):
    """获取或创建当月账单文件"""
    today = datetime.now()
    month_name = f"{today.year}年{today.month}月账单.xlsx"
    bill_path = os.path.join(work_dir, month_name)

    if os.path.exists(bill_path):
        return bill_path, 'append'  # 追加模式
    else:
        # 从模板创建新文件
        template_path = '/Users/chenjie/.claude/skills/bill-screenshot-parser/template.xlsx'
        shutil.copy(template_path, bill_path)
        return bill_path, 'create'  # 新建模式
```

### 2. 接收截图

用户上传一张或多张支付宝/微信账单截图。

### 3. 长截图分割处理

**重要**：如果截图高度超过 2000 像素，必须先分割再识别，否则会出现重复数据问题。

```python
from PIL import Image
import os

def split_long_screenshot(image_path, output_dir='/tmp/bill_parts', part_height=2000):
    """分割长截图"""
    os.makedirs(output_dir, exist_ok=True)
    img = Image.open(image_path)
    width, height = img.size

    if height <= part_height:
        return [image_path]  # 不需要分割

    num_parts = (height + part_height - 1) // part_height
    parts = []

    for i in range(num_parts):
        top = i * part_height
        bottom = min((i + 1) * part_height, height)
        part = img.crop((0, top, width, bottom))
        part_path = f'{output_dir}/part_{i:02d}.png'
        part.save(part_path)
        parts.append(part_path)

    return parts
```

### 4. 解析截图

使用 Read 工具将图片上传到 CDN，然后使用 analyze_image MCP 工具解析。

**注意**：直接使用 analyze_image 可能报错 "图片输入格式/解析错误"，必须先用 Read 工具获取 CDN URL。

对每个分割后的图片部分调用 analyze_image，提取交易记录。

**支付宝字段：**
- 交易时间
- 交易类型（支出/收入）
- 金额
- 商品/商户名称

**微信字段：**
- 交易时间
- 交易类型（支出/收入）
- 金额
- 商品/商户名称

### 5. 数据标准化

将提取的数据统一为以下格式：

```json
{
  "date": "2026-02-27 12:30:00",
  "type": "支出",
  "amount": 25.50,
  "category": "饮食",
  "description": "美团外卖-黄焖鸡米饭",
  "platform": "支付宝",
  "note": ""
}
```

### 6. 类别推断

根据商品/商户名称自动推断类别（共 16 个类别）：

```python
CATEGORIES = ['饮食', '食材', '住房', '咖啡', '通讯', '服饰', '交通', '彩妆', '社交', '医疗', '学习', '娱乐', '健身', '日用', '旅行', '其他']

def infer_category(description):
    """根据描述推断类别"""
    desc = str(description)

    if any(kw in desc for kw in ['外卖', '餐厅', '美团', '饿了么', '肯德基', '麦当劳', '面馆', '海底捞', '快餐', '美食', '饮料', '零食', '小吃', '餐饮', '嵊州']):
        return '饮食'
    elif any(kw in desc for kw in ['盒马', '超市', '菜场', '生鲜', '菜市场']):
        return '食材'
    elif any(kw in desc for kw in ['房租', '物业', '水电', '燃气', '宽带', '水费', '电费']):
        return '住房'
    elif any(kw in desc for kw in ['咖啡', 'Coffee', '星巴克', '瑞幸', 'Manner']):
        return '咖啡'
    elif any(kw in desc for kw in ['话费', '充值', '移动', '联通', '电信', '通讯']):
        return '通讯'
    elif any(kw in desc for kw in ['服装', '衣服', '鞋', 'ZARA', '优衣库']):
        return '服饰'
    elif any(kw in desc for kw in ['打车', '滴滴', '地铁', '公交', '加油', '停车', '高德', '充电', '出行', '中石化', '石化', '交通', '交通出行']):
        return '交通'
    elif any(kw in desc for kw in ['化妆品', '口红', '粉底', '护肤', '美容', '屈臣氏', '丝芙兰']):
        return '彩妆'
    elif any(kw in desc for kw in ['红包', '转账', '请客', '聚餐', '礼物']):
        return '社交'
    elif any(kw in desc for kw in ['医院', '药店', '诊所', '体检', '挂号', '药品']):
        return '医疗'
    elif any(kw in desc for kw in ['课程', '书籍', '培训', '知乎', '教育', '网课', '订阅']):
        return '学习'
    elif any(kw in desc for kw in ['电影', '游戏', '音乐', '视频', '爱奇艺', '腾讯视频', 'B站', 'BUFF', 'steam', '腾讯天游', '娱乐']):
        return '娱乐'
    elif any(kw in desc for kw in ['健身', '运动', '瑜伽', '游泳', '体育馆']):
        return '健身'
    elif any(kw in desc for kw in ['便利', '购', '日用', '洗护', '纸巾', '京东', '拼多多', '淘宝']):
        return '日用'
    elif any(kw in desc for kw in ['机票', '酒店', '旅游', '景点', '民宿', '火车票']):
        return '旅行'
    elif any(kw in desc for kw in ['公益', '捐赠']):
        return '其他'
    else:
        return '其他'
```

### 7. 追加数据到 Excel

使用 openpyxl 将新数据追加到现有账单文件：

```python
from openpyxl import load_workbook
from datetime import datetime

def append_to_bill(bill_path, records):
    """追加记录到账单文件"""
    wb = load_workbook(bill_path)
    ws = wb['明细']

    # 找到最后一行
    last_row = ws.max_row

    # 去重：读取已有记录
    existing_keys = set()
    for row in range(2, last_row + 1):
        date = ws.cell(row=row, column=1).value
        amount = ws.cell(row=row, column=3).value
        desc = ws.cell(row=row, column=5).value
        if date and amount:
            existing_keys.add((str(date), float(amount), str(desc)))

    # 追加新记录（去重）
    added = 0
    for r in records:
        key = (r['date'], r['amount'], r['description'])
        if key not in existing_keys:
            last_row += 1
            ws.cell(row=last_row, column=1, value=r['date'])
            ws.cell(row=last_row, column=2, value=r['type'])
            ws.cell(row=last_row, column=3, value=r['amount'])
            ws.cell(row=last_row, column=4, value=r['category'])
            ws.cell(row=last_row, column=5, value=r['description'])
            ws.cell(row=last_row, column=6, value=r['platform'])
            ws.cell(row=last_row, column=7, value=r.get('note', ''))
            added += 1

    wb.save(bill_path)
    return added
```

## 过滤规则

导出时**默认排除**以下类型的交易：

| 排除类型 | 关键词 |
|---------|-------|
| 理财收益 | 余额宝、收益发放、基金分红、理财、余额宝收益 |
| 系统消息 | 您于、使用"先、商户单号 |
| 大额转账 | 社交类金额 ≥ 5000 |

## Excel 模板结构

模板文件位于：`/Users/chenjie/.claude/skills/bill-screenshot-parser/template.xlsx`

### Sheet 1: 明细
| 列 | 字段 | 说明 |
|---|------|------|
| A | 日期 | YYYY-MM-DD HH:mm:ss |
| B | 类型 | 下拉框：支出/收入 |
| C | 金额 | 数字 |
| D | 类别 | 下拉框：16个标准类别 |
| E | 描述 | 商品/商户名称 |
| F | 平台 | 支付宝/微信 |
| G | 备注 | 其他说明 |

### Sheet 2: 汇总
- 按类别统计支出（使用 SUMIFS 公式）
- 支出合计、收入合计、净支出
- 公式自动覆盖 1000 行数据范围

## 使用示例

**解析截图：**
```
帮我解析这张支付宝截图
```

**多张截图：**
```
帮我解析这些账单截图
```

## 注意事项

1. **长截图处理**：高度超过 2000px 的截图必须分割，否则会出现重复数据
2. **图片上传**：先用 Read 工具获取 CDN URL，再调用 analyze_image
3. **金额识别**：注意区分「-」表示支出，「+」表示收入
4. **日期格式**：统一为 YYYY-MM-DD HH:mm:ss
5. **平台识别**：支付宝截图通常有蓝色主题，微信有绿色主题
6. **自动去重**：追加数据时自动跳过已存在的记录
7. **API 限流**：如遇到 429 错误，稍后重试
