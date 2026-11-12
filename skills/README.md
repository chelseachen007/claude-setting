# 技能索引

> 本文件是 `~/ai/skills/` 的**索引层**，不是技能。
> 目的：AI 找能力时先读这里，判断「这件事该用哪个技能」，再进子目录读 SKILL.md，
> 而不是把 96 个技能的 description 全部塞进上下文。
>
> 新增/删除技能时同步改这里。技能本体只在 `~/ai/skills/<name>/SKILL.md`。
> **2026-11-11 起 Obsidian 库的 23 个专用技能已全部并入本目录**，库里 `.agents/skills/` 只剩 `sigma` 软链，不要再往库里放技能。

## 怎么用

1. 先在这张表里按**场景**找到候选技能名。
2. 再读 `~/ai/skills/<name>/SKILL.md` 拿完整流程。
3. 表里没有 → 去 `find-skills` 找有没有现成的可装，别从头造。

## 一级场景分类

### 投资与金融
| 技能 | 什么时候用 |
|---|---|
| `a-share-pre-trade-gate` | 下单前纪律关卡：计划、止损、仓位、报复窗口、大盘状态，出 GO / NO_GO |
| `signal-postmortem-a-share` | 交易信号事后归因：5/20 日收益、真阳性/假阳性/错失机会分类 |
| `stock-investment-report` | 个股投资分析报告（评分体系 + 模板） |
| `stock-debate-analysis` | 结构化多空辩论，用数据论证出结论 |
| `cn-finance-toolkit` | A股/港股行情、财务指标、宏观数据（skill 内 name 为 `findata-toolkit-cn`） |
| `balance-arbitrage` | Buff 买、Steam 卖算倒余额折扣与收益 |
| `bill-screenshot-parser` | 账单截图 / CSV / XLSX → 交易记录 |
| `fin-report-check` | 个股财报校对：核口径（股息率TTM/分红率、归母/扣非）、核数字、核披露年份 |

> 投资类技能的**数据抓取约定**在 `~/ai/invest/AGENTS.md`：统一走
> `工具/抓数/fetch_eastmoney.py`，别另写一次性脚本。

### 浏览器与联网
| 技能 | 什么时候用 |
|---|---|
| `web-access` | **所有联网/需登录/动态渲染页面的入口**：CDP proxy `127.0.0.1:3456`，带用户登录态 |
| `browser-skill` | bsk CLI + 扩展，操作已登录 Chromium（读页面、填表、抓数据、测 UI） |
| `webapp-testing` | 测本地 web 应用：Playwright 驱动、截图、看浏览器日志 |
| `gemini-media` | 走 Gemini 网页端生成图/视频，不用 API key |
| `last30days` | 最近 30 天跨平台大家在聊什么（Reddit/YouTube/HN/GitHub/小红书） |

### Obsidian 与知识管理
| 技能 | 什么时候用 |
|---|---|
| `media-transcriber` | 音视频/播客/逐字稿 → 保留细节的中文长稿 |
| `xiaopang-video-transcript` | 抓字幕：B站走 CDP、YouTube 走 yt-dlp、其他走本地 ASR，`ingest.ts` 落成视频学习笔记 |
| `weread-skills` | 微信读书：搜书、书架、划线笔记、书评、阅读统计 |
| `carl-weread` | 微信读书行动型阅读教练：今天读哪一小节 → 转成行动卡与选题 |
| `hv-analysis` | 横纵分析法深度研究，产出 PDF 报告 |

| `clip-and-process` | **剪藏唯一入口**：识别视频/音频/网页/英文 → 分发 worker → 存 `剪藏/` → 可选深度处理 |
| `clip-process` | 纯深度处理：给 `剪藏/` 里 `状态/未整理` 的文章补闪念、常青笔记、连接、行动 |
| `article-extractor` | 文章/视频链接 → 提取要点做笔记 |
| `reading-loop` | 微信读书 × Obsidian × Notion 读书闭环：带问题读 → 复盘 → 同步 Notion |
| `book-mirror` | 书镜：把书映射到你的经历，出双栏「脑页」 |
| `daily-learning-journal` | 今日学习总结 / 复盘，周五自动切周复盘 |
| `ob-vault-overview` | 扫库出知识地图：枢纽、孤岛、聚类 → `索引/知识地图.md` |
| `xueqiu-digest` | 雪球每日精选日报（CDP 抓取 + 脚本评分 + 智能分析 → `投资研究/雪球日报/`） |
| `defuddle` | HTML → 干净 Markdown（CLI），抓取降级链的最后一层 |
| `knap` | 模板 + JSON/CSV → 批量生成 Markdown，配合 defuddle 出笔记 |
| `obsidian-markdown` | Obsidian 风味 Markdown：wikilink、callout、frontmatter、embed |
| `obsidian-bases` | `.base` 文件：视图、筛选、公式、汇总 |
| `json-canvas` | `.canvas` 文件：节点、连线、分组，画思维导图/流程图 |
| `obsidian-cli` | Obsidian CLI：读写检索笔记任务属性，也能重载插件、看 DOM 截图调试 |

### 内容生产与发布
| 技能 | 什么时候用 |
|---|---|
| `multi-publish` | 一键发公众号草稿箱 + 小红书 |
| `xhs-cover` | 小红书封面图（HTML+CSS 截图出图） |
| `baoyu-translate` | 快翻/普通/精翻，支持术语表 |
| `banner-design` / `brand` / `design` / `design-system` | 视觉与品牌：banner、品牌规范、logo/CIP、设计 token |
| `pang-writer` | 公众号长文：按你的风格从素材出稿、续写、扩写 |
| `writing-evolve` | 写作进化：对比 AI 原稿与人改终稿，提取规律写进化录 |
| `content-diagnosis` | 发布前 6 维诊断：IP 辨识度、真人感、产品桥梁、情绪路径、AI 味、合规 |
| `card-caster` | 「铸」：内容 → PNG 长图 / 信息图 / 多卡 / 视觉笔记 / 漫画 |
| `md-to-pdf` | Obsidian 笔记 → 排版精美的 PDF（单文件或整目录） |
| `yao-tutorial-skill` | 输入主题/资料 → 生成教程（tutorial.md + 配图） |

