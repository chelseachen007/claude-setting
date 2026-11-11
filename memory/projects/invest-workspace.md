---
summary: "投资工作区（~/WorkBuddy AI/投资）的规则、接口坑与口径纪律"
read_when:
  - 抓东方财富/腾讯行情数据
  - 写投资研究笔记或复盘
---

# 投资工作区

唯一规则源：`~/WorkBuddy AI/投资/AGENTS.md`（新建目录前先读它）。

## 结构

```
研究/<主题>-<YYYYMMDD>/{研究.md, 方法.md, 数据/, 脚本/}
工具/{抓数/, 数据湖/, 策略/}
知识库/ 配置/ data/（约 2GB 数据湖） .tmp/ .archive/
```

硬规则：
- 一个研究一个目录，不按 md 文件名搜
- 脚本进 `工具/` 必须过「用过两次」门槛，且必须路径无关（`Path(__file__).resolve().parent`，禁止依赖 cwd——kelly 5 个脚本曾因此全挂）
- 数据快照跨天不覆盖

## 数据抓取

统一走 `工具/抓数/fetch_eastmoney.py`（quote / board / flow / fin / cashflow / balance 子命令），库内函数 `fin_period` / `cashflow` / `balance`。别再写一次性脚本。

东方财富接口坑：
- 必须 `urllib.request.ProxyHandler({})` 绕过本机 `http_proxy`，否则全部超时/502
- `f43`（价）/ `f162`（静态 PE）/ `f167`（PB）返回 ×100 整数，要 /100
- `RPT_LICO_FN_CPD` 的 columns 写 `NOTICE_DATE` / `DEDUCT_PARENT_NETPROFIT` / `OPERATE_INCOME` 会报 `code 9501 返回字段参数不存在`
- `RPT_DMSK_FN_CASHFLOW` / `RPT_DMSK_FN_BALANCE` 的 filter 要用 `REPORT_DATE='YYYY-MM-DD 00:00:00'`（不是 REPORTDATE），且必须先给 columns
- `searchapi.10jqka.com.cn` DNS 不通，别用
- 腾讯行情 `web.ifzq.gtimg.cn` 可用，A 股交易纪律技能走它

细节文档：`投资/知识库/东方财富接口备忘.md`

## 口径纪律

- PE 必须写明是 PE25A 还是 PE(TTM)
- 板块涨跌用东财自算时要标「自算口径」
- 复盘机制：研究后 1~3 个月回补「当时判断 / 实际结果 / 错在哪」
