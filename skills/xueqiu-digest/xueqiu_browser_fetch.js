// 雪球帖子批量抓取脚本 - 运行在浏览器 CDP 上下文
// 自动携带所有 cookies（含 HttpOnly），绕过 WAF

(function() {
  const STOCKS = [
    // AI/算力
    "SZ300308","SZ300502","SH688041","SH603019","SZ002230","SH688256",
    // 半导体
    "SH688981","SZ002371","SH688012",
    // 新能源
    "SZ300750","SZ002594","SZ002460","SZ300014",
    "SH601012","SZ300274",
    // 医药
    "SH603259","SZ300347","SZ300760","SH688180","SZ300122","SZ002007"
  ];
  const MIN_TEXT_LEN = 150;
  const HOT_SIZE = 50;
  const STOCK_PAGE_SIZE = 15;
  const DELAY_EVERY = 5;  // 每 N 个股票暂停一次

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
    // hot posts: wrapped in original_status; stock timeline: flat
    const s = raw.original_status || raw;
    const user = s.user || {};
    const text = clean(s.description || s.text || "");
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

  async function run() {
    const posts = [];
    const seen = new Set();

    // 1) 热门帖子
    try {
      const resp = await fetch(
        "https://xueqiu.com/statuses/hot/listV2.json?since_id=-1&max_id=-1&size=" + HOT_SIZE
      );
      const data = await resp.json();
      for (const item of data.items || []) {
        const p = parsePost(item, "hot");
        if (p.text.length >= MIN_TEXT_LEN && !seen.has(p.id)) {
          seen.add(p.id);
          posts.push(p);
        }
      }
    } catch (e) { /* skip */ }

    // 2) 个股讨论
    for (let i = 0; i < STOCKS.length; i++) {
      try {
        const url =
          "https://xueqiu.com/query/v1/symbol/search/status.json?symbol=" +
          STOCKS[i] + "&count=" + STOCK_PAGE_SIZE + "&comment=0&page=1";
        const resp = await fetch(url);
        const data = await resp.json();
        for (const item of data.list || []) {
          const p = parsePost(item, "stock:" + STOCKS[i]);
          if (p.text.length >= MIN_TEXT_LEN && !seen.has(p.id)) {
            seen.add(p.id);
            posts.push(p);
          }
        }
      } catch (e) { /* skip */ }
      if ((i + 1) % DELAY_EVERY === 0) {
        await new Promise(r => setTimeout(r, 1000));
      }
    }

    // 3) 保存到全局变量供外部提取
    const result = {
      date: new Date().toISOString().split("T")[0],
      generated_at: new Date().toISOString(),
      total_fetched: posts.length,
      posts: posts,
    };
    window.__xueqiu_result = JSON.stringify(result);
    return JSON.stringify({
      ok: true,
      total: posts.length,
      hot: posts.filter(p => p.source === "hot").length,
      stock: posts.filter(p => p.source !== "hot").length,
    });
  }

  return run();
})()
