// 雪球帖子批量抓取脚本 - 运行在浏览器 CDP 上下文
// 自动携带所有 cookies（含 HttpOnly），绕过 WAF

// 注意：此脚本通过 CDP eval 执行，eval 不会 await Promise。
// 脚本启动后立即返回 "RUNNING"，结果通过 window.__xueqiu_done 信号通知完成。
(async function() {
  window.__xueqiu_done = "RUNNING";
  const STOCKS = [
    // AI/算力
    "SZ300308","SZ300502","SH688041","SH603019","SZ002230","SH688256",
    // 半导体
    "SH688981","SZ002371","SH688012",
    // 新能源
    "SZ300750","SZ002594","SZ002460","SZ300014",
    "SH601012","SZ300274",
    // 医药
    "SH603259","SZ300347","SZ300760","SH688180","SZ300122","SZ002007",
    // 关注 ETF（2026-11-05 新增）
    "SH513180",  // 恒生科技ETF华夏 —— 港股科技
    "SH561550"   // 中证500增强ETF华泰柏瑞
  ];
  // 关注 ETF：个股时间线接口对 ETF 几乎无帖，所以额外按「名称关键词」搜索帖子，并单独出行情
  const FOCUS_ETFS = [
    { symbol: "SH513180", name: "恒生科技ETF华夏", label: "港股科技",
      kw: ["恒生科技ETF", "恒生科技", "恒科ETF", "513180"],
      // 邻居标的：投港股科技的人同时聊恒指/中概/腾讯阿里美团，按这些取最近帖
      symbols: ["SH159920", "SH513050", "SZ159636"] },
    { symbol: "SH561550", name: "中证500增强ETF华泰柏瑞", label: "500增强",
      kw: ["中证500增强", "500增强", "指增", "561550"],
      // 指增讨论高度依赖基准，必须一起取 500 / 1000 宽基的最近帖
      symbols: ["SH510500", "SZ159845", "SZ159922", "SH510300"] },
  ];
  const ETF_SEARCH_SIZE = 15;  // 每个 ETF 关键词搜索只取最近 15 条
  const MIN_TEXT_LEN = 150;
  const HOT_SIZE = 50;
  const STOCK_PAGE_SIZE = 15;
  const DELAY_EVERY = 5;
  const MAX_EXTRA_STOCKS = 20;

  // ---- 限流下的生存参数 ----
  // 雪球限流是间歇性的：正常时单请求 200-500ms，被限时劣化到 8-14 秒甚至不返回。
  // 原实现是上百个串行 await fetch 且没有请求级超时，卡住一个就永远不结束。
  // 现在的原则：单请求短超时快速放弃，按剩余时间预算决定哪些环节还能做，
  // 保证"核心内容一定抓得到"，锦上添花的部分（全文补全）按预算做。
  const REQUEST_TIMEOUT = 7000;    // 单请求上限：正常是几百毫秒，7 秒还没回就当它卡了
  const SLOW_THRESHOLD = 2000;     // 超过这个耗时就认为对方开始限流，主动拉长间隔
  const MAX_STALLS = 3;            // 连续这么多次超时就判定被限流，进入冷却并跳过
  // 各环节的"最晚开工时间"。日报不是实时任务，跑久一点没关系；
  // 宁可跑 15 分钟抓全，也不要 3 分钟抓一半。
  // 顺序固定为：ETF → 热门 → 关注动态 → 个股讨论 → 全文补全。
  // 按"实际耗时"算预算（注意 pace() 在变慢时会叠加最多 3.5s 退避）：
  //   热门 1 个请求、ETF 16 个请求、个股 23 个、关注最多 12 页、补全最多 120 篇。
  // 正常不限流约 3-5 分钟跑完；被限流时按下面的 deadline 依次截断，不会整轮报废。
  const DEADLINE_ETF       = 300000;  // ETF 讨论最晚 5min 开工
  const DEADLINE_FOLLOWING = 600000;  // 关注动态最晚 10min 开工
  const DEADLINE_STOCKS    = 900000;  // 个股讨论最晚 15min 开工
  const DEADLINE_HYDRATE   = 1080000; // 全文补全最晚 18min 开工
  const MAX_TOTAL_MS = 1200000;       // 整轮硬上限 20min，防止脚本永远不结束
  const FOLLOWING_PAGES = 12;         // 关注动态最多翻 12 页（实测每页固定 16 条，count 参数无效）
  const HYDRATE_PAGES = 120;          // 全文补全最多补 120 篇（原来 60，观测到关注动态也能到 48 篇）
  const START = Date.now();
  let stalls = 0;
  let gaveUp = false;
  let slowStreak = 0;

  function past(deadline) {
    return Date.now() - START > deadline;
  }

  // 带超时的 fetch：超时、限流、断网都抛错，由调用方的 catch 记一条 warning 继续往下走。
  async function fetchWithTimeout(url, opts) {
    const controller = new AbortController();
    const timer = setTimeout(() => controller.abort(), REQUEST_TIMEOUT);
    const began = Date.now();
    try {
      const resp = await fetch(url, Object.assign({}, opts, { signal: controller.signal }));
      clearTimeout(timer);
      const took = Date.now() - began;
      // 连续两次偏慢就认为限流开始，让调用方把间隔拉长
      if (took > SLOW_THRESHOLD) slowStreak++;
      else slowStreak = 0;
      return resp;
    } catch (e) {
      clearTimeout(timer);
      throw e;
    }
  }

  // 按限流程度自适应退避：正常 0.5s，开始变慢就逐步加到 4s
  async function pace(base) {
    const extra = slowStreak <= 1 ? 0 : Math.min(3500, slowStreak * 1200);
    await new Promise(r => setTimeout(r, base + extra));
  }

  // 限流判定：连续多次超时后，"跳过"只持续一个冷却窗口，过后再试探一次。
  // 否则一旦中途误判，后面所有环节都会被白白跳过。真限流时下一个请求又会超时，很快再次静默。
  const COOLDOWN_MS = 30000;
  let gaveUpAt = 0;

  function throttled() {
    return gaveUp && (Date.now() - gaveUpAt) < COOLDOWN_MS;
  }

  // 统一的取数入口：成功就清空连续超时计数，超时就累加，攒够 MAX_STALLS 次判定限流。
  async function getJSON(url, label, warnings) {
    if (throttled()) throw new Error("限流冷却中，跳过");
    if (Date.now() - START > MAX_TOTAL_MS) throw new Error("到整轮硬上限，停止");
    const resp = await fetchWithTimeout(url);
    const text = await resp.text();
    stalls = 0;
    if (!text.trim().startsWith("{") && !text.trim().startsWith("[")) {
      throw new Error("WAF/非JSON");
    }
    return JSON.parse(text);
  }

  function noteStall(e, label, warnings) {
    if (e && e.name === "AbortError") {
      stalls++;
      warnings.push(label + " 超时");
      if (stalls >= MAX_STALLS) {
        gaveUp = true;
        gaveUpAt = Date.now();
        warnings.push("连续 " + stalls + " 次超时，进入 " + (COOLDOWN_MS / 1000) + "s 冷却");
      }
      return;
    }
    warnings.push(label + " " + (e && e.message || e));
  }

  function clean(html) {
    return (html || "")
      .replace(/<[^>]+>/g, "")
      .replace(/&nbsp;/g, " ")
      .replace(/&amp;/g, "&")
      .replace(/&lt;/g, "<")
      .replace(/&gt;/g, ">")
      .replace(/&#34;/g, '"')
      .replace(/&#39;/g, "'")
      .trim();
  }

  function parsePost(raw, source) {
    const s = raw.original_status || raw;
    const user = s.user || {};
    const text = clean(s.text || s.description || "");
    const title = s.title || text.substring(0, 60);
    return {
      id: String(s.id || ""),
      title: title,
      text: text,
      author: user.screen_name || "",
      author_id: String(user.id || ""),
      url: "https://xueqiu.com/" + (user.id || "") + "/" + (s.id || ""),
      created_at: s.created_at || 0,
      created_at_str: s.created_at
        ? new Date(s.created_at).toISOString().replace("T", " ").substring(0, 16)
        : "",
      retweet_count: s.retweet_count || 0,
      reply_count: s.reply_count || 0,
      like_count: s.fav_count || s.like_count || 0,
      source: source,
    };
  }

  // 获取用户自选股列表
  async function fetchWatchlist() {
    try {
      const data = await getJSON(
        "https://stock.xueqiu.com/v5/stock/portfolio/stock/list.json?pid=-1&category=1&size=1000",
        "watchlist",
        []
      );
      const items = (data.data && data.data.stocks) || data.stocks || data.items || [];
      return items.map(s => ({
        symbol: s.symbol || "",
        name: s.name || "",
        current: s.current || s.price || 0,
        chg: s.chg || 0,
        percent: s.percent || 0,
        volume: s.volume || 0,
        marketcapital: s.marketcapital || s.market_capital || 0,
        high: s.high || 0,
        low: s.low || 0,
        open: s.open || 0,
        last_close: s.last_close || s.last_close_price || 0,
      }));
    } catch (e) {
      return [];
    }
  }

  // 关注 ETF 行情：一次批量请求（stock.xueqiu.com 与 主页 同站域，带 cookie 可用）
  async function fetchEtfQuotes() {
    try {
      const url = "https://stock.xueqiu.com/v5/stock/realtime/quotec.json?symbol=" +
        FOCUS_ETFS.map(e => e.symbol).join(",");
      const data = await getJSON(url, "etf_quotes", []);
      const bySym = {};
      for (const q of (data.data || [])) bySym[q.symbol] = q;
      return FOCUS_ETFS.map(e => {
        const q = bySym[e.symbol] || {};
        return {
          symbol: e.symbol,
          name: e.name,
          label: e.label,
          current: q.current || 0,
          percent: typeof q.percent === "number" ? q.percent : null,
          chg: q.chg || 0,
          open: q.open || 0,
          high: q.high || 0,
          low: q.low || 0,
          last_close: q.last_close || 0,
          amount: q.amount || 0,
          current_year_percent: typeof q.current_year_percent === "number" ? q.current_year_percent : null,
          ok: !!q.current,
        };
      });
    } catch (e) {
      return FOCUS_ETFS.map(e => ({
        symbol: e.symbol, name: e.name, label: e.label, ok: false, percent: null,
      }));
    }
  }

  // 关注 ETF 讨论：按名称关键词走全站搜索（ETF 走 symbol 时间线基本无帖）
  // 一次请求同时产出「按 symbol 的最近帖」和「按关键词的全站帖」，再一起过滤。
  // 帖子内容会把相关标的串在一起（写 500增强 的帖常带 中证500/沪深300），
  // 所以除盯自己的 symbol，还要盯一组邻居标的，避免只抓到孤帖。
  async function fetchEtfPosts(seen, warnings) {
    const queries = [];
    for (const e of FOCUS_ETFS) {
      for (const s of [e.symbol, ...(e.symbols || [])]) {
        queries.push({ label: e.label, kw: e.kw, symbol: s, filter: false });
      }
      for (const kw of e.kw) {
        queries.push({ label: e.label, kw: e.kw, symbol: "", q: kw, filter: true });
      }
    }

    // 两轮过滤：ETF 环节只做「关键词是否真提到」的去噪，不卡长度——
    // 按 symbol 取到的宽基帖可能很短但照样在聊这只 ETF；长度门槛在最终落库前统一卡一次
    const raw = [];
    for (let qi = 0; qi < queries.length; qi++) {
      const q = queries[qi];
      if (past(DEADLINE_ETF)) { warnings.push("ETF 讨论：到时间预算，已搜 " + qi + "/" + queries.length); break; }
      if (throttled()) { warnings.push("etf搜:" + q.label + " 限流冷却中，跳过剩余"); break; }
      const tag = "etf:" + q.label + "/" + (q.q || q.symbol);
      try {
        const url = "/query/v1/symbol/search/status.json?symbol=" +
          encodeURIComponent(q.q || q.symbol) +
          "&count=" + ETF_SEARCH_SIZE + "&comment=0&page=1";
        const data = await getJSON(url, tag, warnings);
        for (const item of (data.list || [])) {
          raw.push({
            item: item,
            label: q.label,
            kw: q.kw,
            filter: q.filter,
            body: ((item.original_status || item).text || item.description || ""),
          });
        }
      } catch (err) { noteStall(err, tag, warnings); }
      await pace(600);
    }

    const out = [];
    const byId = {};
    for (const r of raw) {
      // 关键词全站搜索会混进无关帖：正文必须真的提到该 ETF 的关键词
      if (r.filter && !r.kw.some(k => r.body.indexOf(k) >= 0)) continue;
      const p = parsePost(r.item, "etf:" + r.label);
      if (seen.has(p.id)) continue;
      if (!byId[p.id]) {
        byId[p.id] = p;
        p.etf_hits = [];      // 合并多个来源的命中，日报里按 label 展示
        out.push(p);
      }
      if (!byId[p.id].etf_hits.includes(r.label)) byId[p.id].etf_hits.push(r.label);
    }
    for (const p of out) seen.add(p.id);
    return out;
  }

  async function run() {
    const posts = [];
    const seen = new Set();
    const warnings = [];

    // 0) 获取自选股列表
    const watchlist = await fetchWatchlist();
    const watchlistSymbols = new Set(watchlist.map(w => w.symbol));

    // 1) 关注 ETF 行情 + 讨论
    // 放在热门之前：它们便宜（1 次行情 + 14 次搜索），
    // 保证后面的核心内容被限流时，「关注 ETF」这块先抓到手。
    const etfQuotes = await fetchEtfQuotes();
    if (etfQuotes.some(q => !q.ok)) warnings.push("ETF 行情：部分标的取不到");

    const etfPostsRaw = await fetchEtfPosts(seen, warnings);
    // 长度门槛统一在这里卡：太短的（如「$中证500ETF$ 买点」）没法进日报分析
    const etfPosts = etfPostsRaw.filter(p => p.text.length >= MIN_TEXT_LEN);
    if (etfPostsRaw.length !== etfPosts.length) {
      warnings.push("ETF 讨论：" + (etfPostsRaw.length - etfPosts.length) + " 篇过短已丢弃");
    }
    posts.push(...etfPosts);

    // 2) 热门帖子
    try {
      const data = await getJSON(
        "/statuses/hot/listV2.json?since_id=-1&max_id=-1&size=" + HOT_SIZE,
        "hot",
        warnings
      );
      for (const item of data.items || []) {
        const p = parsePost(item, "hot");
        if (p.text.length >= MIN_TEXT_LEN && !seen.has(p.id)) {
          seen.add(p.id);
          posts.push(p);
        }
      }
    } catch (e) { noteStall(e, "hot", warnings); }

    // 3) 关注的人动态（原创帖 + 转发评论，翻页到昨天之前）- 核心内容，排在个股讨论之前
    const followingPosts = [];
    const followingSeen = new Set();
    const FOLLOWING_MAX_PAGES = FOLLOWING_PAGES;
    const FOLLOWING_PAGE_SIZE = 50;
    const yesterday = new Date();
    yesterday.setDate(yesterday.getDate() - 1);
    yesterday.setHours(0, 0, 0, 0);
    let stopFollowing = false;

    for (let page = 1; page <= FOLLOWING_MAX_PAGES && !stopFollowing; page++) {
      if (past(DEADLINE_FOLLOWING)) {
        warnings.push("关注动态：到时间预算，已翻 " + (page - 1) + " 页");
        break;
      }
      try {
        const data = await getJSON(
          "/statuses/home_timeline.json?page=" + page +
          "&count=" + FOLLOWING_PAGE_SIZE,
          "following p" + page,
          warnings
        );
        const items = Array.isArray(data) ? data : (data.items || data.list || []);
        for (const item of items) {
          const created = item.created_at || 0;
          // Stop if older than yesterday
          if (created > 0 && created < yesterday.getTime()) {
            stopFollowing = true;
            continue;
          }

          // Keep both original posts and retweets with comments
          const isRetweet = !!item.retweet_status_id;
          const desc = (item.description || "").replace(/<[^>]+>/g, "").replace(/&nbsp;/g, " ").replace(/&#39;/g, "'").replace(/&amp;/g, "&").trim();
          const text = (item.text || "").replace(/<[^>]+>/g, "").replace(/&nbsp;/g, " ").replace(/&#39;/g, "'").replace(/&amp;/g, "&").trim();
          const content = desc || text;

          // Skip pure retweets with no comment
          if (isRetweet && !desc) continue;
          if (!content || followingSeen.has(String(item.id))) continue;
          followingSeen.add(String(item.id));

          const s = item.original_status || item;
          const user = s.user || item.user || {};
          followingPosts.push({
            id: String(item.id),
            title: item.title || content.substring(0, 60),
            text: content,
            author: user.screen_name || "",
            author_id: String(user.id || ""),
            url: "https://xueqiu.com/" + (user.id || "") + "/" + (item.id || ""),
            created_at: created,
            created_at_str: created ? new Date(created).toISOString().replace("T", " ").substring(0, 16) : "",
            retweet_count: item.retweet_count || 0,
            reply_count: item.reply_count || 0,
            like_count: item.fav_count || item.like_count || 0,
            source: "following",
            is_retweet: isRetweet,
          });
        }
        // API returns ~16 items per page, NOT 50. Use === 0 to avoid early break.
        if (items.length === 0) break;
      } catch (e) { noteStall(e, "following p" + page, warnings); }
      await pace(900);
    }

    // 4) 个股讨论 - 合并硬编码 + 自选股（排除已覆盖的）
    // ETF 已通过关键词搜索单独抓过，不重复按 symbol 再抓一轮
    const extraStocks = [...watchlistSymbols]
      .filter(s => !STOCKS.includes(s))
      .slice(0, MAX_EXTRA_STOCKS);
    const allStocks = [...STOCKS, ...extraStocks];

    for (let i = 0; i < allStocks.length; i++) {
      if (past(DEADLINE_STOCKS)) {
        warnings.push("个股讨论：到时间预算，已抓 " + i + "/" + allStocks.length);
        break;
      }
      try {
        const url =
          "/query/v1/symbol/search/status.json?symbol=" +
          allStocks[i] + "&count=" + STOCK_PAGE_SIZE + "&comment=0&page=1";
        const data = await getJSON(url, "stock:" + allStocks[i], warnings);
        for (const item of data.list || []) {
          const p = parsePost(item, "stock:" + allStocks[i]);
          if (p.text.length >= MIN_TEXT_LEN && !seen.has(p.id)) {
            seen.add(p.id);
            posts.push(p);
          }
        }
      } catch (e) { noteStall(e, "stock:" + allStocks[i], warnings); }
      await pace(DELAY_EVERY > 1 ? 500 : 400);
      if ((i + 1) % DELAY_EVERY === 0) await pace(1000);
    }

  // 5) 补拉全文：列表接口只返回截断摘要（description 约 150 字），需按 id 取详情
  // 这是"锦上添花"环节：时间不够就少补几篇，不影响前面已抓到的内容
  const MAX_HYDRATE = HYDRATE_PAGES;
  const HYDRATE_DELAY = 1200;
  let hydrated = 0;
  const targets = posts.slice(0, MAX_HYDRATE);
  for (let i = 0; i < targets.length; i++) {
    if (past(DEADLINE_HYDRATE)) { warnings.push("补全全文：到时间预算，已补 " + i + "/" + targets.length); break; }
    if (throttled()) { warnings.push("补全全文：限流冷却中，跳过剩余 " + (targets.length - i) + " 篇"); break; }
    const p = targets[i];
    try {
      const resp = await fetchWithTimeout("/statuses/show.json?id=" + p.id);
      const txt = await resp.text();
      stalls = 0;
      if (!txt.trim().startsWith("{")) { warnings.push("hydrate:" + p.id + " WAF"); }
      else {
        const d = JSON.parse(txt);
        const full = clean(d.text || d.description || "");
        if (full.length > p.text.length) { p.text = full; hydrated++; }
        if (!p.title || p.title.length < 4) p.title = p.title || full.substring(0, 60);
      }
    } catch (e) { noteStall(e, "hydrate:" + p.id, warnings); }
    if ((i + 1) % 5 === 0) await pace(HYDRATE_DELAY);
  }

  const result = {
    date: new Date().toISOString().split("T")[0],
    generated_at: new Date().toISOString(),
    watchlist: watchlist,
    watchlist_count: watchlist.length,
    focus_etfs: FOCUS_ETFS.map(e => ({ symbol: e.symbol, name: e.name, label: e.label, kw: e.kw })),
    etf_quotes: etfQuotes,
    total_fetched: posts.length,
    posts: posts,
    following: followingPosts,
    following_count: followingPosts.length,
  };
    window.__xueqiu_result = JSON.stringify(result);
    window.__xueqiu_done = JSON.stringify({
      ok: true,
      partial: gaveUp || posts.length === 0 || warnings.some(w => w.indexOf("到时间预算") >= 0 || w.indexOf("冷却") >= 0),
      throttled: gaveUp,
      elapsed_ms: Date.now() - START,
      total: posts.length,
      hot: posts.filter(p => p.source === "hot").length,
      stock: posts.filter(p => String(p.source).indexOf("stock:") === 0).length,
      etf_posts: etfPosts.length,
      etf_quotes_ok: etfQuotes.filter(q => q.ok).length,
      watchlist: watchlist.length,
      extra_stocks: extraStocks.length,
      following: followingPosts.length,
      hydrated: hydrated,
      warnings: warnings,
    });
  }

  try {
    await run();
  } catch(e) {
    window.__xueqiu_done = JSON.stringify({ok: false, error: e.message});
  }
})()
