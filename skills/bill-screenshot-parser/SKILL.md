---
name: bill-screenshot-parser
description: "触发词：账单截图、解析账单、支付宝截图、微信账单、导出Excel、交易记录。当用户上传支付截图或要求解析账单时触发。"
---

# 账单截图解析器

解析支付宝和微信账单截图，提取交易信息并导出为 Excel 文件。

## 工作流

### Step 0: 安装依赖（首次使用）

```bash
pip3 install -r {baseDir}/requirements.txt --break-system-packages
```

### Step 1: 分割长截图

```bash
python3 {baseDir}/scripts/split_images.py <图片路径1> <图片路径2> ...
```

返回 JSON：
```json
{"images": [{"source": "...", "parts": ["part_00.png", ...], "height": 21368, "needs_split": true}]}
```

### Step 2: 启动子 Agent 执行 OCR

启动 **1 个 general-purpose 子 agent**，将 OCR 任务委托给它。

**子 agent prompt 构造**：
1. 读取 `{baseDir}/references/ocr-prompt.md` 获取完整指令模板
2. 替换模板中的 `{year}` 为当前年份，`{platform}` 为平台名（支付宝/微信）
3. 传入所有图片 parts 路径列表
4. 子 agent 对每个 part 执行：Read 获取 CDN URL → analyze_image 识别
5. 子 agent 返回 JSON 交易记录数组

**关键点**：
- 必须先用 Read 工具获取 CDN URL，再调用 analyze_image（直接传本地路径会报错）
- 顺序处理，不并行（避免 API 429 限速）
- 如果用户上传了多张不同平台的截图，按平台分组后分别启动子 agent

### Step 3: 写入 Excel

合并子 agent 返回的 JSON 结果，调用处理脚本：

```bash
python3 {baseDir}/scripts/process_and_write.py \
  --data '<合并后的JSON数组>' \
  --work-dir <工作目录> \
  --year <当前年份>
```

脚本自动完成：年份修正 → 过滤排除 → 双金额合并 → 类别推断 → 去重 → 排序 → 写入 Excel

返回统计 JSON：
```json
{"added": 45, "expense_total": 2200.38, "income_total": 500.00, "categories": {"饮食": 850.5, ...}, "bill_path": "..."}
```

### Step 4: 清理临时文件

```bash
python3 {baseDir}/scripts/split_images.py --clean
```

## Excel 模板

模板文件：`{baseDir}/template.xlsx`

| Sheet | 说明 |
|-------|------|
| 明细 | A-G 列：日期、类型、金额、类别、描述、平台、备注 |
| 汇总 | SUMIFS 按类别统计，覆盖 1000 行 |

## 16 个标准类别

饮食、食材、住房、咖啡、通讯、服饰、交通、彩妆、社交、医疗、学习、娱乐、健身、日用、旅行、其他

## 过滤规则（自动排除）

- 余额宝收益、基金分红、理财
- 花呗还款
- 系统消息（"您于..."、"商户单号"等）
- 社交类金额 >= 5000

## 注意事项

1. 长截图（>2000px）必须分割，否则 OCR 会出现重复数据
2. 金额 `-` 表示支出，`+` 表示收入
3. 日期格式统一为 YYYY-MM-DD HH:mm:ss
4. 自动按 (date, amount, description) 去重
5. 支付宝双金额（消费+退款）自动合并为一条记录
