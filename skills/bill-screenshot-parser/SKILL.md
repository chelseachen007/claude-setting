---
name: bill-screenshot-parser
description: "触发词：账单截图、解析账单、支付宝截图、微信账单、导出Excel、交易记录、账单导入、CSV账单、支付宝交易明细、微信账单流水。当用户上传账单截图、CSV 或 XLSX 文件时触发。"
---

# 账单解析器

解析支付宝和微信账单（截图 / CSV / XLSX），提取交易信息并导出为 Excel 月度账单。

## 工作流

### Step 0: 安装依赖（首次使用）

```bash
pip3 install -r {baseDir}/requirements.txt --break-system-packages
```

### Step 1: 判断输入类型

根据用户上传的附件类型选择路径：

- **CSV / XLSX 文件** → 走「文件导入路径」（Step 2A）
- **截图图片** → 走「截图 OCR 路径」（Step 2B + Step 2C）

---

### 文件导入路径

#### Step 2A: 解析账单文件

```bash
python3 {baseDir}/scripts/parse_import_files.py \
  <文件路径1> <文件路径2> ... \
  --months <用户指定的月份，如 5,6>
```

脚本自动完成：
- 识别文件类型（支付宝 CSV / 微信 XLSX）
- 跳过文件头部元信息
- 支付宝 CSV 自动检测编码（GBK/UTF-8）
- 微信 XLSX 自动定位数据表头行
- 按月份过滤
- 按月分组输出 JSON

返回 JSON：
```json
{
  "total": 103,
  "months": {
    "2026-05": [{"date": "...", "type": "支出", "amount": 17.65, "description": "...", "platform": "支付宝", "category": "", "note": ""}, ...],
    "2026-06": [...]
  }
}
```

**月份参数**：
- 用户明确说了月份（如"5月和6月"）→ `--months 5,6`
- 用户没说月份 → 不传 `--months`，保留所有月份

---

### 截图 OCR 路径

#### Step 2B: 分割长截图

```bash
python3 {baseDir}/scripts/split_images.py <图片路径1> <图片路径2> ...
```

返回 JSON：
```json
{"images": [{"source": "...", "parts": ["part_00.png", ...], "height": 21368, "needs_split": true}]}
```

#### Step 2C: 启动子 Agent 执行 OCR

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

---

### Step 3: 按月写入 Excel

对 Step 2 输出的每个月份，分别调用处理脚本：

```bash
# 循环每个月
python3 {baseDir}/scripts/process_and_write.py \
  --data '<该月的JSON记录数组>' \
  --work-dir <工作目录> \
  --year <当前年份>
```

脚本自动完成：年份修正 → 过滤排除 → 双金额合并 → 类别推断 → 去重 → 排序 → 写入 Excel

返回统计 JSON：
```json
{"added": 45, "expense_total": 2200.38, "income_total": 500.00, "categories": {"饮食": 850.5, ...}, "bill_path": "..."}
```

### Step 4: 清理临时文件（仅截图路径需要）

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
6. 支付宝 CSV 编码为 GBK，脚本自动检测
7. 微信 XLSX 头部有元信息行，脚本自动跳过
