---
summary: "投资工作区（~/ai/invest）的规则、接口坑与口径纪律"
read_when:
  - 抓东方财富/腾讯行情数据
  - 写投资研究笔记或复盘
---

# 投资工作区

唯一规则源：`~/ai/invest/AGENTS.md`（新建目录前先读它）。

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

## 数据湖运维（2026-11-12 重建，详见 `投资/知识库/数据湖运维手册.md`）

cnequity 0.18.0，`data/cnequity` 是数据湖，只能通过 `cne` CLI 操作。

- 三个 LaunchAgent：`com.cnequity.lake-serve`（看板 8787）、`com.cnequity.web.706c3d40b7beb570`（内置调度器，15:30 日更 / 18:00 stale 检查）、`com.user.lake-watchdog`（工作日 15:10 判断今天抓到没，没抓到弹通知）
- 调度器 label 的 16 位 = `sha256(meta_root.resolve())[:16]`，换目录就变
- 体检一条命令：`bash 工具/数据湖/lake_health.sh`（服务 / 调度器心跳 / 数据到哪天+欠账 / 看门狗）
- **手动跑 cne 一律用 `.venv/bin/python3 工具/数据湖/cne_clean.py <args>`**：httpx 0.28.1 解析 `NO_PROXY` 里的 `[::1]` 会抛 `Invalid port: ':1]'`，这个包装脚本会删掉所有代理变量（本机所有源直连都通），并把 `public-api.baostock.com` 换成真实 IP（Clash fake-ip 198.18.x.x 让裸 socket 连不上）
- 补历史按交易日逐天：`cne run daily --trade-date <d> --group core`。**别直接 `cne run daily` 补历史**：signals 组的 dragon_tiger/block_trades 会从 2007 年逐日重扫（6 年/小时），锁被占 6-7 小时，其他组全拒
- 卡住的任务：`POST /api/ops/jobs/<id>/cancel` 返回 202 但无效，**用 `kill -TERM`**（SIGINT 要 11s 且未必退）
- 看板 API 提交任务字段只有 `preview_id` + `launch_token`，多传 422
- A 股当日 K 线 15:05 前拒绝写入，中午跑必然缺当日行情
- `push2.eastmoney.com` 在代理出口被上游断开；熔断一次（strikes_needed=1）就关一整天，期间单票补数掉到 baostock 兜底，而 baostock 被连接重置（`10002007 网络接收错误`），白天补不上
- `coverage_status=incomplete` 长期存在是欠账误报：停牌/退市票（688121.SH、301139.SZ）+ 新股（920085.BJ）+ 北交所快照不可用那天个别票。`missing_ranges` 里的 `bj_price_limit` 是 `staged_contracts.py:38` 把科创板票当北交所校验的 bug
- 5 个 STALE（commodity_bars / index_constituents / industry_members / macro_indicators / market_breadth）是「没调度」被算成 stale，不影响行情