### 前端与界面
| 技能 | 什么时候用 |
|---|---|
| `frontend-design` | 做出不像 AI 味的前端界面 |
| `ui-ux-pro-max` | 本地 CSV 检索：79 风格 / 192 配色 / 119 UX 规则 / 22 技术栈 |
| `ui-styling` | shadcn/ui + Tailwind + canvas 视觉 |
| `vue-best-practices` | 写/审 Vue 组件，props、vue-tsc 类型检查 |
| `nuxt` | Nuxt SSR、useFetch、中间件、Nitro |
| `pixel-replicate` | 照目标页面逐像素还原 DOM/CSS |

### 后端与工程规范
| 技能 | 什么时候用 |
|---|---|
| `api-design-principles` / `review-api-design` | 设计或评审 REST/GraphQL |
| `springboot-patterns` / `springboot-tdd` / `springboot-verification` | Spring Boot 架构模式 / TDD / 完整验证循环 |
| `java-coding-standards` | Java 编码规范 |
| `domain-modeling` | 领域模型、GLOSSARY、ADR |
| `mcp-builder` | 造 MCP server（FastMCP / MCP SDK） |

### 测试
| 技能 | 什么时候用 |
|---|---|
| `tdd-workflow` | 先写失败测试 → 最小实现 → 重构，80%+ 覆盖 |
| `e2e-testing` | Playwright E2E 结构、POM、CI、flaky 治理 |
| `playwright` / `cypress` / `selenium` / `appium` / `detox` | 各测试框架的写法与坑 |
| `jest` / `vitest` / `pytest` / `junit` | 单测框架 |
| `test-collaboration` | 测试资产盘点：TEST-ID 与需求/风险/缺陷的对应 |

### 办公文档
| 技能 | 什么时候用 |
|---|---|
| `docx-anthropic` | Word 读写、批注、修订（skill 内 name 为 `docx`） |
| `docx-template-bookmark-tagging` | docx 清成空白模板 + 打标签 + 书签/字段分类 json |
| `pptx-anthropic` | 读取/生成/编辑 PPT（skill 内 name 为 `pptx`） |
| `youshu-formula` | 有数 BI 公式：语法坑、LOD、参数筛选 |

### 流程与元能力
| 技能 | 什么时候用 |
|---|---|
| `brainstorm` | 动手前先把方向想清楚 |
| `grilling` / `grill-me` | 拷问计划/决策，压力测试自己的思路 |
| `skill-creator` / `yao-meta-skill` | 造/改/评技能，做 trigger 评测与打包 |
| `find-skills` | 找可安装的技能 |
| `commit` | 按 Conventional Commits 提交 |
| `github` | gh CLI：issue、PR、CI |
| `project-analyzer` | 30 分钟看懂一个陌生项目，出 4 份学习文档 |
| `find-skills` 之外的 `storage-analyzer` | 磁盘/存储占空间分析与清理方案（只读扫描） |
| `multi-agent-parallel-dev` / `asset-platform-parallel-delivery` | 多 agent 并行开发的编排与验收 |
| `morning-brief` | 中台定时派活：写当天早报 |
| `sigma` | Bloom 2-sigma 个性化辅导 |
| `resume-optimization-pro` | 简历优化与面试准备 |
| `flyai` | 飞猪 MCP：机票、酒店、景点、演出 |
| `travel-planner` | 目的地 + 天数 → 攻略：路线、景点池、排坑、预订链接 |

### 平台与自动化
| 技能 | 什么时候用 |
|---|---|
| `agent-autoloop` | 配 Agent 自动化中台：规则、事件插件、通道、部署 |
| `wechat-clawbot-push` | 主动推送到个人微信（iLink bot） |
| `lark-suite` | 飞书全家桶（审批、多维表格、云文档、日历、任务、妙记……） |
| `workbuddy-internals-debug` | 排查 WorkBuddy 内置功能报错 |
| `dsh-chat-import-usage` / `dsh-chat-import-convert`（**插件内建，不在本目录**） | 外部会话导入 DSH：各来源格式路径表、参数与重导规则；把任意对话记录转成 interchange v1 文档 |

## 待处理（已知问题，别当成好用的技能）

| 技能 | 问题 |
|---|---|
| `source-command-xiaohongshu-skills-skills-xhs-publish-skill` | 旧 slash command 迁移残留，名字超长，与 `multi-publish` 的小红书能力重叠，建议删 |
| `pixel-replicate` | 缺 YAML frontmatter（无 name/description），模型无法按描述触发 |
| `morning-brief` | description 只写「写早报」，没写产出落点与幂等规则，靠正文才知道 |
| `cn-finance-toolkit` / `docx-anthropic` / `pptx-anthropic` | 目录名与 `name` 不一致，按 name 找会找不到 |

> 已经踩过、不用再查的坑：**技能之间不要互相硬编码 `~/.claude/skills/…`、`~/.Codex/skills/…`、
> `~/.workbuddy-ai/skills/…`**。跨技能调用一律写 `~/.agents/skills/<name>/…`（dsh 和 Codex 共用的那个入口），
> 自己目录内的文件用 `SKILL_DIR` 或 `$(dirname "$0")` 推导。2026-11-11 全库扫过一遍，旧写法已清零。

---

更新时间：2026-11-11
