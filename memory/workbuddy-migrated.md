---
title: WorkBuddy 记忆迁移归档
date: 2026-10-23
source: ~/.workbuddy/memory/ 与 ~/WorkBuddy AI/*/.workbuddy-ai/memory/
---

# WorkBuddy 记忆迁移归档

> 2026-10-23 归档。跨项目可复用的约定已提炼进 `MEMORY.md` 与 `USER.md`；这里保留**项目私有**的内容，原文件仍在原处，可继续被 WorkBuddy 读取。

## 来源清单

| 位置 | 内容 | 处理 |
|---|---|---|
| `~/.workbuddy/memory/02e67107-…_memory.md` | App 级用户记忆，`memoryBlock` 为空 | 无内容可迁 |
| `~/WorkBuddy AI/博物馆探索/.workbuddy-ai/memory/MEMORY.md` | 博物馆项目约定 + 12 条跨会话踩坑 | 通用踩坑已提炼 |
| `~/WorkBuddy AI/历史学习/.workbuddy-ai/memory/MEMORY.md` | 历史学习应用项目记忆（多 Agent 分工） | 项目私有，保留 |
| `~/WorkBuddy AI/投资/.workbuddy-ai/memory/MEMORY.md` | CNEquity 数据湖项目记忆 | 项目私有 + 2 条通用坑 |
| `~/WorkBuddy AI/{Claw,博物馆,未来模板,2026-10-23-17-00-39}/…/YYYY-MM-DD.md` | 按日工作日志 | 不迁，属于流水 |

---

## 博物馆探索（项目私有）

工作区：`~/WorkBuddy AI/博物馆探索/`（2026-10-08 从 Obsidian 库迁出）

- **数据源必须用官方文件**：195 件永禁出境文物以国家文物局三批目录 PDF 为准（文物办发〔2002〕5 号 / 文物博函〔2012〕1345 号 / 文物博函〔2013〕1320 号），原件在 `tools/source/`。网上流传版本有 3 处错。
- **构建工具全在 `tools/`**，路径相对脚本自身定位（`_HERE = dirname(abspath(__file__))`）。链条：`build.py`（数据）→ `build_html.py`（全国页）→ `build_hz.py`（杭州页）。一键重建：双击根目录 `重新构建.command`
- **图片只取 Wikimedia Commons 的公有领域 / CC 授权**，经 Wikidata `P18` 中转匹配。每张保留署名，卡片下方渲染「📷 许可 · 作者」
- **展厅信息不做**（用户明确要求）：展厅轮展换柜，写死会误导。改为每张卡片给「官方入口」
- **用户照片只存本机**：IndexedDB（`guobao_photos_v1`），不上传、零服务器成本
- **本地运行**：双击 `启动博物馆探索.command` → `127.0.0.1:8765` 静态服务。**不要直接双击 HTML**（腾讯地图 JS API GL 不支持 `file://`）
- **腾讯地图 key**：`tmap-key.txt` 或环境变量 `TMAP_KEY`；没配 key 时不初始化地图，显示「地图未启用」
- **图片流水线**：`tools/wdpipe.py` → `wdall.py` → `repair.py` → `build.py`。42/195 有实物照片，命中率约 3 成（冷门文物在 Wikidata 上确实没有 `P18`）
- **三道数据质量闸门**（`build.py`）：名称三级匹配（精确→归一化→子串）｜`BAD_MATCH` 黑名单｜`MAX_ASPECT=4.0` 长宽比闸门
- **验证脚本在 `tools/tests/`**，最常用 `verify.js`（三页一次过）

---

## 历史学习应用（项目私有）

工作区：`/Users/chenjie/WorkBuddy AI/历史学习`

- 工程：`app/`（Vite 5 + React 18 + TS 5.6 + Zustand 4 + Dexie 4，纯前端无后端）
- 文档：`历史学习应用-需求设计.md`｜`历史学习应用-Spec-Plan.md`｜`历史学习应用-原型.html`
- **三条铁律**：①文件独占 ②契约冻结（`src/types/index.ts` 不得私自增删）③节点不复制（`Thread.nodeIds` 只引用 id）
- 已交付 A1~A6；**待办 A7** 辅助与导出（`suggestNeighbors` + `exportMarkdown`），依赖 A3 的 `logic.ts`
- **关键决策**：时间 = 坐标（公元年，可负）；地点 = 历史地名；朝代取「不晚于该年的最后一个朝代起点」；年份夹在 `[-5000, 当前年]`
- 地图合规：只用腾讯地图 GL JS + `_TMapSecurityConfig` 代理，前端零 key；禁止 Google / OSM / Mapbox / 手绘中国轮廓
- **地图 SDK 调用一律套 `safeRun`**，鉴权失败时 SDK 会抛出，冒到 React 里会白屏
- `.map-stage` 必须有 `z-index: 0`，否则被 SDK 版权层盖住
- 语义色：民间推动 = 蓝、国家推动 = 赭、空白 = 虚线琥珀、当前镜头 = 赭红
- **已知死代码**：`features/map/powerArea.ts` 未被引用

---

## 投资数据湖（项目私有）

工作区：`/Users/chenjie/WorkBuddy AI/投资`

- 本地 CNEquity A 股数据湖 + MCP 只读接口。不是选股软件，不产生信号。
- venv：`/Users/chenjie/WorkBuddy AI/投资/.venv`；必须 `./.venv/bin/python3 ./.venv/bin/cne-wb`
- **读数据必须 `hive_partitioning=false`**：DuckDB 会用分区目录名顶掉同名字段（`trade_date=2023/` 把 DATE 静默变成 BIGINT 2023），不报错
- 自检：`select count(distinct trade_date)`，正常 700+，只剩 4~5 个就是踩了
- 湖结构：`data/cnequity/{curated,derived}/<dataset>/<分区>/part-merged.parquet`
- **北交所无历史**（只有当日 tip bar，换 920 号段后新浪只认旧代码）
- `snapshot_only` 数据集没有历史可回填，只能从首次采集日积累
- 看板：launchd `com.cnequity.lake-serve`，http://127.0.0.1:8787/
- 排障顺序：`cne status`（看 `orphaned_running_runs`）→ manifest 的 `ingestion_batches` → `cne check`
- Obsidian 联动：`投资研究/`（236 篇），`选股分析/` 六线标准：PE<20、PB<2、ROE>15%、行业垄断、确定性增长、上市满5年
