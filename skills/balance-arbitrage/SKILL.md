---
name: balance-arbitrage
description: "触发词：倒余额、余额分析、Steam余额、Buff倒卖、折扣分析、余额比例。从 Buff 买入 + Steam 卖出数据中计算倒余额的折扣、损耗和总收益。"
---

# 倒余额分析器

从 Buff（买入）和 Steam（卖出）市场记录中，自动匹配同一饰品，计算倒余额的折扣率、手续费损耗和净利润。输出 Excel 报告。

## 工作流

### Step 1: 获取数据

需要用户提供两份数据来源：

#### Steam 市场历史

从浏览器 DevTools 复制 Steam `market/myhistory` 的 curl 请求。脚本用该请求获取全部市场记录。

关键判断：
- Steam 市场历史中，`-` 表示**卖出**（失去物品），`+` 表示**买入**（获得物品）
- **Steam 显示的价格已经是扣完手续费的到手净值**，不要再扣一次 15%

#### Buff 买入记录

**方式 A（推荐）**: 从 Buff 网站复制导出 API 的 curl 请求（`/account/api/export/bill_order`），脚本触发导出后下载 CSV。

**方式 B**: 用户直接上传 Buff 导出的 CSV 文件。

### Step 2: 安装依赖

```bash
pip3 install openpyxl --break-system-packages 2>/dev/null || pip3 install openpyxl
```

### Step 3: 解析和匹配

运行分析脚本：

```bash
python3 {baseDir}/scripts/analyze.py \
  --steam-json <steam_history.json> \
  --buff-csv <buff_buy.csv> \
  --output <output.xlsx>
```

参数说明：
- `--steam-json`: Steam 市场历史 JSON（从 curl 保存）
- `--buff-csv`: Buff 买入记录 CSV
- `--output`: 输出 Excel 路径（默认 `~/Downloads/倒余额分析报告.xlsx`）

**注意**: Steam 市场 API 返回的价格是扣除手续费后的到手净值（Valve 5% + 游戏 10% 已扣），脚本不再重复扣除。

### Step 4: 匹配逻辑

1. **名称归一化**：去除品质/磨损后缀（括号内容）、StatTrak™、纪念品、铭刻 前缀
2. **按归一化名称匹配**：同一名称的 Buff 买入和 Steam 卖出配对
3. **计算公式**（Steam 价格已含手续费扣除，为到手净值）：
   - 几折优惠 = Buff 买入价 / Steam 到手净值 × 10（如 75.6% → 75.6折）
   - 差额 = Steam 到手净值 - Buff 买入价
   - 转换效率 = Steam 到手净值 / Buff 买入价 × 100%

### Step 5: 输出 Excel 报告

包含 4 个 Sheet：

1. **倒余额明细**：逐笔对比 + 核心指标（综合折扣、总投入、总到账、净利润）
2. **未匹配记录**：Buff 买了但 Steam 无对应 / Steam 卖了但 Buff 无对应
3. **Steam 全部记录**：所有市场交易，绿色=卖出，红色=买入
4. **Buff 全部记录**：所有买入记录

### Step 6: 报告结果

输出核心指标摘要：
- 综合折扣（X折）
- 总投入 / 总到账 / 净利润
- 每 ¥100 真钱 → 多少 Steam 余额

## 注意事项

- **Steam 市场 API 返回的价格是扣除手续费后的净值**，不要重复扣除（Valve 5% + 游戏 10% 已在 API 价格中体现）
- 集换式卡牌不计入倒余额分析（单独统计）
- Cookie 有时效性，过期后需要用户重新获取
- 如果匹配率低，提示用户检查是否有未导出的记录
