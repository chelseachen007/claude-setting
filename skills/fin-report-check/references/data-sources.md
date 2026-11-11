# 数据源查询方法

依据 `投资研究/README.md` 的分层，这里沉淀**一手源的具体查询方法**和**聚合源的已知陷阱**。

## 数据源分层

| 层级 | 用途 | 源 | 可信度 |
|------|------|-----|--------|
| 一手源 | 核对关键数字（净利/分红/营收/披露日期） | 巨潮资讯、上交所/深交所、港交所披露易 | 唯一最终依据 |
| 聚合源 | 快速定位、交叉比对 | 雪球、AASTOCKS、同花顺、东方财富 | 可能滞后/错漏 |
| 观点源 | 逻辑参考 | 雪球讨论帖、券商研报 | 不是数据源 |

## 巨潮资讯（A 股一手源）

**判断某类公告是否已披露**（最常用）：

```bash
curl -s 'https://www.cninfo.com.cn/new/hisAnnouncement/query' \
  --data-urlencode 'pageNum=1' \
  --data-urlencode 'pageSize=30' \
  --data-urlencode 'column=szse' \
  --data-urlencode 'tabName=fulltext' \
  --data-urlencode 'plate=' \
  --data-urlencode 'stock=600690,gssh0600690' \
  --data-urlencode 'searchkey=' \
  --data-urlencode 'secid=' \
  --data-urlencode 'category=category_bndbg_szsh' \
  --data-urlencode 'trade=' \
  --data-urlencode 'seDate=2026-01-01~2026-08-14' \
  --data-urlencode 'sortName=' \
  --data-urlencode 'sortType=' \
  --data-urlencode 'isHLtitle=true'
```

- `stock`：`股票代码,orgId`。orgId 格式沪市 `gssh0600690`、深市 `gsz0000000`。
- `category`：`category_ndbg_szsh`=年度报告，`category_bndbg_szsh`=半年度报告，`category_yjdbg_szsh`=季度报告。留空查全部。
- `seDate`：披露日期区间 `YYYY-MM-DD~YYYY-MM-DD`。
- 返回 JSON，`announcements` 数组；为空 = 该期间未披露该类公告。

**陷阱**：
- 必须用 **https**，http 会 mixed-content 拦截（「Failed to fetch」）。
- 个股页 URL `.../disclosure/stock?stockCode=600690` 缺 `orgId` 返回「页面不存在」。
- `new/information/topSearch/query` 接口返回 HTML 不是 JSON，不能用。

## AASTOCKS（港股聚合源，确认披露日期用）

**新闻 URL 模式**：`https://www.aastocks.com/sc/cnhk/quote/stock-news-content/{6位代码}/now.{newsID}/aafn`

- 新闻正文完整转述公告数据（收入、纯利、同比、派息），并带精确披露时间戳 `YYYY/MM/DD HH:MM CST`。
- **标题不写年份**——「中期纯利 120.33 亿增 15.6%」可能是任何一年的。必须看正文时间戳确认。这是最常见的翻车点。

## 港交所披露易（H 股一手源）

- 主站 `www1.hkexnews.hk`，标题搜索是 JSF 表单（`search/titlesearch.xhtml`）。
- **陷阱**：`searchStockCode` 用 JS 赋值 + dispatch 事件，自动补全不出现；点击「搜尋」后结果常为空。表单自动化成功率低、耗时高。
- 要核 H 股公告，优先用 AASTOCKS 新闻原文（能确认披露日期），或直接搜索公告标题。

## 雪球（实时估值）

- 实时估值（股价/PE/PB/股息率/市值）从雪球个股页 DOM `innerText` 读，SSR 已渲染，无需登录。
- quote API `stock.xueqiu.com/v5/stock/quote.json` 会返回 400016（需登录），不要用。
- 估值是**快照**，超一个季度未更新视为待核对。
