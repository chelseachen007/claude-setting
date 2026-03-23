# 金融日报生成器 — cn-finance-daily

A 股 + 美股 + 大宗商品日报自动生成工具。智能缓存低频宏观数据（每月更新），实时获取高频市场数据，输出 Obsidian 格式日报并自动保存。

## 核心设计

### 数据分类策略

| 数据类型 | 更新频率 | 缓存策略 |
|----------|----------|----------|
| [[LPR]] 贷款市场报价利率 | **月度** | 缓存 **30天** |
| [[CPI]] 居民消费价格指数 | **月度** | 缓存 **30天** |
| [[PPI]] 工业生产者出厂价格 | **月度** | 缓存 **30天** |
| [[PMI]] 采购经理指数 | **月度** | 缓存 **30天** |
| 外汇储备 + 黄金储备 | **月度** | 缓存 **30天** |
| A股指数（实时行情） | **日度** | **每次必取** |
| 美股指数 + 大宗商品 | **日度**（美盘后） | **每次必取** |
| 北向资金（沪深港通） | **日度** | **每次必取** |

## 使用方法

```
/cn-finance-daily
```

或直接说：
- "生成今天的金融市场日报"
- "写投资日报"
- "更新投资日报"

## 命令行用法

从技能目录运行：

```bash
# 获取所有数据（智能缓存）
python scripts/fetch_data.py --all

# 只获取高频市场数据（跳过缓存）
python scripts/fetch_data.py --market

# 强制刷新宏观数据
python scripts/fetch_data.py --macro

# 显示缓存状态
python scripts/fetch_data.py --cache-show

# 清除所有缓存
python scripts/fetch_data.py --cache-clear

# 生成日报（自动保存到 Obsidian）
python scripts/generate_report.py

# 预览日报（不保存）
python scripts/generate_report.py --dry-run

# 指定日期生成
python scripts/generate_report.py --date 2026-03-20
```

## 数据源

| 数据 | 来源 | 备注 |
|------|------|------|
| A股指数历史 | AKShare (Sina) | |
| 北向资金 | AKShare (东方财富) | |
| 宏观数据 | AKShare | |
| 美股 + 金属 | **Stooq**（优先）/ Yahoo Finance（备用） | Stooq 更稳定，不限流 |
| 黄金 ETF 持仓 | AKShare (宏观消费) | 缓存30天 |
| 上海金交所金价 | AKShare (SGE) | 缓存30天 |

## 输出格式

日报保存到：`洞察报告/投资日报/YYYY/YYYY-MM/YYYY-MM-DD.md`

包含六大板块：
1. **A 股市场** — 主要指数收盘价、涨跌幅、趋势
2. **美股** — S&P 500、Dow Jones、Nasdaq 等
3. **大宗商品** — 黄金、白银、铜、铂金、钯金
4. **北向资金** — 沪深港通净流向
5. **宏观数据** — LPR/CPI/PPI/PMI（标注是否缓存）
6. **综合点评** — 市场情绪判断、关键观察点

## 故障排除

- **Stooq 无数据**：改用 Yahoo Finance ETF 代理（SPY, GLD 等）
- **AKShare 限流**：切换东方财富数据源或等待
- **yfinance 限流**：Stooq 是主要备选
- **SGE 黄金无数据**：使用 Stooq gc.f 期货数据
- **宏观数据缺失**：使用缓存数据 + 标注"数据截至XXX"

## 目录结构

```
cn-finance-toolkit-reporter/
├── SKILL.md                    # 本文档
├── requirements.txt             # 依赖
└── scripts/
    ├── fetch_data.py           # 数据获取器（含缓存逻辑）
    ├── generate_report.py      # 日报生成器
    └── cache.json             # 宏观数据缓存
```
