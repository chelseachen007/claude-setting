---
summary: "GitHub 关注名单 + 收藏夹的全局索引：46 位关注对象是谁、他们的高星项目、大佬们共同收藏的技术栈、AI 应用方向该补关注的人。"
read_when:
  - 要选技术栈、找现成轮子、判断某技术值不值得用之前（先查这里，别人已经收藏过了）
  - 想找人问、找参考实现、找学习资源时
  - 想判断「这个东西流行吗」时看「共识层」的收藏人数
updated: 2026-11-12
source: gh api（账号 chelseachen007，抓取于 2026-11-12，数据快照在同目录 *.tsv）
---

# GitHub 全局索引

> 用途：**防重复造轮子。** 写新工具前先在这里搜一遍，再看「共识层」。
> 搜索方式：`grep -i 关键词 ~/ai/memory/projects/github-mirror/INDEX.md`
> 更新：`gh api` 重新抓（见文末「刷新方式」），别手改数据要动就重跑。

五张表：

| 层 | 是什么 | 怎么用 |
|---|---|---|
| [一、关注对象](#一关注对象46-人) | 我 follow 的 46 个人，谁靠谱、谁该取关 | 找人、看某人最强的东西 |
| [一 B、AI 方向该补关注的人](#一-bai-应用方向该补关注的人2026-11-12-扫出来) | 90 位 AI 候选筛出的四梯队，含「现在就关注这 12 个」 | 补人时看这里 |
| [二、关注对象的高星项目](#二关注对象的主力项目) | 每人 top 8 仓库 | 找参考实现、找学习材料 |
| [三、大佬共识层](#三、大佬的共识收藏≥6-人收藏) | 24 人的收藏里被 ≥6 人共同收藏的 239 个仓库 | **选型直接看这里**，被 8 个以上大佬收藏的基本可以闭眼用 |
| [四、我的收藏](#四、我的收藏146-个-star-都是干什么用的) | 我自己 146 个 star 全部按用途归类 | 查「这个我收过没有」 |

**2026-11-12 的一个重要事实：我的 146 个 star 和 46 位关注对象的收藏夹，直接重合 0 个。**
但换个口径看：我的收藏里**有 86 个**出现在第三节「共识层」（被 ≥5 人收藏）。所以不是品味跑偏，是**收藏散、没有主线**——按搜索和推荐随手收，而不是顺着一条技术主线往里填。第三节要解决的正是这个。

---

## 一、关注对象（46 人）

### 还在更新、值得盯（2026 年仍有 push）

| 人 | 主领域 | 最值得看的东西 | 备注 |
|---|---|---|---|
| [phodal](https://github.com/phodal) | 全栈 / AI 工程 | `auto-dev`（多 Agent 编码平台）、`understand-prompt`、Growth 系列电子书 | 杭州，Thoughtworks 出身，中文技术写作标杆 |
| [ruanyf](https://github.com/ruanyf) | 科普 / 教程 | `weekly` 科技周刊、`es6tutorial`、`free-books` | 每周五必看 |
| [ascoders](https://github.com/ascoders) | 前端精读 | `weekly` 前端精读周刊 | 字节，杭州 |
| [PanJiaChen](https://github.com/PanJiaChen) | Vue 后台 | `vue-element-admin`（9 万星） | 后台模板的事实标准，但 2024 后基本停更 |
| [azl397985856](https://github.com/azl397985856) | 算法 | `leetcode` 题解（5.5 万星）、`fe-interview` | 「力扣加加」 |
| [doodlewind](https://github.com/doodlewind) | JS 底层 / 图形 | `jshistory-cn`《JavaScript 二十年》、`beam` WebGPU 渲染 | 前 Toeverything 联合创始人 |
| [woai3c](https://github.com/woai3c) | 前端工程 / 系统 | `visual-drag-demo` 低代码、`nand2tetris`、`MIT6.828` | 笔记型仓库质量高 |
| [linonetwo](https://github.com/linonetwo) | 知识管理 / 游戏 AIGC | `segmentit` 中文分词、LangChain-Alpaca | TiddlyWiki 社区核心，收藏夹 3500+ |
| [zzzzzhowie](https://github.com/zzzzzhowie) | 数据 / AI Agent / CI | `file-upload` 大文件上传、`practical-javascript` | TikTok，圣何塞 |
| [HcySunYang](https://github.com/HcySunYang) | Vue 源码 | `vue-design`《渲染器》 | 微软 |
| [LuckyWinty](https://github.com/LuckyWinty) | 前端 | 博客、面试题 | 腾讯 |
| [dailc](https://github.com/dailc) | 前端 / 图像处理 | `image-process` | 阿里，杭州 |
| [xlzy520](https://github.com/xlzy520) | 小程序 | `uniapp-tailwind-uview-starter` | 深圳 |
| [Adashuai5](https://github.com/Adashuai5) | Agent Skill / 理财知识 | `awesome-financial-freedom`（打包成 skill 的理财知识） | 跟你两个方向都对得上 |
| [su37josephxia](https://github.com/su37josephxia) | 手写轮子 | `wheel-awesome`「天天造轮子」 | 适合对照学习 |
| [react-component](https://github.com/react-component)（组织） | React 组件基座 | antd 底层的 `table`/`form`/`select` | 直接读源码学组件设计 |
| [unrealflow](https://github.com/unrealflow) | 图形 / Vulkan / Shader | `Hexbound`、`LearnVulkan` | 图形方向 |
| [DeianHsu](https://github.com/DeianHsu) | AI Agent 练手 | `demo-mini-swe-agent`、游戏自动化助手 | 收藏少但项目新 |

### 已停更但仓库仍是经典（读仓库不读人）

| 人 | 代表作 | 状态 |
|---|---|---|
| [fouber](https://github.com/fouber) | `blog`（2.2 万星）、`page-monitor` | 2019 后停 |
| [mqyqingfeng](https://github.com/mqyqingfeng) | `Blog`「JS 深入系列」（3.1 万星）、`Wheels` | 2026-06 后停 |
| [answershuto](https://github.com/answershuto) | `learnVue` Vue 源码解析 | 阿里，2023 停 |
| [ityouknow](https://github.com/ityouknow) | `spring-boot-examples`（3 万星） | Java 方向，你不走这条路 |
| [berwin](https://github.com/berwin) | 《深入浅出 Vue.js》、`Blog` | 淘宝，2023 停 |
| [icarusion](https://github.com/icarusion) | iView 作者、`vue-book` | 2023 停 |
| [biaochenxuying](https://github.com/biaochenxuying) | `blog` 全栈博客模板 | 2024 停 |
| [shengxinjing](https://github.com/shengxinjing) | `programmer-job-blacklist`（2.8 万星） | 求职黑名单，还在维护 |
| [LiangJunrong](https://github.com/LiangJunrong) | `document-library` 文档库 | 2024 停 |
| [qdlaoyao](https://github.com/qdlaoyao) | 《JS 正则迷你书》 | 2019 停 |
| [suukii](https://github.com/suukii) | `91-days-algorithm` 图解算法题解 | 2023 停 |
| [amikey](https://github.com/amikey) | 全是别人的 fork（12306、Anki） | fork 站，没有原创价值 |

### 建议取关（零原创产出 / 多年无动静）

`huanglinsong`、`cjygis`、`gryphonWcw`、`Lucas0719`、`FangCWProject`、`fswhq`、`xutianhuii`、`hiraras`、`okbug`、`feikerwu`、`lvxiaowu`、`lxhguard`、`co-star`、`FontEndArt`、`taopoppy`、`wow-lc`
—— 这 16 人最高星项目都不超过 20，或仓库为 0～2 个。关注他们等于给信息流加噪音。
（`huanglinsong` / `FontEndArt` 如果是同事或群友就留着，别一刀切。）

---

## 一 B、AI 应用方向该补关注的人（2026-11-12 扫出来）

> 口径：GitHub `search/repositories` 20 组 AI 关键词 → 1817 个仓库 → 只留 User 账号、仓库 2026-05 后仍有 push、排除已关注的 46 人 → 按最高星取前 90 → 人工筛。
> 数据快照：`ai_candidates.json`（90 人完整元信息，含每人 top5 仓库）。
> **你的 46 人名单里一个「AI Agent / 上下文工程」一线的都没有**——phodal、linonetwo、zzzzzhowie 沾边，但主力不在 Phase。下面是真正在做这件事的人。

### 第一梯队：直接对应你要解决的问题（上下文工程 / Agent 工程化）

你的痛点是「AI 收藏 42 个但没跑通」+「上下文工程 / 任务分解 / 验证体系 / 代码审查」这四个方向。这批人正好各占一个：

| 人 | 星 | 代表作（星） | 为什么对你有用 |
|---|---|---|---|
| [obra](https://github.com/obra) | 9.5k | `superpowers`（31.7 万） | **Skills 编排的源头**。你的 `~/ai/skills/` 体系跟它是同一套思路，值得对照看它的 skill 描述怎么写、怎么被调度 |
| [affaan-m](https://github.com/affaan-m) | 14.2k | `ECC`（30.2 万） | Agent harness 的**性能优化层**：skills、instincts、memory、安全。Jump Trading 的 compute lead，工程含量高的那一类 |
| [code-yeongyu](https://github.com/code-yeongyu) | 4.1k | `oh-my-openagent`（7.1 万） | 多 Agent 编排（OmO），一个 prompt 触发任务分解 |
| [Yeachan-Heo](https://github.com/Yeachan-Heo) | 4.8k | `oh-my-claudecode`（4.1 万） | 团队式多 Agent 编排，**README 里有完整的并行分工设计**，跟你的 `multi-agent-parallel-dev` 技能直接对得上 |
| [can1357](https://github.com/can1357) | 3.9k | `oh-my-pi`（3.9 万） | 把 IDE 焊进 coding agent 的思路 |
| [wshobson](https://github.com/wshobson) | 2.4k | `agents`（4.2 万） | Claude Code / Codex 的 **agent + skill + command 集合**，现成可抄的目录结构 |
| [bojieli](https://github.com/bojieli) | 3.3k | `ai-agent-book`（5.8 万）、`ai-infra-book`（7.5k） | **中文**《深入理解 AI Agent》开源全书 + 配套代码。比零散收藏强，一本顶十个仓库 |
| [shanraisshan](https://github.com/shanraisshan) | 1.5k | `claude-code-best-practice`（6.9 万） | 从 vibe coding 到 agentic engineering 的实践手册 |
| [mvanhorn](https://github.com/mvanhorn) | 6.0k | `last30days-skill`（6.7 万） | 你已经装了同款 skill（`last30days`），作者本人值得跟 |
| [linshenkx](https://github.com/linshenkx) | 0.3k | `prompt-optimizer`（4.1 万） | 提示词优化器，中文作者，你已经有星标，人没关注 |

### 第二梯队：记忆 / 上下文 / 基础设施（你现在自己搭的那层）

| 人 | 星 | 代表作（星） | 为什么对你有用 |
|---|---|---|---|
| [thedotmack](https://github.com/thedotmack) | 2.5k | `claude-mem`（11.6 万） | 跨会话持久记忆。你在用 Mnemon + `~/ai/memory/`，这是另一条实现路线 |
| [DeusData](https://github.com/DeusData) | 0.9k | `codebase-memory-mcp`（4.9 万） | 代码库级记忆 MCP，把 repo 变成可查询的结构 |
| [mksglu](https://github.com/mksglu) | 0.7k | `context-mode`（3.4 万） | **把工具输出挡在上下文之外**——「单次任务百万 token」那个问题，这是正经解法之一 |
| [rohitg00](https://github.com/rohitg00) | 7.7k | `ai-engineering-from-scratch`（7.9 万）、`agentmemory`（3 万） | 从零学 AI 工程的完整路线 |
| [patchy631](https://github.com/patchy631) | 3.4k | `ai-engineering-hub`（4.2 万） | RAG / Agent 真实项目的教程库 |
| [unclecode](https://github.com/unclecode) | 2.1k | `crawl4ai`（8.7 万） | 喂给 LLM 的网页抓取，你的剪藏/抓取链路可以对照 |
| [punkpeye](https://github.com/punkpeye) | 2.2k | `awesome-mcp-servers`（9.8 万） | MCP 生态总目录 |
| [AlexsJones](https://github.com/AlexsJones) | 1.6k | `llmfit`（3.9 万） | 一条命令判断某个模型能不能跑本地 |
| [hiyouga](https://github.com/hiyouga) | 6.9k | `LlamaFactory`（7.6 万） | 微调 100+ LLM/VLM 的统一框架（北京） |
| [jingyaogong](https://github.com/jingyaogong) | 2.4k | `minimind`（6.5 万） | 2 小时从零训一个 64M 的 LLM，理解原理最短路径 |

### 第三梯队：模型路由 / 网关 / 国内可用（跟你 `magpie` 那套直接相关）

| 人 | 星 | 代表作 | 为什么对你有用 |
|---|---|---|---|
| [musistudio](https://github.com/musistudio) | 0.6k | `claude-code-router`（3.8 万） | **杭州**，一个本地控制面路由所有 agent 的模型。跟 magpie 是同题不同解 |
| [yetone](https://github.com/yetone) | 10.8k | `magpie`（3.5 万） | **你正在用的网关就是他写的**，居然没关注 |
| [Wei-Shaw](https://github.com/Wei-Shaw) | 1.2k | `sub2api`（4.6 万）、`claude-relay-service`（1.3 万） | 订阅转 API / 拼车共享，你的收藏里有 `sub2api` |
| [Ebony-Vinyl](https://github.com/Ebony-Vinyl) | 0.3k | `dsh-our-free-model`（7.1 万） | 往 dsh 里装插件免 API Key 用模型 |
| [asgeirtj](https://github.com/asgeirtj)、[x1xhlol](https://github.com/x1xhlol) | 2.4k / 3.9k | `system_prompts_leaks`（7.1 万）、`system-prompts-and-models-of-ai-tools`（14.5 万） | 各家产品的真实 system prompt。**写 agent 时最直接的参考样本**，你两个都收了星，人都没关注 |
| [tw93](https://github.com/tw93) | 13.8k | `Pake`（6.3 万）、`Waza`（7.5k） | 国内独立开发者，`Waza` 是「把工程习惯变成 AI skill」的集合 |

### 第四梯队：跟你理财 / 知识管理方向交叉

| 人 | 星 | 代表作 | 为什么 |
|---|---|---|---|
| [ZhuLinsen](https://github.com/ZhuLinsen) | 1.9k | `daily_stock_analysis`（7.1 万） | LLM 驱动的多市场股票分析，零成本定时跑。跟你投资数据湖同题 |
| [hsliuping](https://github.com/hsliuping) | 0.3k | `TradingAgents-CN`（3.3 万） | 多智能体中文金融交易框架 |
| [sansan0](https://github.com/sansan0) | 1.7k | `TrendRadar`（6.4 万） | 多平台舆情热点监控，跟你的早报/雪球日报是同一条线 |
| [freestylefly](https://github.com/freestylefly) | 2.3k | `awesome-gpt-image-2`（3.6 万） | Prompt as Code，530+ 图像提示词案例 |

### 建议动作（按优先级）

**现在就关注这 12 个**（覆盖你的四个方向，一人一件事）：
`obra`、`affaan-m`、`Yeachan-Heo`、`code-yeongyu`、`bojieli`、`hiyouga`、`yetone`、`musistudio`、`mksglu`、`thedotmack`、`punkpeye`、`asgeirtj`

**接下来一周读这 5 个仓库**（不用关注人，直接看东西）：
1. `bojieli/ai-agent-book` —— 中文体系化，每天一章
2. `obra/superpowers` —— 对照你的 `~/ai/skills/`，看 skill 的组织方式差在哪
3. `Yeachan-Heo/oh-my-claudecode` —— 并行分工设计，对着 `multi-agent-parallel-dev` 技能改
4. `mksglu/context-mode` —— 解决「工具输出吃上下文」
5. `asgeirtj/system_prompts_leaks` —— 抄别家的 system prompt 写法

**不建议关注的**：`DietrichGebert`（`ponytail`）、`JuliusBrussee`（`caveman`）、`Leonxlnx`（`taste-skill`）、`Panniantong`、`cathrynlavery`、`Imbad0202`、`zhaoxuya520`、`Donchitos`、`h4ckf0r0day`、`tt-a1i`、`koala73` —— 清一色「单仓库爆款 + 仓库描述含糊 + 没有持续产出」，跟你的零原创取关名单是同一类。高星不等于值得跟。

---

## 二、关注对象的主力项目

> 每人取 star 最高的 8 个仓库（不含 fork）。共 44 人、311 条，全量在 `repos.tsv`。
> 这里只列**跟你当前方向（前端 → 全栈 + AI 应用）真的相关**的。

| 人 | 值得看的仓库（按这个顺序翻） |
|---|---|
| phodal | `auto-dev` 多 Agent 编码平台、`understand-prompt` 提示词理解、`growth-ebook` / `migration` 电子书、`awesome-growth` |
| ruanyf | `weekly`（每周五）、`es6tutorial`、`free-books`、`jstraining` |
| ascoders | `weekly` 前端精读（理解源码写法的模板） |
| azl397985856 | `leetcode`、`fe-interview`、`awesome-coding-js` |
| PanJiaChen | `vue-element-admin`、`vue-admin-template` |
| doodlewind | `jshistory-cn`《JavaScript 二十年》、`beam`（WebGPU 文本渲染引擎） |
| woai3c | `visual-drag-demo` 可视化拖拽编辑器、`nand2tetris`、`MIT6.828` |
| linonetwo | `segmentit` 中文分词、`TiddlyWiki` 插件族 |
| zzzzzhowie | `file-upload`（大文件分片上传完整方案）、`vue2-admin` |
| HcySunYang | `vue-design`《Vue.js 设计与实现》 |
| su37josephxia | `wheel-awesome` 天天造轮子 |
| mqyqingfeng | `Blog` JS 深入系列、`Wheels` 手写系列 |
| fouber | `blog`（前端工程化思想提纲） |
| answershuto | `learnVue` |
| dailc | `image-process` |
| LuckyWinty | `fe-books`、面试题 |
| Adashuai5 | `awesome-financial-freedom`（把理财知识打包成 Agent Skill） |
| xlzy520 | `uniapp-tailwind-uview-starter` |
| unrealflow | `Hexbound`、`LearnVulkan` |
| DeianHsu | `demo-mini-swe-agent` |
| react-component | `table`、`form`、`select`（antd 的底座，直接读源码学组件设计） |

其余人的高星项目基本都在上面 20 人里重复出现；完整 311 条看 `repos.tsv`（`cut -f1,2,3 repos.tsv | sort -t$'\t' -k3 -gr`）。

---

## 三、大佬的共识收藏（≥6 人收藏）

> 24 位大佬收藏里，239 个仓库被 ≥6 人收藏。**「收藏」= 这 24 人里有几人 star 了它**；≥8 人 = 这个圈子的公共设施，可以闭眼用。


### AI / Agent 工程

| 仓库 | 收藏 | 干什么 |
|---|---|---|
| [openclaw/openclaw](https://github.com/openclaw/openclaw) | 9 | The AI that really does things. Any OS. Any Platform. The lobster way. 🦞  |
| [earendil-works/pi](https://github.com/earendil-works/pi) | 8 | AI agent toolkit: unified LLM API, agent loop, TUI, coding agent CLI |

<details><summary>AI / Agent 工程：其余 3 个（6–7 人收藏）</summary>

| 仓库 | 收藏 | 干什么 |
|---|---|---|
| [deepseek-ai/deepseek-harness](https://github.com/deepseek-ai/deepseek-harness) | 7 | DeepSeek Harness: Everything is a Plugin. |
| [browser-use/browser-use](https://github.com/browser-use/browser-use) | 7 | Open-source Python library for AI browser agents, plus Browser Use Cloud: stea |
| [naptha/tesseract.js](https://github.com/naptha/tesseract.js) | 6 | Pure Javascript OCR for more than 100 Languages 📖🎉🖥 |

</details>

### 框架、状态与跨端

| 仓库 | 收藏 | 干什么 |
|---|---|---|
| [vuejs/vue](https://github.com/vuejs/vue) | 15 | This is the repo for Vue 2. For Vue 3, go to https://github.com/vuejs/core |
| [react/react](https://github.com/react/react) | 14 | The library for web and native user interfaces. |
| [vuejs/core](https://github.com/vuejs/core) | 9 | 🖖 Vue.js is a progressive, incrementally-adoptable JavaScript framework for bu |
| [umijs/qiankun](https://github.com/umijs/qiankun) | 9 | 📦 🚀 Blazing fast, simple and complete solution for micro frontends. |
| [nuxt/nuxt](https://github.com/nuxt/nuxt) | 9 | The full-stack Vue framework. |
| [single-spa/single-spa](https://github.com/single-spa/single-spa) | 8 | The router for easy microfrontends |
| [PanJiaChen/vue-element-admin](https://github.com/PanJiaChen/vue-element-admin) | 8 | :tada: A magical vue admin                                                     |

<details><summary>框架、状态与跨端：其余 23 个（6–7 人收藏）</summary>

| 仓库 | 收藏 | 干什么 |
|---|---|---|
| [vuejs/vuex](https://github.com/vuejs/vuex) | 7 | 🗃️ Centralized State Management for Vue.js. |
| [tauri-apps/tauri](https://github.com/tauri-apps/tauri) | 7 | Build smaller, faster, and more secure desktop and mobile applications with a  |
| [statelyai/xstate](https://github.com/statelyai/xstate) | 7 | State machines, statecharts, and actors for complex logic |
| [nestjs/nest](https://github.com/nestjs/nest) | 7 | A progressive TypeScript framework for Node.js backends: from a small API in o |
| [mobxjs/mobx](https://github.com/mobxjs/mobx) | 7 | Simple, scalable state management. |
| [eggjs/egg](https://github.com/eggjs/egg) | 7 | 🥚🥚🥚🥚 Born to build better enterprise frameworks and apps with Node.js & Koa. h |
| [dcloudio/mui](https://github.com/dcloudio/mui) | 7 | 最接近原生APP体验的高性能框架 |
| [baidu/amis](https://github.com/baidu/amis) | 7 | 前端低代码框架，通过 JSON 配置就能生成各种页面。 |
| [ant-design/ant-design-pro](https://github.com/ant-design/ant-design-pro) | 7 | 👨🏻‍💻👩🏻‍💻 Use Ant Design like a Pro! |
| [alibaba/weex](https://github.com/alibaba/weex) | 7 | A framework for building Mobile cross-platform UI |
| [NervJS/taro](https://github.com/NervJS/taro) | 7 | 开放式跨端跨框架解决方案，支持使用 React/Vue 等框架来开发微信/京东/百度/支付宝/字节跳动/ QQ 小程序/H5/React Native 等应 |
| [vuejs/pinia](https://github.com/vuejs/pinia) | 6 | 🍍 Intuitive, type safe, light and flexible Store for Vue using the composition |
| [vuejs/awesome-vue](https://github.com/vuejs/awesome-vue) | 6 | 🎉 A curated list of awesome things related to Vue.js |
| [taowen/awesome-lowcode](https://github.com/taowen/awesome-lowcode) | 6 | 国内低代码平台从业者交流 |
| [sveltejs/svelte](https://github.com/sveltejs/svelte) | 6 | web development for the rest of us |
| [strapi/strapi](https://github.com/strapi/strapi) | 6 | 🚀 Strapi is the leading open-source headless CMS. It’s 100% JavaScript/TypeScr |
| [react/react-native](https://github.com/react/react-native) | 6 | A framework for building native applications using React |
| [pmndrs/zustand](https://github.com/pmndrs/zustand) | 6 | 🐻 Bear necessities for state management in React |
| [meteor/meteor](https://github.com/meteor/meteor) | 6 | Meteor, the JavaScript App Platform |
| [lit/lit](https://github.com/lit/lit) | 6 | Lit is a simple library for building fast, lightweight web components. |
| [dcloudio/uni-app](https://github.com/dcloudio/uni-app) | 6 | A cross-platform framework using Vue.js |
| [RubyLouvre/avalon](https://github.com/RubyLouvre/avalon) | 6 | an elegant efficient express mvvm framework |
| [DMQ/mvvm](https://github.com/DMQ/mvvm) | 6 | 剖析vue实现原理，自己动手实现mvvm |

</details>

### 前端 UI 与设计

| 仓库 | 收藏 | 干什么 |
|---|---|---|
| [storybookjs/storybook](https://github.com/storybookjs/storybook) | 12 | Storybook is the industry standard workshop for building, documenting, and tes |
| [ant-design/ant-design](https://github.com/ant-design/ant-design) | 10 | An enterprise-class UI design language and React UI library |
| [ElemeFE/element](https://github.com/ElemeFE/element) | 10 | A Vue.js 2.0 UI Toolkit for Web |
| [ustbhuangyi/better-scroll](https://github.com/ustbhuangyi/better-scroll) | 9 | :scroll: inspired by iscroll, and it supports more features and has a better s |
| [streamich/react-use](https://github.com/streamich/react-use) | 8 | React Hooks — 👍 |
| [rough-stuff/rough](https://github.com/rough-stuff/rough) | 8 | Create graphics with a hand-drawn, sketchy, appearance |
| [nolimits4web/swiper](https://github.com/nolimits4web/swiper) | 8 | Most modern mobile touch slider with hardware accelerated transitions |
| [nilbuild/driver.js](https://github.com/nilbuild/driver.js) | 8 | A lightweight, dependency-free JavaScript library for guiding user focus acros |
| [mui/material-ui](https://github.com/mui/material-ui) | 8 | Material UI: Comprehensive React component library that implements Google's Ma |
| [ianstormtaylor/slate](https://github.com/ianstormtaylor/slate) | 8 | A completely customizable framework for building rich text editors. (Currently |
| [alibaba/formily](https://github.com/alibaba/formily) | 8 | 📱🚀 🧩 Cross Device & High Performance Normal Form/Dynamic(JSON Schema) Form/For |

<details><summary>前端 UI 与设计：其余 18 个（6–7 人收藏）</summary>

| 仓库 | 收藏 | 干什么 |
|---|---|---|
| [youzan/vant](https://github.com/youzan/vant) | 7 | A lightweight, customizable Vue UI library for mobile web apps. |
| [vueuse/vueuse](https://github.com/vueuse/vueuse) | 7 | Collection of essential Vue Composition Utilities for Vue 3 |
| [ueberdosis/tiptap](https://github.com/ueberdosis/tiptap) | 7 | The headless rich text editor framework for web artisans. |
| [tusen-ai/naive-ui](https://github.com/tusen-ai/naive-ui) | 7 | A Vue 3 Component Library. Fairly Complete. Theme Customizable. Uses TypeScrip |
| [shipshapecode/shepherd](https://github.com/shipshapecode/shepherd) | 7 | Guide your users through a tour of your app |
| [chokcoco/iCSS](https://github.com/chokcoco/iCSS) | 7 | 不止于 CSS |
| [bvaughn/react-virtualized](https://github.com/bvaughn/react-virtualized) | 7 | React components for efficiently rendering large lists and tabular data |
| [atlassian/react-beautiful-dnd](https://github.com/atlassian/react-beautiful-dnd) | 7 | Beautiful and accessible drag and drop for lists with React |
| [vuetifyjs/vuetify](https://github.com/vuetifyjs/vuetify) | 6 | 🐉 Vue Component Framework |
| [usablica/intro.js](https://github.com/usablica/intro.js) | 6 | Lightweight, user-friendly onboarding tour library |
| [tailwindlabs/tailwindcss](https://github.com/tailwindlabs/tailwindcss) | 6 | A utility-first CSS framework for rapid UI development. |
| [tailwindlabs/headlessui](https://github.com/tailwindlabs/headlessui) | 6 | Completely unstyled, fully accessible UI components, designed to integrate bea |
| [iview/iview](https://github.com/iview/iview) | 6 | A high quality UI Toolkit built on Vue.js 2.0 |
| [codex-team/editor.js](https://github.com/codex-team/editor.js) | 6 | A block-style editor with clean JSON output |
| [alvarotrigo/fullPage.js](https://github.com/alvarotrigo/fullPage.js) | 6 | fullPage plugin by Alvaro Trigo. Create full screen pages fast and simple |
| [alibaba/hooks](https://github.com/alibaba/hooks) | 6 | A high-quality & reliable React Hooks library.   https://alibaba.github.io/hoo |
| [SortableJS/Vue.Draggable](https://github.com/SortableJS/Vue.Draggable) | 6 | Vue drag-and-drop component based on Sortable.js |
| [AlloyTeam/AlloyFinger](https://github.com/AlloyTeam/AlloyFinger) | 6 | Super tiny size multi-touch gestures library for the web. 　　　You can touch thi |

</details>

### 构建、工程化与调试

| 仓库 | 收藏 | 干什么 |
|---|---|---|
| [puppeteer/puppeteer](https://github.com/puppeteer/puppeteer) | 13 | JavaScript API for Chrome and Firefox |
| [parcel-bundler/parcel](https://github.com/parcel-bundler/parcel) | 11 | The zero configuration build tool for the web. 📦🚀 |
| [google/zx](https://github.com/google/zx) | 11 | A tool for writing better scripts |
| [evanw/esbuild](https://github.com/evanw/esbuild) | 10 | An extremely fast bundler for the web |
| [webpack/webpack](https://github.com/webpack/webpack) | 9 | A bundler for javascript and friends. Packs many modules into a few bundled as |
| [vitejs/vite](https://github.com/vitejs/vite) | 9 | Next generation frontend tooling. It's fast! |
| [swc-project/swc](https://github.com/swc-project/swc) | 9 | Rust-based platform for the Web |
| [microsoft/vscode](https://github.com/microsoft/vscode) | 9 | Visual Studio Code |
| [microsoft/playwright](https://github.com/microsoft/playwright) | 9 | Playwright is a framework for Web Testing and Automation. It allows testing Ch |
| [microsoft/monaco-editor](https://github.com/microsoft/monaco-editor) | 9 | A browser based code editor |
| [liriliri/eruda](https://github.com/liriliri/eruda) | 9 | Console for mobile browsers |
| [jamiebuilds/babel-handbook](https://github.com/jamiebuilds/babel-handbook) | 9 | :blue_book: A guided handbook on how to use Babel and how to create plugins fo |
| [cypress-io/cypress](https://github.com/cypress-io/cypress) | 9 | Fast, easy and reliable testing for anything that runs in a browser. |
| [rrweb-io/rrweb](https://github.com/rrweb-io/rrweb) | 8 | record and replay the web |
| [lerna/lerna](https://github.com/lerna/lerna) | 8 | Lerna is a fast, modern build system for managing and publishing multiple Java |
| [jestjs/jest](https://github.com/jestjs/jest) | 8 | Delightful JavaScript Testing. |
| [electron/electron](https://github.com/electron/electron) | 8 | :electron: Build cross-platform desktop apps with JavaScript, HTML, and CSS |
| [easy-mock/easy-mock](https://github.com/easy-mock/easy-mock) | 8 | A persistent service that generates mock data quickly and provids visualizatio |
| [avwo/whistle](https://github.com/avwo/whistle) | 8 | HTTP, HTTP2, HTTPS, Websocket debugging proxy |
| [SBoudrias/Inquirer.js](https://github.com/SBoudrias/Inquirer.js) | 8 | A collection of common interactive command line user interfaces. |

<details><summary>构建、工程化与调试：其余 28 个（6–7 人收藏）</summary>

| 仓库 | 收藏 | 干什么 |
|---|---|---|
| [vuejs/vuepress](https://github.com/vuejs/vuepress) | 7 | 📝 Minimalistic Vue-powered static site generator |
| [vuejs/vue-cli](https://github.com/vuejs/vue-cli) | 7 | 🛠️ webpack-based tooling for Vue.js Development |
| [vadimdemedes/ink](https://github.com/vadimdemedes/ink) | 7 | 🌈 React for interactive command-line apps |
| [teambit/bit](https://github.com/teambit/bit) | 7 | AI-powered development workspaces with reusable components, architectural clar |
| [microsoft/rushstack](https://github.com/microsoft/rushstack) | 7 | Monorepo for tools developed by the Rush Stack community |
| [meta/jscodeshift](https://github.com/meta/jscodeshift) | 7 | A JavaScript codemod toolkit. |
| [coder/code-server](https://github.com/coder/code-server) | 7 | VS Code in the browser |
| [codemirror/codemirror5](https://github.com/codemirror/codemirror5) | 7 | In-browser code editor (version 5, legacy) |
| [avajs/ava](https://github.com/avajs/ava) | 7 | Node.js test runner that lets you develop with confidence 🚀 |
| [acornjs/acorn](https://github.com/acornjs/acorn) | 7 | A small, fast, JavaScript-based JavaScript parser |
| [FredKSchott/snowpack](https://github.com/FredKSchott/snowpack) | 7 | ESM-powered frontend build tool. Instant, lightweight, unbundled development.  |
| [verdaccio/verdaccio](https://github.com/verdaccio/verdaccio) | 6 | A lightweight Node.js private proxy registry |
| [uncss/uncss](https://github.com/uncss/uncss) | 6 | Remove unused styles from CSS |
| [typicode/json-server](https://github.com/typicode/json-server) | 6 | Get a full fake REST API with zero coding in less than 30 seconds (seriously) |
| [typicode/husky](https://github.com/typicode/husky) | 6 | Git hooks made easy 🐶 woof! |
| [tj/commander.js](https://github.com/tj/commander.js) | 6 | node.js command-line interfaces made easy |
| [rome/tools](https://github.com/rome/tools) | 6 | Unified developer tools for JavaScript, TypeScript, and the web |
| [prettier/prettier](https://github.com/prettier/prettier) | 6 | Prettier is an opinionated code formatter. |
| [postcss/postcss](https://github.com/postcss/postcss) | 6 | Transforming styles with JS plugins |
| [pnpm/pnpm](https://github.com/pnpm/pnpm) | 6 | Fast, disk space efficient package manager |
| [pedronauck/docz](https://github.com/pedronauck/docz) | 6 | ✍ It has never been so easy to document your things! |
| [nwjs/nw.js](https://github.com/nwjs/nw.js) | 6 | Call all Node.js modules directly from DOM/WebWorker and enable a new way of w |
| [mswjs/msw](https://github.com/mswjs/msw) | 6 | The industry standard for API mocking in JavaScript. |
| [meta/docusaurus](https://github.com/meta/docusaurus) | 6 | Easy to maintain open source documentation websites. |
| [gulpjs/gulp](https://github.com/gulpjs/gulp) | 6 | A toolkit to automate & enhance your workflow |
| [ariya/phantomjs](https://github.com/ariya/phantomjs) | 6 | Scriptable Headless Browser |
| [Unitech/pm2](https://github.com/Unitech/pm2) | 6 | Node.js/Typescript/Bun Production Process Manager with a built-in Load Balance |
| [Tencent/vConsole](https://github.com/Tencent/vConsole) | 6 | A lightweight, extendable front-end developer tool for mobile web page. |

</details>

### 语言、运行时与工具库

| 仓库 | 收藏 | 干什么 |
|---|---|---|
| [microsoft/TypeScript](https://github.com/microsoft/TypeScript) | 12 | TypeScript is a superset of JavaScript that compiles to clean JavaScript outpu |
| [type-challenges/type-challenges](https://github.com/type-challenges/type-challenges) | 10 | Collection of TypeScript type challenges with online judge |
| [denoland/deno](https://github.com/denoland/deno) | 10 | A modern runtime for JavaScript and TypeScript. |
| [DefinitelyTyped/DefinitelyTyped](https://github.com/DefinitelyTyped/DefinitelyTyped) | 9 | The repository for high quality TypeScript type definitions. |
| [typicode/lowdb](https://github.com/typicode/lowdb) | 8 | Simple and fast JSON database |
| [airbnb/javascript](https://github.com/airbnb/javascript) | 8 | JavaScript Style Guide |

<details><summary>语言、运行时与工具库：其余 17 个（6–7 人收藏）</summary>

| 仓库 | 收藏 | 干什么 |
|---|---|---|
| [sindresorhus/execa](https://github.com/sindresorhus/execa) | 7 | Process execution for humans |
| [lovell/sharp](https://github.com/lovell/sharp) | 7 | High performance Node.js image processing, the fastest module to resize JPEG,  |
| [localForage/localForage](https://github.com/localForage/localForage) | 7 | 💾 Offline storage, improved. Wraps IndexedDB, WebSQL, or localStorage using a  |
| [immerjs/immer](https://github.com/immerjs/immer) | 7 | Create the next immutable state by mutating the current one |
| [hapijs/joi](https://github.com/hapijs/joi) | 7 | The most powerful data validation library for JS |
| [cheeriojs/cheerio](https://github.com/cheeriojs/cheerio) | 7 | The fast, flexible, and elegant library for parsing and manipulating HTML and  |
| [ai/nanoid](https://github.com/ai/nanoid) | 7 | A tiny (118 bytes), secure, URL-friendly, unique string ID generator for JavaS |
| [zenorocha/clipboard.js](https://github.com/zenorocha/clipboard.js) | 6 | :scissors: Modern copy to clipboard. No Flash. Just 3kb gzipped :clipboard: |
| [snabbdom/snabbdom](https://github.com/snabbdom/snabbdom) | 6 | A virtual DOM library with focus on simplicity, modularity, powerful features  |
| [sindresorhus/ora](https://github.com/sindresorhus/ora) | 6 | Elegant terminal spinner |
| [shelljs/shelljs](https://github.com/shelljs/shelljs) | 6 | :shell: Portable Unix shell commands for Node.js |
| [rust-lang/rust](https://github.com/rust-lang/rust) | 6 | Empowering everyone to build reliable and efficient software. |
| [nodejs/node](https://github.com/nodejs/node) | 6 | Node.js JavaScript runtime ✨🐢🚀✨ |
| [eligrey/FileSaver.js](https://github.com/eligrey/FileSaver.js) | 6 | An HTML5 saveAs() FileSaver implementation |
| [colinhacks/zod](https://github.com/colinhacks/zod) | 6 | TypeScript-first schema validation with static type inference |
| [automerge/automerge-classic](https://github.com/automerge/automerge-classic) | 6 | A JSON-like data structure (a CRDT) that can be modified concurrently by diffe |
| [Matt-Esch/virtual-dom](https://github.com/Matt-Esch/virtual-dom) | 6 | A Virtual DOM and diffing algorithm |

</details>

### 可视化、动效与网页能力

| 仓库 | 收藏 | 干什么 |
|---|---|---|
| [slidevjs/slidev](https://github.com/slidevjs/slidev) | 13 | Presentation Slides for Developers |
| [animate-css/animate.css](https://github.com/animate-css/animate.css) | 13 | 🍿 A cross-browser library of CSS animations. As easy to use as an easy thing. |
| [hakimel/reveal.js](https://github.com/hakimel/reveal.js) | 10 | The HTML Presentation Framework |
| [apache/echarts](https://github.com/apache/echarts) | 10 | Apache ECharts is a powerful, interactive charting and data visualization libr |
| [tsayen/dom-to-image](https://github.com/tsayen/dom-to-image) | 9 | Generates an image from a DOM node using HTML5 canvas |
| [mrdoob/three.js](https://github.com/mrdoob/three.js) | 9 | JavaScript 3D Library. |
| [juliangarnier/anime](https://github.com/juliangarnier/anime) | 9 | JavaScript animation engine |
| [d3/d3](https://github.com/d3/d3) | 9 | Bring data to life with SVG, Canvas and HTML. :bar_chart::chart_with_upwards_t |
| [pixijs/pixijs](https://github.com/pixijs/pixijs) | 8 | The HTML5 Creation Engine: Create beautiful digital content with the fastest,  |
| [mermaid-js/mermaid](https://github.com/mermaid-js/mermaid) | 8 | Generation of diagrams like flowcharts or sequence diagrams from text in a sim |
| [ksky521/nodeppt](https://github.com/ksky521/nodeppt) | 8 | This is probably the best web presentation tool so far! |
| [carbon-app/carbon](https://github.com/carbon-app/carbon) | 8 | :black_heart: Create and share beautiful images of your source code |

<details><summary>可视化、动效与网页能力：其余 15 个（6–7 人收藏）</summary>

| 仓库 | 收藏 | 干什么 |
|---|---|---|
| [tldraw/tldraw](https://github.com/tldraw/tldraw) | 7 | Build infinite canvas apps in React with the tldraw SDK. World's best, top-mos |
| [pmndrs/react-spring](https://github.com/pmndrs/react-spring) | 7 | ✌️ A spring physics based React animation library |
| [phaserjs/phaser](https://github.com/phaserjs/phaser) | 7 | Phaser is a fun, free and fast 2D game framework for making HTML5 games for de |
| [niklasvh/html2canvas](https://github.com/niklasvh/html2canvas) | 7 | Screenshots with JavaScript |
| [jxnblk/mdx-deck](https://github.com/jxnblk/mdx-deck) | 7 | ♠️ React MDX-based presentation decks |
| [excalidraw/excalidraw](https://github.com/excalidraw/excalidraw) | 7 | Virtual whiteboard for sketching hand-drawn like diagrams |
| [Tonejs/Tone.js](https://github.com/Tonejs/Tone.js) | 7 | A Web Audio framework for making interactive music in the browser. |
| [tweenjs/tween.js](https://github.com/tweenjs/tween.js) | 6 | JavaScript/TypeScript animation engine |
| [myliang/x-spreadsheet](https://github.com/myliang/x-spreadsheet) | 6 | The project has been migrated to @wolf-table/table https://github.com/wolf-tab |
| [latentcat/qrbtf](https://github.com/latentcat/qrbtf) | 6 | AI & parametric QR code generator. AI & 参数化二维码生成器。https://qrbtf.com |
| [konvajs/konva](https://github.com/konvajs/konva) | 6 | Konva.js is an HTML5 Canvas JavaScript framework for interactive graphics, des |
| [Popmotion/popmotion](https://github.com/Popmotion/popmotion) | 6 | Simple animation libraries for delightful user interfaces |
| [GoogleChromeLabs/quicklink](https://github.com/GoogleChromeLabs/quicklink) | 6 | ⚡️Faster subsequent page-loads by prefetching in-viewport links during idle ti |
| [GoogleChromeLabs/comlink](https://github.com/GoogleChromeLabs/comlink) | 6 | Comlink makes WebWorkers enjoyable. |
| [GoogleChrome/workbox](https://github.com/GoogleChrome/workbox) | 6 | 📦 Workbox: JavaScript libraries for Progressive Web Apps |

</details>

### 请求与内容处理

| 仓库 | 收藏 | 干什么 |
|---|---|---|
| [modood/Administrative-divisions-of-China](https://github.com/modood/Administrative-divisions-of-China) | 9 | 中华人民共和国行政区划：省级（省份）、 地级（城市）、 县级（区县）、 乡级（乡镇街道）、 村级（村委会居委会） ，中国省市区镇村二级三级四级五级联动地址数 |
| [markedjs/marked](https://github.com/markedjs/marked) | 9 | A markdown parser and compiler. Built for speed. |
| [iamkun/dayjs](https://github.com/iamkun/dayjs) | 9 | ⏰ Day.js 2kB immutable date-time library alternative to Moment.js with the sam |
| [axios/axios](https://github.com/axios/axios) | 9 | Promise based HTTP client for the browser and node.js |
| [chinese-poetry/chinese-poetry](https://github.com/chinese-poetry/chinese-poetry) | 8 | The most comprehensive database of Chinese poetry 🧶最全中华古诗词数据库,  唐宋两朝近一万四千古诗人,  |

<details><summary>请求与内容处理：其余 3 个（6–7 人收藏）</summary>

| 仓库 | 收藏 | 干什么 |
|---|---|---|
| [mixmark-io/turndown](https://github.com/mixmark-io/turndown) | 6 | 🛏 An HTML to Markdown converter written in JavaScript |
| [markdown-it/markdown-it](https://github.com/markdown-it/markdown-it) | 6 | Markdown parser, done right. 100% CommonMark support, extensions, syntax plugi |
| [highlightjs/highlight.js](https://github.com/highlightjs/highlight.js) | 6 | JavaScript syntax highlighter with language auto-detection and zero dependenci |

</details>

### 算法与面试

| 仓库 | 收藏 | 干什么 |
|---|---|---|
| [Advanced-Frontend/Daily-Interview-Question](https://github.com/Advanced-Frontend/Daily-Interview-Question) | 10 | 我是依扬（木易杨），公众号「高级前端进阶」作者，每天搞定一道前端大厂面试题，祝大家天天进步，一年后会看到不一样的自己。 |
| [trekhleb/javascript-algorithms](https://github.com/trekhleb/javascript-algorithms) | 9 | 📝 Algorithms and data structures implemented in JavaScript with explanations a |
| [haizlin/fe-interview](https://github.com/haizlin/fe-interview) | 8 | 前端面试每日 3+1，以面试题来驱动学习，提倡每日学习与思考，每天进步一点！每天早上5点纯手工发布面试题（死磕自己，愉悦大家），6000+道前端面试题全面覆 |
| [MisterBooo/LeetCodeAnimation](https://github.com/MisterBooo/LeetCodeAnimation) | 8 | Demonstrate all the questions on LeetCode in the form of animation.（用动画的形式呈现解L |
| [ElemeFE/node-interview](https://github.com/ElemeFE/node-interview) | 8 | How to pass the Node.js interview of ElemeFE. |

<details><summary>算法与面试：其余 8 个（6–7 人收藏）</summary>

| 仓库 | 收藏 | 干什么 |
|---|---|---|
| [yangshun/front-end-interview-handbook](https://github.com/yangshun/front-end-interview-handbook) | 7 | Front End interview preparation materials for busy engineers (updated for 2026 |
| [jwasham/coding-interview-university](https://github.com/jwasham/coding-interview-university) | 7 | A complete computer science study plan to become a software engineer. |
| [h5bp/Front-end-Developer-Interview-Questions](https://github.com/h5bp/Front-end-Developer-Interview-Questions) | 7 | A list of helpful front-end related questions you can use to interview potenti |
| [algorithm-visualizer/algorithm-visualizer](https://github.com/algorithm-visualizer/algorithm-visualizer) | 7 | :fireworks:Interactive Online Platform that Visualizes Algorithms from Code |
| [yangshun/tech-interview-handbook](https://github.com/yangshun/tech-interview-handbook) | 6 | Curated coding interview preparation materials for busy software engineers |
| [sudheerj/reactjs-interview-questions](https://github.com/sudheerj/reactjs-interview-questions) | 6 | List of top 500 ReactJS Interview Questions & Answers....Coding exercise quest |
| [azl397985856/leetcode](https://github.com/azl397985856/leetcode) | 6 | LeetCode Solutions: A Record of My Problem Solving Journey.( leetcode题解，记录自己的l |
| [azl397985856/fe-interview](https://github.com/azl397985856/fe-interview) | 6 | 宇宙最强的前端面试指南 (https://lucifer.ren/fe-interview) |

</details>

### 学习资源与社区共识

| 仓库 | 收藏 | 干什么 |
|---|---|---|
| [fouber/blog](https://github.com/fouber/blog) | 12 | 没事写写文章，喜欢的话请点star，想订阅点watch，千万别fork！ |
| [goldbergyoni/nodebestpractices](https://github.com/goldbergyoni/nodebestpractices) | 11 | ✅ The Node.js best practices list (July 2026) |
| [getify/You-Dont-Know-JS](https://github.com/getify/You-Dont-Know-JS) | 11 | A book series (2 published editions) on the JS language. |
| [codecrafters-io/build-your-own-x](https://github.com/codecrafters-io/build-your-own-x) | 10 | Master programming by recreating your favorite technologies from scratch. |
| [ascoders/weekly](https://github.com/ascoders/weekly) | 10 | 前端精读周刊。帮你理解最前沿、实用的技术。 |
| [Chalarangelo/30-seconds-of-code](https://github.com/Chalarangelo/30-seconds-of-code) | 10 | Coding articles to level up your development skills |
| [mqyqingfeng/Blog](https://github.com/mqyqingfeng/Blog) | 9 | 冴羽写博客的地方，预计写四个系列：JavaScript深入系列、JavaScript专题系列、ES6系列、React系列。 |
| [justjavac/free-programming-books-zh_CN](https://github.com/justjavac/free-programming-books-zh_CN) | 9 | :books: 免费的计算机编程类中文书籍，欢迎投稿 |
| [answershuto/learnVue](https://github.com/answershuto/learnVue) | 9 | :octocat:Vue.js 源码解析 |
| [521xueweihan/HelloGitHub](https://github.com/521xueweihan/HelloGitHub) | 9 | :octocat: 分享 GitHub 上有趣、入门级的开源项目。Share interesting, entry-level open source pr |
| [sindresorhus/awesome](https://github.com/sindresorhus/awesome) | 8 | 😎 Awesome lists about all kinds of interesting topics [NOTE: Pull requests are |
| [nilbuild/developer-roadmap](https://github.com/nilbuild/developer-roadmap) | 8 | Interactive roadmaps, guides and other educational content to help developers  |
| [996icu/996.ICU](https://github.com/996icu/996.ICU) | 8 | Repo for counting stars and contributing. Press F to pay respect to glorious d |

<details><summary>学习资源与社区共识：其余 28 个（6–7 人收藏）</summary>

| 仓库 | 收藏 | 干什么 |
|---|---|---|
| [xitu/gold-miner](https://github.com/xitu/gold-miner) | 7 | 🥇掘金翻译计划，可能是世界最大最好的英译中技术社区，最懂读者和译者的翻译平台： |
| [ustbhuangyi/vue-analysis](https://github.com/ustbhuangyi/vue-analysis) | 7 | :thumbsup: Vue.js 源码分析 |
| [ruanyf/jstraining](https://github.com/ruanyf/jstraining) | 7 | 全栈工程师培训材料 |
| [amfe/article](https://github.com/amfe/article) | 7 | — |
| [EbookFoundation/free-programming-books](https://github.com/EbookFoundation/free-programming-books) | 7 | :books: Freely available programming books |
| [zenany/weekly](https://github.com/zenany/weekly) | 6 | 汇总平时看到的好文章... |
| [yygmind/blog](https://github.com/yygmind/blog) | 6 | 我是木易杨，公众号「高级前端进阶」作者，跟着我每周重点攻克一个前端面试重难点。接下来让我带你走进高级前端的世界，在进阶的路上，共勉！ |
| [youngwind/blog](https://github.com/youngwind/blog) | 6 | 梁少峰的个人博客 |
| [yeasy/docker_practice](https://github.com/yeasy/docker_practice) | 6 | 最新Docker容器技术，从真实案例中学习最佳实践！| Learn and understand Docker&Container technologies |
| [stephentian/33-js-concepts](https://github.com/stephentian/33-js-concepts) | 6 | :scroll: 每个 JavaScript 工程师都应懂的33个概念 @leonardomso |
| [shengxinjing/programmer-job-blacklist](https://github.com/shengxinjing/programmer-job-blacklist) | 6 | :see_no_evil:程序员找工作黑名单，换工作和当技术合伙人需谨慎啊 更新有赞 |
| [ruanyf/weekly](https://github.com/ruanyf/weekly) | 6 | 科技爱好者周刊，每周五发布 |
| [ruanyf/free-books](https://github.com/ruanyf/free-books) | 6 | 互联网上的免费书籍 |
| [ruanyf/es6tutorial](https://github.com/ruanyf/es6tutorial) | 6 | 《ECMAScript 6入门》是一本开源的 JavaScript 语言教程，全面介绍 ECMAScript 6 新增的语法特性。 |
| [livoras/blog](https://github.com/livoras/blog) | 6 | Too young, too simple. Sometimes, naive. |
| [k88hudson/git-flight-rules](https://github.com/k88hudson/git-flight-rules) | 6 | Flight rules for git |
| [jkchao/typescript-book-chinese](https://github.com/jkchao/typescript-book-chinese) | 6 | TypeScript Deep Dive 中文版  |
| [jamiebuilds/the-super-tiny-compiler](https://github.com/jamiebuilds/the-super-tiny-compiler) | 6 | :snowman: Possibly the smallest compiler ever |
| [easychen/howto-make-more-money](https://github.com/easychen/howto-make-more-money) | 6 | 程序员如何优雅的挣零花钱，2.0版，升级为小书了。Most of this not work outside China , so no English t |
| [doodlewind/jshistory-cn](https://github.com/doodlewind/jshistory-cn) | 6 | 🇨🇳 《JavaScript 二十年》中文版 |
| [donnemartin/system-design-primer](https://github.com/donnemartin/system-design-primer) | 6 | Learn how to design large-scale systems. Prep for the system design interview. |
| [coder2gwy/coder2gwy](https://github.com/coder2gwy/coder2gwy) | 6 | 互联网首份程序员考公指南，由3位已经进入体制内的前大厂程序员联合献上。 |
| [byoungd/up](https://github.com/byoungd/up) | 6 | 韩先凯的人生进阶指南 AI时代 中英双语终身学习指南：AI、学习 、创业、财富、爱情与人生 |
| [MostlyAdequate/mostly-adequate-guide](https://github.com/MostlyAdequate/mostly-adequate-guide) | 6 | Mostly adequate guide to FP (in javascript) |
| [InterviewMap/CS-Interview-Knowledge-Map](https://github.com/InterviewMap/CS-Interview-Knowledge-Map) | 6 | Build the best interview map. The current content includes JS, network, browse |
| [HcySunYang/vue-design](https://github.com/HcySunYang/vue-design) | 6 | 📖 master分支：《渲染器》 |
| [CyC2018/CS-Notes](https://github.com/CyC2018/CS-Notes) | 6 | :books: 技术面试必备基础知识、Leetcode、计算机操作系统、计算机网络、系统设计 |
| [BetaSu/just-react](https://github.com/BetaSu/just-react) | 6 | 「React技术揭秘」  一本自顶向下的React源码分析书 |

</details>

### 杂项工具

| 仓库 | 收藏 | 干什么 |
|---|---|---|
| [public-apis/public-apis](https://github.com/public-apis/public-apis) | 8 | A collective list of free APIs |
| [ohmyzsh/ohmyzsh](https://github.com/ohmyzsh/ohmyzsh) | 8 | 🙃   A delightful community-driven (with 2,500+ contributors) framework for man |
| [MustangYM/WeChatExtension-ForMac](https://github.com/MustangYM/WeChatExtension-ForMac) | 8 | A plugin for Mac WeChat |
| [Binaryify/NeteaseCloudMusicApi](https://github.com/Binaryify/NeteaseCloudMusicApi) | 8 | 网易云音乐 Node.js API service |

<details><summary>杂项工具：其余 8 个（6–7 人收藏）</summary>

| 仓库 | 收藏 | 干什么 |
|---|---|---|
| [wechaty/wechaty](https://github.com/wechaty/wechaty) | 7 | Conversational RPA SDK for Chatbot Makers. Join our Discord: https://discord.g |
| [jaywcjlove/awesome-mac](https://github.com/jaywcjlove/awesome-mac) | 7 |  This project is dedicated to collecting high-quality macOS software and orga |
| [iina/iina](https://github.com/iina/iina) | 7 | The modern video player for macOS. |
| [hzlzh/Best-App](https://github.com/hzlzh/Best-App) | 7 | 收集&推荐优秀的 Apps/硬件/技巧/周边等 |
| [houshanren/hangzhou_house_knowledge](https://github.com/houshanren/hangzhou_house_knowledge) | 7 | 2017年买房经历总结出来的买房购房知识分享给大家，希望对大家有所帮助。买房不易，且买且珍惜。Sharing the knowledge of buy an |
| [DIYgod/RSSHub](https://github.com/DIYgod/RSSHub) | 7 | 🧡 Everything is RSSible |
| [phobal/ivideo](https://github.com/phobal/ivideo) | 6 | 一个可以观看国内主流视频平台所有视频的客户端（Mac、Windows、Linux） A client that can watch video of dom |
| [TKkk-iOSer/WeChatPlugin-MacOS](https://github.com/TKkk-iOSer/WeChatPlugin-MacOS) | 6 | 微信小助手 |

</details>

### 杂项（GitHub 本身）

| 仓库 | 收藏 | 干什么 |
|---|---|---|
| [anuraghazra/github-readme-stats](https://github.com/anuraghazra/github-readme-stats) | 9 | :zap: Dynamically generated stats for your github readmes |

<details><summary>杂项（GitHub 本身）：其余 1 个（6–7 人收藏）</summary>

| 仓库 | 收藏 | 干什么 |
|---|---|---|
| [tipsy/profile-summary-for-github](https://github.com/tipsy/profile-summary-for-github) | 7 | Tool for visualizing GitHub profiles |

</details>

### 跨端与移动

| 仓库 | 收藏 | 干什么 |
|---|---|---|
| [flutter/flutter](https://github.com/flutter/flutter) | 9 | Flutter makes it easy and fast to build beautiful apps for mobile and beyond |

**怎么用**：选库/选框架前先查它在这里的位置。
- ≥8 人 → 圈内公认，放心用；
- 6–7 人 → 有人用在真实项目里，但不是必需品；
- **不在这 239 个里 → 关注的人都还没用它。** 这时别只看 star 总数，看最近半年有没有发版、开 issue 的痛点是啥。
- 我的收藏和这份名单重合度很高（146 个 star 里 86 个被 ≥5 人收藏），说明品味没问题，缺的只是「按主线收」。

---

## 四、我的收藏（146 个 star 都是干什么用的）

> **146 个 star 按用途归类。** 概括：一半是 AI 应用层工具，一半是前端工程化的底子，剩下是理财/副业/生活的零散收藏。

| 类别 | 数量 | 这块在收什么 |
|---|---|---|
| AI / Agent 工程 | 31 | 收藏最集中的一块，注意力确实押在 AI 应用层 |
| AI 视觉与音视频 | 11 | AIGC 内容生产的整套开源工具 |
| 视频与字幕工具 | 7 | 下载 / 转录 / 出片，跟自媒体工作流直接相关 |
| 内容发布 / 订阅 / 捕获 | 11 | 一次写好、多渠道发 |
| 自建服务 / 运维 | 15 | NAS、WAF、监控、DNS、自动任务 |
| 前端 / 后端框架与模板 | 16 | 起新项目先从这里挑，别自己搭 |
| 监控 / 工程化 | 3 | 埋点 / 错误 / 性能监控，能直接抄结构 |
| 学习 / 面试 / 方法论 | 30 | 怎么学、怎么想，长期价值类 |
| 理财 / 生活 / 杂项 | 17 | 房产、副业、账单、法律 |
| 我的仓库 | 5 | 自己的，星数还很低 |

### AI / Agent 工程（31 个）

| 仓库 | 星 | 干什么 |
|---|---|---|
| [paperclipai/paperclip](https://github.com/paperclipai/paperclip) | 113310 | The open-source app everyone uses to manage agents at work |
| [Panniantong/Agent-Reach](https://github.com/Panniantong/Agent-Reach) | 111250 | Give your AI agent eyes to see the entire internet. Read & search Twit |
| [infiniflow/ragflow](https://github.com/infiniflow/ragflow) | 94084 | RAGFlow is an agent-native database: a Retrieval-Augmented Generation  |
| [OpenHands/OpenHands](https://github.com/OpenHands/OpenHands) | 93318 | 🙌 OpenHands: AI-Driven Development |
| [ChatGPTNextWeb/NextChat](https://github.com/ChatGPTNextWeb/NextChat) | 88946 | ✨ Zero-config AI chat assistant. No API key needed — sign up and insta |
| [openai/openai-cookbook](https://github.com/openai/openai-cookbook) | 77059 | Examples and guides for using the OpenAI API |
| [gsd-build/get-shit-done](https://github.com/gsd-build/get-shit-done) | 64151 | A light-weight and powerful meta-prompting, context engineering and sp |
| [zhayujie/CowAgent](https://github.com/zhayujie/CowAgent) | 47894 | Open-source personal AI assistant & Agent Harness. Plans tasks, runs t |
| [TabbyML/tabby](https://github.com/TabbyML/tabby) | 33935 | Self-hosted AI coding assistant |
| [lbjlaq/Antigravity-Manager](https://github.com/lbjlaq/Antigravity-Manager) | 33016 | Professional Antigravity Account Manager & Switcher. One-click seamles |
| [datawhalechina/llm-cookbook](https://github.com/datawhalechina/llm-cookbook) | 24890 | 面向开发者的 LLM 入门教程，吴恩达大模型系列课程中文版 |
| [1Panel-dev/MaxKB](https://github.com/1Panel-dev/MaxKB) | 23150 | 🔥 MaxKB is an open-source platform for building enterprise-grade agent |
| [LiLittleCat/awesome-free-chatgpt](https://github.com/LiLittleCat/awesome-free-chatgpt) | 21357 | 🆓免费的 ChatGPT 镜像网站列表，持续更新。List of free ChatGPT mirror sites, continuous |
| [eosphoros-ai/DB-GPT](https://github.com/eosphoros-ai/DB-GPT) | 20288 | open-source agentic AI data assistant for the next generation of AI +  |
| [transitive-bullshit/agentic](https://github.com/transitive-bullshit/agentic) | 18081 | Your API ⇒ Paid MCP. Instantly. |
| [ConardLi/garden-skills](https://github.com/ConardLi/garden-skills) | 15012 | ConardLi's open-source Skills collection, featuring web design, knowle |
| [hexclave/hexclave](https://github.com/hexclave/hexclave) | 6891 | The user infrastructure platform. You choose the frontend, backend, an |
| [lvwzhen/law-cn-ai](https://github.com/lvwzhen/law-cn-ai) | 4914 | ⚖️ AI 法律助手 |
| [Ikaros-521/AI-Vtuber](https://github.com/Ikaros-521/AI-Vtuber) | 4615 | AI Vtuber是一个由 【ChatterBot/ChatGPT/claude/langchain/chatglm/text-gen-we |
| [AmintaCCCP/GithubStarsManager](https://github.com/AmintaCCCP/GithubStarsManager) | 3864 | AI-powered GitHub stars manager with semantic search, auto-categorizat |
| [TigerResearch/TigerBot](https://github.com/TigerResearch/TigerBot) | 2259 | TigerBot: A multi-language multi-task LLM |
| [BidingCC/BuildingAI](https://github.com/BidingCC/BuildingAI) | 1931 | AI时代的WordPress，东半球首个积木式AI应用搭建系统，人人都可免费搭建自己的AI应用系统，例如企业智能体系统、AI漫剧系统、AI论 |
| [cfour-hi/gitstars](https://github.com/cfour-hi/gitstars) | 1802 | Github Starred Repositories Manager |
| [codeacme17/examor](https://github.com/codeacme17/examor) | 1070 | For students, scholars, interviewees and lifelong learners. Let LLMs a |
| [browser-use/agent-sdk](https://github.com/browser-use/agent-sdk) | 685 | — |
| [kxxt/chatgpt-action](https://github.com/kxxt/chatgpt-action) | 683 | Let ChatGPT review PRs for you |
| [krisyangdev/ChatLLM-Web](https://github.com/krisyangdev/ChatLLM-Web) | 641 | Private local model studio, AI chat, and agent workspace powered by We |
| [l0ng-ai/papr](https://github.com/l0ng-ai/papr) | 591 | A fast, native RSS reader — plus an agent-facing CLI so your AI agent  |
| [IamLiuLv/compoder](https://github.com/IamLiuLv/compoder) | 287 | Compoder is an open-source AI-powered component code generation engine |
| [CH563/gpts-url](https://github.com/CH563/gpts-url) | 163 | ChatGPT GPTs Store, use Astro + Taiwindcss, and crawl the 6,876 GPTs S |
| [302ai/302-Dev-Kit](https://github.com/302ai/302-Dev-Kit) | 151 | The starting template for all our AI Apps |

### AI 视觉与音视频（11 个）

| 仓库 | 星 | 干什么 |
|---|---|---|
| [abi/screenshot-to-code](https://github.com/abi/screenshot-to-code) | 81174 | Drop in a screenshot and convert it to clean code (HTML/Tailwind/React |
| [photoprism/photoprism](https://github.com/photoprism/photoprism) | 40442 | AI-Powered Photos App 🌈💎✨ |
| [suno-ai/bark](https://github.com/suno-ai/bark) | 39357 | 🔊 Text-Prompted Generative Audio Model |
| [WEIFENG2333/VideoCaptioner](https://github.com/WEIFENG2333/VideoCaptioner) | 16510 | 🎬 卡卡字幕助手 ／ VideoCaptioner - 基于 LLM 的智能字幕助手 - 视频字幕生成、断句、校正、字幕翻译全流程处理！-  |
| [web-infra-dev/midscene](https://github.com/web-infra-dev/midscene) | 15595 | See interfaces like a human. E2E testing in natural language. |
| [instantX-research/InstantID](https://github.com/instantX-research/InstantID) | 11995 | InstantID: Zero-shot Identity-Preserving Generation in Seconds 🔥 |
| [wiltodelta/remove-ai-watermarks](https://github.com/wiltodelta/remove-ai-watermarks) | 6358 | Remove visible and invisible AI watermarks from images and video, and  |
| [lxfater/inpaint-web](https://github.com/lxfater/inpaint-web) | 6129 | A free and open-source inpainting & image-upscaling tool powered by we |
| [6174/comflowyspace](https://github.com/6174/comflowyspace) | 2343 | Comflowyspace is an intuitive, user-friendly, open-source AI tool for  |
| [antfu/qrcode-toolkit](https://github.com/antfu/qrcode-toolkit) | 1262 | Anthony's QR Code Toolkit for AI generated QR Codes |
| [2234839/silkpulse](https://github.com/2234839/silkpulse) | 242 | silkpulse 是一个 AI 原生的远程设备调试器：让 AI agent 直接查看、诊断、操作 运行在远程设备上的网页——线上 H5、移 |

### 视频与字幕工具（7 个）

| 仓库 | 星 | 干什么 |
|---|---|---|
| [webadderallorg/Recordly](https://github.com/webadderallorg/Recordly) | 36574 | Create polished demo videos without editing skills. Mac/Windows/Linux |
| [leandromoreira/digital_video_introduction](https://github.com/leandromoreira/digital_video_introduction) | 16386 | A hands-on introduction to video technology: image, video, codec (av1, |
| [nexmoe/VidBee](https://github.com/nexmoe/VidBee) | 11129 | Download video and audio from 1000+ sites, transcribe locally with spe |
| [xtyxtyx/sorry](https://github.com/xtyxtyx/sorry) | 6403 | 在线制作`sorry 为所欲为`的gif |
| [BilibiliVideoDownload/BilibiliVideoDownload](https://github.com/BilibiliVideoDownload/BilibiliVideoDownload) | 3544 | Cross-platform download bilibili video desktop software, support windo |
| [wendy7756/AI-Video-Transcriber](https://github.com/wendy7756/AI-Video-Transcriber) | 3411 | Transcribe and summarize videos and podcasts using AI. Open-source, mu |
| [gkajs/gka](https://github.com/gkajs/gka) | 2113 | 一款高效、高性能的帧动画生成工具 |

### 内容发布 / 订阅 / 捕获（11 个）

| 仓库 | 星 | 干什么 |
|---|---|---|
| [usememos/memos](https://github.com/usememos/memos) | 64418 | Memos is an open-source, self-hosted note-taking app that brings your  |
| [slidevjs/slidev](https://github.com/slidevjs/slidev) | 49446 | Presentation Slides for Developers |
| [The-Vibe-Company/quivr](https://github.com/The-Vibe-Company/quivr) | 39644 | An open-source engine that turns continuous content streams into searc |
| [omnivore-app/omnivore](https://github.com/omnivore-app/omnivore) | 16415 | Omnivore is a complete, open source read-it-later solution for people  |
| [wechatsync/Wechatsync](https://github.com/wechatsync/Wechatsync) | 6612 | 一键同步文章到多个内容平台，支持今日头条、WordPress、知乎、简书、掘金、CSDN、typecho各大平台，一次发布，多平台同步发布。 |
| [scriptscat/scriptcat](https://github.com/scriptscat/scriptcat) | 5859 | ScriptCat, a browser extension that can execute userscript; 脚本猫，一个可以执行 |
| [leaperone/MultiPost-Extension](https://github.com/leaperone/MultiPost-Extension) | 3909 | A browser extension that helps users publish content to multiple socia |
| [blossom-editor/blossom](https://github.com/blossom-editor/blossom) | 3800 | A markdown editor that you can deploy on your own servers to achieve c |
| [anc95/writely](https://github.com/anc95/writely) | 1294 | ❤️‍🔥 A chrome extension as an alternative to Notion AI that goes beyon |
| [Zebartin/autoxjs-scripts](https://github.com/Zebartin/autoxjs-scripts) | 312 | 一些自用的autox.js脚本 |
| [cmdch2017/GenerateAndAutoupload](https://github.com/cmdch2017/GenerateAndAutoupload) | 106 | 界面化批量上传视频抖音、bilibili、腾讯，及文字生成文字视频功能 |

### 自建服务 / 运维（15 个）

| 仓库 | 星 | 干什么 |
|---|---|---|
| [Genymobile/scrcpy](https://github.com/Genymobile/scrcpy) | 154652 | Display and control your Android device |
| [AdguardTeam/AdGuardHome](https://github.com/AdguardTeam/AdGuardHome) | 38389 | Network-wide ads & trackers blocking DNS server |
| [IceWhaleTech/CasaOS](https://github.com/IceWhaleTech/CasaOS) | 37636 | CasaOS - A simple, easy-to-use, elegant open-source Personal Cloud sys |
| [dubinc/dub.link](https://github.com/dubinc/dub.link) | 25158 | The modern link attribution platform. Loved by world-class engineering |
| [chaitin/SafeLine](https://github.com/chaitin/SafeLine) | 23259 | SafeLine is a self-hosted WAF(Web Application Firewall) / reverse prox |
| [rybbit-io/rybbit](https://github.com/rybbit-io/rybbit) | 13288 | 🐸 Rybbit - open-source and privacy-friendly alternative to Google Anal |
| [highlight/highlight](https://github.com/highlight/highlight) | 9390 | highlight.io: The open source, full-stack monitoring platform. Error m |
| [RayWangQvQ/BiliBiliToolPro](https://github.com/RayWangQvQ/BiliBiliToolPro) | 9215 | B 站（bilibili）自动任务工具，支持docker、青龙、k8s等多种部署方式。全面拥抱AI。敏感肌也能用。 |
| [WECENG/ticket-purchase](https://github.com/WECENG/ticket-purchase) | 7508 | 大麦自动抢票，支持人员、城市、日期场次、价格选择 |
| [msgbyte/tianji](https://github.com/msgbyte/tianji) | 3119 | Tianji: Insight into everything, Website Analytics + Uptime Monitor +  |
| [opennaslab/kubespider](https://github.com/opennaslab/kubespider) | 2190 | A global resource download orchestration system, build your home downl |
| [beilunyang/moepush](https://github.com/beilunyang/moepush) | 1370 | 一个基于 NextJS + Cloudflare 技术栈构建的可爱消息推送服务, 支持多种消息推送渠道✨ |
| [besscroft/PicImpact](https://github.com/besscroft/PicImpact) | 1320 | 自部署的摄影作品网站，支持多种功能特性。PicImpact，分享你和世界！ |
| [amikey/12306](https://github.com/amikey/12306) | 99 | https://github.com/testerSunshine/12306.git |
| [easyshell-ai/easyshell](https://github.com/easyshell-ai/easyshell) | 80 | Lightweight server management & intelligent ops platform with Docker o |

### 前端 / 后端框架与模板（16 个）

| 仓库 | 星 | 干什么 |
|---|---|---|
| [vuejs/vue](https://github.com/vuejs/vue) | 212528 | This is the repo for Vue 2. For Vue 3, go to https://github.com/vuejs/ |
| [vitejs/vite](https://github.com/vitejs/vite) | 83886 | Next generation frontend tooling. It's fast! |
| [streamich/react-use](https://github.com/streamich/react-use) | 43978 | React Hooks — 👍 |
| [vuejs/devtools-v6](https://github.com/vuejs/devtools-v6) | 24651 | ⚙️ Browser devtools extension for debugging Vue.js applications. |
| [alibaba/flutter-go](https://github.com/alibaba/flutter-go) | 23616 | flutter 开发者帮助 APP，包含 flutter 常用 140+ 组件的demo 演示与中文文档 |
| [vueComponent/ant-design-vue](https://github.com/vueComponent/ant-design-vue) | 21712 | 🌈  An enterprise-class UI components based on Ant Design and Vue. 🐜 |
| [supertokens/supertokens-core](https://github.com/supertokens/supertokens-core) | 15345 | Open source alternative to Auth0 / Firebase Auth / AWS Cognito |
| [cool-team-official/cool-admin-midway](https://github.com/cool-team-official/cool-admin-midway) | 3286 | 🔥 cool-admin(midway版)一个很酷的后台权限管理框架，Ai编码、流程编排、模块化、插件化、CRUD极速开发，永久开源免费，基 |
| [codercup/unibest](https://github.com/codercup/unibest) | 2864 | unibest - 最好用的 uniapp 开发框架。unibest 是由 uniapp + Vue3 + Ts + Vite4 + Uno |
| [livoras/simple-virtual-dom](https://github.com/livoras/simple-virtual-dom) | 1718 | Basic virtual-dom algorithm |
| [BoBoooooo/Element-Pro-Crud](https://github.com/BoBoooooo/Element-Pro-Crud) | 254 | 🚀 LowCode平台,配套表单,表格设计器,一键Crud🚀 |
| [Meta3D-Technology/Meta3D](https://github.com/Meta3D-Technology/Meta3D) | 185 | 开源Web3D低代码平台，一条龙可视化搭建Web3D应用、编辑器、引擎，共建开放互助的Web3D生态 |
| [zzzzzhowie/vue2-admin](https://github.com/zzzzzhowie/vue2-admin) | 123 | Some good practice for Vue projects |
| [xuya227939/full-stack](https://github.com/xuya227939/full-stack) | 116 | full-stack Next.js 16 + React 19 template with Auth, Supabase, Stripe/ |
| [scarecrowdu/vue-free-table](https://github.com/scarecrowdu/vue-free-table) | 61 | vue-free-table基于 element ui table 二次封装，几乎支持原 table 所有的功能 |
| [liutao2428118/blogs](https://github.com/liutao2428118/blogs) | 5 | vue-ssr博客项目(服务端渲染) |

### 监控 / 工程化（3 个）

| 仓库 | 星 | 干什么 |
|---|---|---|
| [hyj1991/easy-monitor](https://github.com/hyj1991/easy-monitor) | 3129 | 企业级 Node.js 应用性能监控与线上故障定位解决方案 |
| [clouDr-f2e/monitor](https://github.com/clouDr-f2e/monitor) | 1913 | 👀 一款轻量级的收集页面的用户点击行为、路由跳转、接口报错、代码报错、页面性能并上报服务端的SDK |
| [alex1504/femonitor-web](https://github.com/alex1504/femonitor-web) | 126 | 📹 A SDK for web error and performance monitor. web前端错误及性能监控SDK，JS执行错误、 |

### 学习 / 面试 / 方法论（30 个）

| 仓库 | 星 | 干什么 |
|---|---|---|
| [codecrafters-io/build-your-own-x](https://github.com/codecrafters-io/build-your-own-x) | 562029 | Master programming by recreating your favorite technologies from scrat |
| [trekhleb/javascript-algorithms](https://github.com/trekhleb/javascript-algorithms) | 196726 | 📝 Algorithms and data structures implemented in JavaScript with explan |
| [ruanyf/weekly](https://github.com/ruanyf/weekly) | 107967 | 科技爱好者周刊，每周五发布 |
| [goldbergyoni/nodebestpractices](https://github.com/goldbergyoni/nodebestpractices) | 105726 | ✅ The Node.js best practices list (July 2026) |
| [enaqx/awesome-react](https://github.com/enaqx/awesome-react) | 75257 | A collection of awesome things regarding React ecosystem |
| [azl397985856/leetcode](https://github.com/azl397985856/leetcode) | 55706 | LeetCode Solutions: A Record of My Problem Solving Journey.( leetcode题 |
| [ascoders/weekly](https://github.com/ascoders/weekly) | 31717 | 前端精读周刊。帮你理解最前沿、实用的技术。 |
| [Advanced-Frontend/Daily-Interview-Question](https://github.com/Advanced-Frontend/Daily-Interview-Question) | 27327 | 我是依扬（木易杨），公众号「高级前端进阶」作者，每天搞定一道前端大厂面试题，祝大家天天进步，一年后会看到不一样的自己。 |
| [haizlin/fe-interview](https://github.com/haizlin/fe-interview) | 26251 | 前端面试每日 3+1，以面试题来驱动学习，提倡每日学习与思考，每天进步一点！每天早上5点纯手工发布面试题（死磕自己，愉悦大家），6000+道 |
| [ruanyf/free-books](https://github.com/ruanyf/free-books) | 16065 | 互联网上的免费书籍 |
| [phodal/github](https://github.com/phodal/github) | 11343 | GitHub 漫游指南- a Chinese ebook on how to build a good project on Github. |
| [hzpt-inet-club/english-note](https://github.com/hzpt-inet-club/english-note) | 5796 | 从0开始学习英语语法 |
| [kevin2li/PDF-Guru](https://github.com/kevin2li/PDF-Guru) | 4243 | PDF Guru Anki是你整个知识世界的“中枢转换器”，与 Anki 的强大记忆引擎无缝融合，能将来自任何地方、任何格式的知识精华，高效 |
| [LiangJunrong/document-library](https://github.com/LiangJunrong/document-library) | 3877 | jsliang 的文档库. 里面包含了个人撰写的所有前端文章，例如 Vue、React,、ECharts、微信小程序、算法、数据结构等…… |
| [ConardLi/awesome-coding-js](https://github.com/ConardLi/awesome-coding-js) | 3282 | Algorithms and data structures implemented in JavaScript, with detaile |
| [woai3c/nand2tetris](https://github.com/woai3c/nand2tetris) | 2932 | 计算机系统要素-从零开始构建现代计算机 |
| [azl397985856/fe-interview](https://github.com/azl397985856/fe-interview) | 2836 | 宇宙最强的前端面试指南 (https://lucifer.ren/fe-interview) |
| [oldwinter/knowledge-garden](https://github.com/oldwinter/knowledge-garden) | 2466 | 我的第二大脑 second brain，我的数字花园 digital garden，用obsidian双链笔记软件写作而成 |
| [xdite/learn-hack](https://github.com/xdite/learn-hack) | 1587 | 打造超人學習 |
| [fltenwall/web3-awesome](https://github.com/fltenwall/web3-awesome) | 1424 | web3百科全书👏🏻 打造 web3 全球第一中文资源 |
| [RustMagazine/rust_magazine_2021](https://github.com/RustMagazine/rust_magazine_2021) | 1222 | RustMagazine 2021 期刊 (已完结) |
| [kevingo/system-design-primer-zh-tw](https://github.com/kevingo/system-design-primer-zh-tw) | 968 | system-design-primer 繁體中文翻譯計畫。原作者：https://github.com/donnemartin/syste |
| [JohnsenZhou/Front-End-Performance-Checklist](https://github.com/JohnsenZhou/Front-End-Performance-Checklist) | 528 | 🎮  前端性能清单，让你的网站跑的更快 |
| [cpselvis/geektime-webpack-course](https://github.com/cpselvis/geektime-webpack-course) | 334 | 《玩转webpack》极客时间课程源码和课件 |
| [arronf2e/FE-Books](https://github.com/arronf2e/FE-Books) | 237 | 📖  📖  前端书籍pdf整理 |
| [suukii/91-days-algorithm](https://github.com/suukii/91-days-algorithm) | 226 | 91天学算法-Leetcode图解题解集合(JavaScript/C++/Python) Solutions and Explainatio |
| [suukii/Articles](https://github.com/suukii/Articles) | 27 | 记录自己的学习轨迹 |
| [FontEndArt/SGGB](https://github.com/FontEndArt/SGGB) | 12 | Study Group Greens Bird |
| [FontEndArt/blog](https://github.com/FontEndArt/blog) | 8 | 博客源码 含md文件 |
| [yygmind/TargetCompany](https://github.com/yygmind/TargetCompany) | 7 | 面进大厂，代码库 |

### 理财 / 生活 / 杂项（17 个）

| 仓库 | 星 | 干什么 |
|---|---|---|
| [fighting41love/funNLP](https://github.com/fighting41love/funNLP) | 84542 | 中英文敏感词、语言检测、中外手机/电话归属地/运营商查询、名字推断性别、手机号抽取、身份证抽取、邮箱抽取、中日文人名库、中文缩写库、拆字词典 |
| [The-Run-Philosophy-Organization/run](https://github.com/The-Run-Philosophy-Organization/run) | 32751 | 润学全球官方指定GITHUB，整理润学宗旨、纲领、理论和各类润之实例；解决为什么润，润去哪里，怎么润三大问题； 并成为新中国人的核心宗教，核 |
| [houshanren/hangzhou_house_knowledge](https://github.com/houshanren/hangzhou_house_knowledge) | 26850 | 2017年买房经历总结出来的买房购房知识分享给大家，希望对大家有所帮助。买房不易，且买且珍惜。Sharing the knowledge o |
| [modood/Administrative-divisions-of-China](https://github.com/modood/Administrative-divisions-of-China) | 21022 | 中华人民共和国行政区划：省级（省份）、 地级（城市）、 县级（区县）、 乡级（乡镇街道）、 村级（村委会居委会） ，中国省市区镇村二级三级四 |
| [easychen/howto-make-more-money](https://github.com/easychen/howto-make-more-money) | 18736 | 程序员如何优雅的挣零花钱，2.0版，升级为小书了。Most of this not work outside China , so no E |
| [fangzesheng/free-api](https://github.com/fangzesheng/free-api) | 16285 | 收集免费的接口服务,做一个api的搬运工 |
| [laoma528/awesome-zhuiju-free](https://github.com/laoma528/awesome-zhuiju-free) | 15382 | 免费无广告的追剧资源指南，人工精选资源、每天检测资源有效性。收录在线影视、影视APP、网盘搜索、磁力BT、字幕、TVBox / 影视仓空壳软 |
| [OpenEthan/SMSBoom](https://github.com/OpenEthan/SMSBoom) | 15077 | SMSBoom - Deprecate: Due to judicial reasons, the repository has been  |
| [myliang/x-spreadsheet](https://github.com/myliang/x-spreadsheet) | 14573 | The project has been migrated to @wolf-table/table https://github.com/ |
| [easychen/lean-side-bussiness](https://github.com/easychen/lean-side-bussiness) | 12184 | 精益副业：程序员如何优雅地做副业 |
| [WTFAcademy/WTF-Ethers](https://github.com/WTFAcademy/WTF-Ethers) | 3518 | 我最近在重新学ethers.js，巩固一下细节，也写一个“WTF Ethers.js极简入门”，供小白们使用，每周更新1-3讲。Now su |
| [hax/heshijun_v_360](https://github.com/hax/heshijun_v_360) | 2407 | 贺师俊与360的劳动争议诉讼 |
| [ddiu8081/ChartFun](https://github.com/ddiu8081/ChartFun) | 1153 | 🎲 数据大屏可视化编辑器 |
| [ant-design/ant-design-web3](https://github.com/ant-design/ant-design-web3) | 1149 | 🥳 Efficient react components for building dapps easier ／ Connect crypt |
| [carsonWuu/echartJs](https://github.com/carsonWuu/echartJs) | 189 | — |
| [dtsola/xiaoyaoprivatebill](https://github.com/dtsola/xiaoyaoprivatebill) | 110 | 小遥账单，支付宝微信账单一键智能分析，看清每一分钱的去向，每月省下不该花的钱。Xiaoyao Bill Assistant, One-cli |
| [unjust-life/DiffChineseBot](https://github.com/unjust-life/DiffChineseBot) | 7 | 字符串文本diff |

### 我的仓库（5 个）

| 仓库 | 星 | 干什么 |
|---|---|---|
| [chelseachen007/write-code](https://github.com/chelseachen007/write-code) | 2 | 手写一些api原理 |
| [chelseachen007/blog](https://github.com/chelseachen007/blog) | 2 | 奔跑的小胖blog |
| [chelseachen007/xiaopang-cli](https://github.com/chelseachen007/xiaopang-cli) | 1 | 奔跑的小胖个人脚手架 |
| [chelseachen007/c-view](https://github.com/chelseachen007/c-view) | 1 | 奔跑的小胖个人组件库 |
| [chelseachen007/base-vue](https://github.com/chelseachen007/base-vue) | 1 | 一个用于快速新建项目的模板 |

---

### 四张表放在一起看，结论有三条

1. **AI/Agent 相关的收藏有 42 个，数量不缺，缺的是把它们跑通。** 收藏越多越容易产生「我已经会了」的错觉，选 2 个真正用起来（比如 agent 记忆 + 一个 RAG/工作流平台）比继续收 20 个有用。
2. **收藏夹里有一批「一次性工具」**（抢票、SMSBoom、追剧、 gif 生成），作用有限但占位——真要清理时优先删这些。
3. **自己的 5 个仓库星数 1–2**， /  /  都是「想造轮子」型项目。造之前先去第三节查一遍有没有现成的：比如 CLI 脚手架有 、；组件库有 、 这种源码级可抄的。

---

## 刷新方式

```bash
cd /tmp/ghcollect && mkdir -p users
gh api --paginate "user/following?per_page=100" --jq '.[] | .login' > following.tsv
gh api --paginate "user/starred?per_page=100" --jq '.[] | [.full_name,.html_url,..] | @tsv' > starred.tsv
# 每人的 top 仓库
cut -f1 following.tsv | while read -r u; do
  gh api "users/$u/repos?per_page=100" --paginate \
  | jq -r --arg u "$u" '.[] | select(.fork==false) | [$u,.name,.stargazers_count,(.description//""|gsub("[\n\t]";" ")),(.pushed_at//""),(.language//""),((.topics//[])|join(",")),(.archived|tostring)] | @tsv' \
  | sort -t$'\t' -k3,3 -gr | head -8
done > repos.tsv
```
坑：
- `gh api --jq` 不支持 `--arg`（报 `accepts 1 arg(s), received 4`），带变量的 jq 要管道给 `jq -r --arg`。
- 数「某人收藏了多少」不能数返回条数，要读 `--include` 里 `Link` 头的 `page=N; rel="last"`。
- token 只有 `repo`/`gist`/`read:org`/`workflow` 权限，读自己的 following/starred 够用；**改别人的 star 需要交互式 `gh auth refresh -s user`，不能自动做。**
