#!/usr/bin/env bun
/**
 * 统一视频字幕提取 —— 抓取层
 *
 * 只负责「拿到带时间戳的分段文本」，不做清洗、不做整理、不写笔记。
 * 输出一律落到 /tmp/xvt/<jobId>/ 下的标准中间产物：
 *   meta.json       视频元信息
 *   segments.json   [{start, end, text}]      —— 唯一权威原文
 *   transcript.txt  纯文本（无时间戳）
 *   transcript.srt  SRT
 *
 * 用法:
 *   bun fetch.ts <url-or-path> [--out <dir>] [--lang zh] [--force-asr]
 *                               [--platform bilibili|youtube|douyin|xiaohongshu|podcast|local]
 *                               [--model-path <dir>] [--whisper-model small] [--json]
 */

import { spawnSync } from "node:child_process";
import { existsSync, mkdirSync, readFileSync, readdirSync, rmSync, writeFileSync } from "node:fs";
import { basename, extname, join, resolve } from "node:path";

const CDP = "http://127.0.0.1:3456";
const VERSION = "4.0.0";

type Seg = { start: number; end: number; text: string };
type Platform =
  | "bilibili" | "youtube" | "douyin" | "xiaohongshu"
  | "xiaoyuzhou" | "ximalaya" | "podcast" | "local" | "unknown";

type Meta = {
  id: string;
  platform: Platform;
  title: string;
  author: string;
  description: string;
  duration: number;
  url: string;
  cover: string;
  language: string;
  source: "official" | "asr";
  /** 依序尝试过的路线，成功的那条在最后；失败记录含原因 */
  attempts: { route: string; ok: boolean; note?: string }[];
  fetchedAt: string;
};

// ────────────────────────────── 工具 ──────────────────────────────

function sh(cmd: string, args: string[], opts: { timeout?: number; env?: Record<string, string> } = {}) {
  const r = spawnSync(cmd, args, {
    encoding: "utf-8",
    timeout: opts.timeout ?? 180_000,
    env: { ...process.env, ...(opts.env ?? {}) },
  });
  return { status: r.status, stdout: r.stdout ?? "", stderr: r.stderr ?? "" };
}

function have(cmd: string): boolean {
  return sh("sh", ["-c", `command -v ${cmd}`], { timeout: 5_000 }).status === 0;
}

function hms(t: number): string {
  const s = Math.max(0, Math.floor(t));
  return [Math.floor(s / 3600), Math.floor((s % 3600) / 60), s % 60]
    .map((n) => String(n).padStart(2, "0")).join(":");
}

function srtTime(t: number): string {
  const ms = Math.max(0, Math.round(t * 1000));
  const h = Math.floor(ms / 3_600_000), m = Math.floor((ms % 3_600_000) / 60_000);
  const s = Math.floor((ms % 60_000) / 1000), r = ms % 1000;
  return `${String(h).padStart(2, "0")}:${String(m).padStart(2, "0")}:${String(s).padStart(2, "0")},${String(r).padStart(3, "0")}`;
}

const sleep = (ms: number) => new Promise((r) => setTimeout(r, ms));

function slug(s: string): string {
  return s.replace(/[\\/:*?"<>|\n\r\t]/g, "").replace(/\s+/g, " ").trim().slice(0, 80) || "untitled";
}

// ────────────────────────────── CDP ──────────────────────────────

async function cdpOk(): Promise<boolean> {
  try {
    const r = await fetch(`${CDP}/targets`, { signal: AbortSignal.timeout(3000) });
    return r.ok;
  } catch {
    return false;
  }
}

async function cdpNew(url: string): Promise<string> {
  const r = await fetch(`${CDP}/new?url=${encodeURIComponent(url)}`, { signal: AbortSignal.timeout(30_000) });
  const j = (await r.json()) as { targetId?: string; error?: string };
  if (!j.targetId) throw new Error(`CDP 新建标签页失败: ${j.error ?? JSON.stringify(j)}`);
  return j.targetId;
}

async function cdpEval(target: string, js: string): Promise<any> {
  const r = await fetch(`${CDP}/eval?target=${target}`, {
    method: "POST", body: js, signal: AbortSignal.timeout(60_000),
  });
  const j = (await r.json()) as { value?: any; error?: string };
  if (j.error) throw new Error(j.error);
  return j.value;
}

async function cdpJson(target: string, js: string): Promise<any> {
  const v = await cdpEval(target, js);
  if (typeof v !== "string") return v;
  try { return JSON.parse(v); } catch { throw new Error(`CDP 返回非 JSON: ${v.slice(0, 200)}`); }
}

async function cdpClose(target: string) {
  await fetch(`${CDP}/close?target=${target}`, { signal: AbortSignal.timeout(10_000) }).catch(() => {});
}

// ────────────────────────────── B站 ──────────────────────────────

/** 从页面取视频元信息 + 字幕列表（走页面上下文，自动带 Cookie 和 WBI 签名） */
async function bilibiliOfficial(bvid: string): Promise<{ segs: Seg[]; meta: Partial<Meta> }> {
  const tid = await cdpNew(`https://www.bilibili.com/video/${bvid}`);
  try {
    await sleep(4500);
    const info = await cdpJson(tid, `JSON.stringify({
      aid: window.__INITIAL_STATE__?.aid,
      cid: window.__INITIAL_STATE__?.cid || window.__INITIAL_STATE__?.videoData?.cid,
      title: window.__INITIAL_STATE__?.videoData?.title,
      author: window.__INITIAL_STATE__?.videoData?.owner?.name,
      desc: window.__INITIAL_STATE__?.videoData?.desc,
      duration: window.__INITIAL_STATE__?.videoData?.duration,
      pic: window.__INITIAL_STATE__?.videoData?.pic
    })`);
    if (!info?.aid || !info?.cid) throw new Error("页面 __INITIAL_STATE__ 未就绪（可能需要登录或页面改版）");

    const subs = await cdpJson(tid, `(async () => {
      const r = await fetch('https://api.bilibili.com/x/player/wbi/v2?bvid=${bvid}&cid=${info.cid}&aid=${info.aid}', {credentials:'include'});
      const d = await r.json();
      if (d.code !== 0) return JSON.stringify({ error: d.code + ' ' + d.message });
      return JSON.stringify({ list: (d.data?.subtitle?.subtitles ?? []).map(s => ({ url: s.subtitle_url, lan: s.lan, doc: s.lan_doc })) });
    })()`);
    if (subs?.error) throw new Error(`B站 player API 失败: ${subs.error}`);
    if (!subs?.list?.length) throw new Error("该视频没有官方字幕");

    // 中文优先，其次任意语言官方字幕，最后第一个
    const pick = subs.list.find((s: any) => /^zh/i.test(s.lan)) ?? subs.list[0];
    const url = pick.url.startsWith("http") ? pick.url : `https:${pick.url}`;
    const body = await cdpJson(tid, `(async () => {
      const r = await fetch('${url}');
      const d = await r.json();
      return JSON.stringify((d.body ?? []).map(s => ({ start: s.from, end: s.to, text: s.content })));
    })()`);
    if (!Array.isArray(body) || !body.length) throw new Error("字幕接口返回空正文");

    return {
      segs: body.map((s: any) => ({ start: +s.start, end: +s.end, text: String(s.text ?? "").trim() })),
      meta: {
        title: info.title ?? "", author: info.author ?? "", description: info.desc ?? "",
        duration: info.duration ?? 0, cover: info.pic ?? "", language: pick.lan ?? "zh",
      },
    };
  } finally {
    await cdpClose(tid);
  }
}

// ────────────────────────────── 通用 CDP 抓取 ──────────────────────────────

/**
 * 小红书专用：从 __INITIAL_STATE__.note.noteDetailMap 里取真实 CDN 地址。
 * 为什么不能用 video.currentSrc：小红书播放器用 MSE，currentSrc 是 blob:，
 * curl 拿到会报 `Port number was not a decimal number`。stream 里才是可下载的 mp4。
 * 取 size 最小的一档（够 ASR 用，下载最快）。
 * 但必须先筛「带音轨」的：stream 分两族，EF4 = h264+aac，EF5 = HEVC 纯视频无音轨；
 * 直接按 size 最小选会命中 EF5，ffmpeg 抽不出音频 → ASR 全挂。
 */
async function xhsMediaFromState(tid: string): Promise<{ media: string; duration: number } | null> {
  const raw = await cdpJson(tid, `JSON.stringify((function(){
    var s = window.__INITIAL_STATE__ && window.__INITIAL_STATE__.note;
    if(!s || !s.noteDetailMap) return {err:"no noteDetailMap"};
    var k = Object.keys(s.noteDetailMap);
    if(!k.length) return {err:"empty noteDetailMap"};
    var m = s.noteDetailMap[k[0]].note;
    if(!m) return {err:"no note"};
    var media = m.video && m.video.media;
    var st = (media && media.stream) || {};
    var withAudio = [], noAudio = [];
    for(var key in st){
      var arr = st[key];
      if(!Array.isArray(arr)) continue;
      for(var i=0;i<arr.length;i++){
        var v = arr[i];
        if(!v || !v.masterUrl) continue;
        (v.audioCodec ? withAudio : noAudio).push(v);
      }
    }
    var pool = withAudio.length ? withAudio : noAudio;
    var best = null;
    for(var j=0;j<pool.length;j++){ if(!best || pool[j].size < best.size) best = pool[j]; }
    if(!best) return {err:"no stream url"};
    return {url: best.masterUrl, size: best.size, hasAudio: !!best.audioCodec,
            dur: (media.video && media.video.duration) || 0,
            title: m.title || "", desc: m.desc || "", user: (m.user && m.user.nickname) || ""};
  })())`);
  if (!raw || raw.err || !raw.url) return null;
  if (!raw.hasAudio) console.warn("⚠ 小红书只返回了无音轨的 HEVC 流，ASR 会失败");
  return { media: raw.url, duration: raw.dur || 0 };
}

/** 在页面里找 <video>/<audio> 的真实媒体地址（handle 有时效，必须立刻下载） */
async function mediaUrlFromPage(url: string): Promise<{ media: string; kind: "video" | "audio"; meta: Partial<Meta> }> {
  const tid = await cdpNew(url);
  try {
    await sleep(5000);

    // 小红书优先走 state（blob: 兜不住），失败再退回通用探测
    if (/xiaohongshu\.com/.test(url)) {
      const x = await xhsMediaFromState(tid);
      if (x) {
        const t = await cdpJson(tid, `JSON.stringify({
          title: (document.querySelector('#detail-title')?.innerText || document.title || '').replace(/ - 小红书$/, '').trim(),
          author: document.querySelector('.username')?.innerText?.trim() || '',
          desc: document.querySelector('#detail-desc')?.innerText?.trim() || ''
        })`);
        return {
          media: x.media, kind: "video",
          meta: { title: t?.title ?? "", author: t?.author ?? "", description: t?.desc ?? "", duration: x.duration },
        };
      }
    }

    const info = await cdpJson(tid, `JSON.stringify({
      media: document.querySelector('video')?.currentSrc
          || document.querySelector('video')?.src
          || document.querySelector('audio')?.currentSrc
          || document.querySelector('audio source')?.src || '',
      kind: document.querySelector('video')?.currentSrc || document.querySelector('video')?.src ? 'video' : 'audio',
      title: document.querySelector('h1')?.innerText?.trim()
          || document.querySelector('[id*=title]')?.innerText?.trim()
          || document.title,
      author: document.querySelector('.author-card-user-name')?.innerText?.trim()
          || document.querySelector('[data-e2e="user-info"] h3')?.innerText?.trim()
          || document.querySelector('.author-wrapper .username')?.innerText?.trim()
          || document.querySelector('.username')?.innerText?.trim()
          || document.querySelector('[class*=author]')?.innerText?.trim() || '',
      desc: document.querySelector('meta[name=description]')?.content
          || document.querySelector('#detail-desc')?.innerText?.trim() || ''
    })`);
    if (!info?.media) throw new Error("页面里没找到 <video>/<audio> 媒体源（可能未登录、需验证码或非媒体页）");
    return {
      media: info.media, kind: info.kind ?? "video",
      meta: { title: (info.title ?? "").replace(/ - (抖音|抖音精选|小红书)$/, "").trim(), author: info.author ?? "", description: info.desc ?? "" },
    };
  } finally {
    await cdpClose(tid);
  }
}

function download(mediaUrl: string, dest: string, referer?: string) {
  const args = ["-L", "--fail", "--max-time", "600", "-o", dest, "-A",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0 Safari/537.36"];
  if (referer) args.push("-H", `Referer: ${referer}`);
  args.push(mediaUrl);
  const r = sh("curl", args);
  if (r.status !== 0 || !existsSync(dest)) throw new Error(`媒体下载失败: ${(r.stderr || "").slice(0, 300)}`);
}

// ────────────────────────────── ASR ──────────────────────────────

/** WhisperKit（CoreML / Apple Silicon）。模型路径来自 config.json，也可 --model-path 覆盖 */
function asrWhisperKit(media: string, workDir: string, language: string, modelPath?: string): Seg[] {
  if (!have("whisperkit-cli")) throw new Error("whisperkit-cli 未安装：brew install whisperkit-cli");
  const mp = modelPath || loadConfig().whisperkit_model_path;
  if (mp && !existsSync(mp)) throw new Error(`WhisperKit 模型目录不存在: ${mp}`);

  const wav = join(workDir, "audio.wav");
  const c = sh("ffmpeg", ["-y", "-v", "error", "-i", media, "-vn", "-ac", "1", "-ar", "16000", "-c:a", "pcm_s16le", wav]);
  if (c.status !== 0) throw new Error(`ffmpeg 抽音频失败: ${(c.stderr || "").slice(0, 300)}`);

  // 关键：WhisperKit 的 --report-path 目录必须事先存在，否则静默失败但退出码仍是 0
  const repDir = join(workDir, "wkreport");
  mkdirSync(repDir, { recursive: true });
  const args = ["transcribe", "--audio-path", wav, "--language", language,
    "--report", "--report-path", repDir];
  if (mp) args.push("--model-path", mp);
  const t = sh("whisperkit-cli", args, { timeout: 3_600_000 });
  if (t.status !== 0) throw new Error(`whisperkit-cli 失败: ${(t.stderr || t.stdout || "").slice(0, 400)}`);

  const jsonFiles = existsSync(repDir) ? readdirSync(repDir).filter((f) => f.endsWith(".json")) : [];
  if (!jsonFiles.length) throw new Error(`WhisperKit 未产出报告（目录 ${repDir} 为空）`);
  const report = JSON.parse(readFileSync(join(repDir, jsonFiles[0]), "utf-8"));
  const segs: Seg[] = (report.segments ?? []).map((s: any) => ({
    start: +s.start, end: +s.end,
    text: String(s.text ?? "").replace(/<\|[^|]*\|>/g, "").trim(),
  })).filter((s: Seg) => s.text);
  if (!segs.length) throw new Error("WhisperKit 返回 0 个有效分段（音频可能无声或语言参数不匹配）");
  return segs;
}

/** faster-whisper / mlx-whisper 兜底（跨平台，不依赖 Apple Silicon） */
function asrPython(media: string, workDir: string, language: string, engine: "faster-whisper" | "mlx"): Seg[] {
  const script = join(import.meta.dir, "asr_fallback.py");
  const args = [script, media, "--out", join(workDir, "pyasr"), "--language", language, "--engine", engine];
  const r = sh("python3", args, { timeout: 3_600_000 });
  if (r.status !== 0) throw new Error(`Python ASR 失败: ${(r.stderr || "").slice(0, 400)}`);
  const data = JSON.parse(readFileSync(join(workDir, "pyasr", "segments.json"), "utf-8"));
  const segs: Seg[] = (data.segments ?? []).map((s: any) => ({ start: +s.start, end: +s.end, text: String(s.text ?? "").trim() }))
    .filter((s: Seg) => s.text);
  if (!segs.length) throw new Error(`${engine} 返回 0 个有效分段`);
  return segs;
}

/** 依次尝试 WhisperKit → mlx-whisper → faster-whisper */
function asrChain(media: string, workDir: string, language: string, attempts: Meta["attempts"]): Seg[] {
  const order: ("whisperkit" | "mlx" | "faster-whisper")[] =
    process.platform === "darwin" && process.arch === "arm64"
      ? ["whisperkit", "mlx", "faster-whisper"]
      : ["faster-whisper"];
  for (const engine of order) {
    try {
      const segs = engine === "whisperkit"
        ? asrWhisperKit(media, workDir, language)
        : asrPython(media, workDir, language, engine);
      attempts.push({ route: `asr:${engine}`, ok: true });
      return segs;
    } catch (e) {
      attempts.push({ route: `asr:${engine}`, ok: false, note: (e as Error).message });
    }
  }
  throw new Error("所有本地 ASR 引擎都失败，见 attempts 详情");
}

// ────────────────────────────── 平台识别 ──────────────────────────────

function detect(input: string): { platform: Platform; id: string } {
  if (existsSync(input)) return { platform: "local", id: basename(input) };

  // 先按域名判定，避免 query 里的随机串被误认成 BV 号。
  // 真实踩坑：小红书 xsec_token=ABVZmacZFayiR... 里含 "BVZmacZFayiR"，
  // 被 (BV[0-9A-Za-z]{10}) 无锚点命中 → 整条小红书链接被当成 B 站视频。
  if (/xiaohongshu\.com|xhslink/.test(input)) return { platform: "xiaohongshu", id: input.match(/explore\/([a-f0-9]+)/)?.[1] ?? "xhs" };
  if (/douyin\.com|v\.douyin/.test(input)) return { platform: "douyin", id: input.match(/video\/(\d+)/)?.[1] ?? "douyin" };
  if (/youtu\.?be/.test(input)) {
    const yt = input.match(/(?:v=|youtu\.be\/|\/shorts\/)([0-9A-Za-z_-]{11})/);
    return { platform: "youtube", id: yt?.[1] ?? "youtube" };
  }
  if (/bilibili\.com|b23\.tv/.test(input)) {
    const bv = input.match(/(BV[0-9A-Za-z]{10})/);
    const av = input.match(/\/video\/av(\d+)/i);
    return { platform: "bilibili", id: bv?.[1] ?? (av ? `av${av[1]}` : "bilibili") };
  }
  if (/xiaoyuzhoufm\.com/.test(input)) return { platform: "xiaoyuzhou", id: input.match(/episode\/([a-z0-9]+)/i)?.[1] ?? "xyz" };
  if (/ximalaya\.com/.test(input)) return { platform: "ximalaya", id: input.match(/(\d+)/)?.[1] ?? "ximalaya" };

  // 裸 ID 兜底（用户直接给 BV 号 / av 号）
  const bareBv = input.match(/^(BV[0-9A-Za-z]{10})$/);
  if (bareBv) return { platform: "bilibili", id: bareBv[1] };
  const bareAv = input.match(/^av(\d+)$/i);
  if (bareAv) return { platform: "bilibili", id: `av${bareAv[1]}` };

  return { platform: "unknown", id: "unknown" };
}

function loadConfig(): any {
  const p = join(import.meta.dir, "..", "config.json");
  return existsSync(p) ? JSON.parse(readFileSync(p, "utf-8")) : {};
}

// ────────────────────────────── 主流程 ──────────────────────────────

type Opts = {
  input: string; out?: string; lang: string; forceAsr: boolean;
  platform?: Platform; modelPath?: string; whisperModel?: string; quiet: boolean;
};

async function fetchTranscript(o: Opts): Promise<{ meta: Meta; segs: Seg[]; workDir: string }> {
  const det = o.platform ? { platform: o.platform, id: detect(o.input).id } : detect(o.input);
  const attempts: Meta["attempts"] = [];
  const cfg = loadConfig();
  const jobId = `${det.platform}-${Date.now()}`;
  const workDir = o.out ? resolve(o.out) : `/tmp/xvt/${jobId}`;
  mkdirSync(workDir, { recursive: true });
  const mediaDir = join(workDir, "media");
  mkdirSync(mediaDir, { recursive: true });

  let segs: Seg[] = [];
  let meta: Partial<Meta> = {};
  let source: "official" | "asr" = "official";

  const asrFromUrl = (url: string, referer?: string) => {
    const dest = join(mediaDir, "media.bin");
    download(url, dest, referer);
    return asrChain(dest, workDir, o.lang, attempts);
  };

  try {
    switch (det.platform) {
      case "bilibili": {
        if (o.forceAsr) throw new Error("--force-asr 已指定，跳过官方字幕");
        const r = await bilibiliOfficial(det.id);
        meta = r.meta;
        const fixed = fixBilibiliAi(r.segs);
        segs = fixed.segs;
        attempts.push({
          route: `bilibili:cdp-official(${r.meta.language ?? "?"})`,
          ok: true,
          note: fixed.dropped ? `合并重叠/重复段 ${fixed.dropped} 条` : undefined,
        });
        break;
      }

      case "youtube": {
        if (o.forceAsr) throw new Error("--force-asr 已指定，跳过官方字幕");
        if (!have("yt-dlp") && !have("python3")) throw new Error("yt-dlp 未安装");
        const outTpl = join(mediaDir, "yt");
        const langList = [o.lang, `${o.lang}-orig`, "zh-Hans", "zh-CN", "zh", "en", "en-orig"].join(",");
        // 先试原语言 + 中文，再退回任意可用字幕
        // --no-update 抑制过期提示；--skip-download 只要字幕，不碰视频
        const ytBase = ["--ignore-config", "--no-playlist", "--no-update", "--skip-download",
          "--write-subs", "--write-auto-subs", "--sub-format", "vtt/srt", "-o", outTpl, o.input];
        const listSubs = () => readdirSync(mediaDir).filter((f) => /\.(vtt|srt)$/.test(f));
        let r = sh("yt-dlp", [...ytBase, "--sub-langs", langList], { timeout: 180_000 });
        let files = listSubs();
        if (!files.length) {
          r = sh("yt-dlp", [...ytBase, "--sub-langs", "all"], { timeout: 180_000 });
          files = listSubs();
        }
        if (!files.length) throw new Error(`yt-dlp 未取到字幕: ${(r.stderr || "").slice(0, 300)}`);

        // 选文件：先按与 lang 的匹配度打分，再在同分里优先非 auto 生成。
        // 不能顺序依赖 readdirSync——之前退了德语字幕却默认 lang=zh，静默给出全德文稿。
        const langOf = (f: string) => f.match(/\.([a-zA-Z-]+)\.(vtt|srt)$/)?.[1] ?? "";
        const score = (f: string) => {
          const l = langOf(f).toLowerCase();
          const want = o.lang.toLowerCase();
          if (l === want || l === `${want}-orig`) return 3;
          if (l.startsWith(want + "-") || l === "zh-hans" || l === "zh-cn") return want.startsWith("zh") && l.startsWith("zh") ? 3 : 2;
          if (want.startsWith("zh") && l.startsWith("zh")) return 3;
          if (l.startsWith("en")) return 1;
          return 0;
        };
        const ranked = [...files].sort((a, b) => {
          const d = score(b) - score(a);
          if (d !== 0) return d;
          return (/\.auto\./i.test(a) ? 1 : 0) - (/\.auto\./i.test(b) ? 1 : 0);
        });
        const pickFile = ranked[0];
        const pickedLang = langOf(pickFile);
        const offLang = score(pickFile) === 0;

        segs = parseSubtitle(join(mediaDir, pickFile));
        const info = ytInfo(o.input);
        meta = { ...info, language: pickedLang || o.lang };
        attempts.push({
          route: `youtube:subtitle(${pickFile})`, ok: true,
          note: offLang ? `无 ${o.lang} 字幕，退到 ${pickedLang}，需人工确认是否接受该语种` : undefined,
        });
        if (offLang) {
          console.error(`⚠ 该视频没有 ${o.lang} 字幕，已退到 ${pickedLang}（${pickFile}）`);
          console.error(`  要原语言转写请加 --force-asr，否则正文将是 ${pickedLang} 的原文。`);
        }
        break;
      }

      case "douyin":
      case "xiaohongshu":
      case "xiaoyuzhou":
      case "ximalaya":
      case "podcast": {
        if (!(await cdpOk())) throw new Error("需要 CDP：请确认 Chrome 已开远程调试且 CDP Proxy 在 127.0.0.1:3456 运行");
        const page = await mediaUrlFromPage(o.input);
        const referer = det.platform === "douyin" ? "https://www.douyin.com/"
          : det.platform === "xiaohongshu" ? "https://www.xiaohongshu.com/" : undefined;
        segs = asrFromUrl(page.media, referer);
        meta = { ...page.meta };
        source = "asr";
        break;
      }

      case "local": {
        segs = asrChain(resolve(o.input), workDir, o.lang, attempts);
        meta = { title: basename(o.input), author: "", description: "", url: resolve(o.input), duration: 0 };
        source = "asr";
        break;
      }

      default:
        throw new Error(`无法识别的输入: ${o.input}（可用 --platform bilibili|youtube|douyin|xiaohongshu|podcast|local 强制指定）`);
    }
  } catch (e) {
    attempts.push({ route: `${det.platform}:primary`, ok: false, note: (e as Error).message });
    // B站/YouTube 主路线失败后统一降级到 ASR
    if (det.platform === "bilibili" || det.platform === "youtube") {
      const url = det.platform === "bilibili"
        ? `https://www.bilibili.com/video/${det.id}`
        : `https://www.youtube.com/watch?v=${det.id}`;
      try {
        const dest = join(mediaDir, "media.m4a");
        const r = sh("yt-dlp", ["--ignore-config", "--no-playlist", "--no-update",
          "-f", "bestaudio[ext=m4a]/bestaudio", "-o", dest, url], { timeout: 900_000 });
        if (r.status !== 0 || !existsSync(dest)) throw new Error(`音频下载失败: ${(r.stderr || "").slice(0, 300)}`);
        segs = asrChain(dest, workDir, o.lang, attempts);
        const info = det.platform === "youtube" ? ytInfo(url) : {};
        meta = { ...info, title: (meta.title as string) ?? info.title ?? det.id };
        source = "asr";
      } catch (e2) {
        attempts.push({ route: `${det.platform}:asr-fallback`, ok: false, note: (e2 as Error).message });
        throw new Error(`主路线与 ASR 兜底都失败：\n${attempts.map((a) => `  - ${a.route}: ${a.ok ? "ok" : a.note}`).join("\n")}`);
      }
    } else {
      throw e;
    }
  }

  const full: Meta = {
    id: det.id,
    platform: det.platform,
    title: slug(String(meta.title ?? det.id)),
    author: String(meta.author ?? ""),
    description: String(meta.description ?? ""),
    duration: Number(meta.duration ?? 0) || (segs.at(-1)?.end ?? 0),
    url: String(meta.url ?? o.input),
    cover: String(meta.cover ?? ""),
    language: String(meta.language ?? o.lang),
    source,
    attempts,
    fetchedAt: new Date().toISOString(),
  };

  writeArtifacts(workDir, full, segs);
  return { meta: full, segs, workDir };
}

function ytInfo(url: string): Partial<Meta> {
  const r = sh("yt-dlp", ["--ignore-config", "--no-playlist", "--no-update", "--skip-download", "--dump-json", url], { timeout: 120_000 });
  if (r.status !== 0) return {};
  try {
    const j = JSON.parse(r.stdout.trim().split("\n")[0]);
    return { title: j.title, author: j.uploader ?? j.channel, description: j.description ?? "", duration: j.duration ?? 0, cover: j.thumbnail ?? "" };
  } catch { return {}; }
}

/** SRT/VTT → segments（滚动字幕去重只在 B站/YouTube 自动字幕上做，用 overlap 检测） */
function parseSubtitle(path: string): Seg[] {
  const raw = readFileSync(path, "utf-8").replace(/\r\n/g, "\n");
  const blocks = raw.split(/\n\s*\n/);
  const stamp = /(\d+):(\d{2}):(\d{2})[.,](\d{3})\s*-->\s*(\d+):(\d{2}):(\d{2})[.,](\d{3})/;
  const segs: Seg[] = [];
  for (const b of blocks) {
    const m = b.match(stamp);
    if (!m) continue;
    const toSec = (h: string, mi: string, s: string, ms: string) =>
      +h * 3600 + +mi * 60 + +s + +ms / 1000;
    const start = toSec(m[1], m[2], m[3], m[4]);
    const end = toSec(m[5], m[6], m[7], m[8]);
    const text = b.split("\n").filter((l) => !stamp.test(l) && !/^\d+$/.test(l.trim()))
      .join(" ")
      .replace(/<[^>]+>/g, "")
      .replace(/&amp;/g, "&").replace(/&lt;/g, "<").replace(/&gt;/g, ">")
      .replace(/&quot;/g, '"').replace(/&#39;/g, "'")
      .replace(/\s+/g, " ").trim();
    if (text) segs.push({ start, end, text });
  }
  if (!segs.length) throw new Error(`字幕文件解析后为 0 段: ${path}`);
  return segs;
}

function writeArtifacts(dir: string, meta: Meta, segs: Seg[]) {
  writeFileSync(join(dir, "meta.json"), JSON.stringify(meta, null, 2));
  writeFileSync(join(dir, "segments.json"), JSON.stringify(segs, null, 2));
  writeFileSync(join(dir, "transcript.txt"), segs.map((s) => s.text).join("\n") + "\n");
  writeFileSync(join(dir, "transcript.srt"),
    segs.map((s, i) => `${i + 1}\n${srtTime(s.start)} --> ${srtTime(s.end)}\n${s.text}`).join("\n\n") + "\n");
}

// ────────────────────────────── CLI ──────────────────────────────

function parseArgs(argv: string[]): Opts {
  const o: Opts = { input: "", lang: "zh", forceAsr: false, quiet: false };
  for (let i = 0; i < argv.length; i++) {
    const a = argv[i];
    const next = () => argv[++i];
    if (a === "--out") o.out = next();
    else if (a === "--lang") o.lang = next();
    else if (a === "--force-asr") o.forceAsr = true;
    else if (a === "--platform") o.platform = next() as Platform;
    else if (a === "--model-path") o.modelPath = next();
    else if (a === "--whisper-model") o.whisperModel = next();
    else if (a === "--json") o.quiet = true;
    else if (!a.startsWith("-")) o.input = a;
  }
  if (!o.input) { console.error("用法: bun fetch.ts <url-or-path> [--out dir] [--lang zh] [--force-asr] [--platform P] [--json]"); process.exit(2); }
  return o;
}

if (import.meta.main) {
  const o = parseArgs(process.argv.slice(2));
  try {
    const { meta, segs, workDir } = await fetchTranscript(o);
    if (o.quiet) {
      console.log(JSON.stringify({ ok: true, ...meta, segments: segs.length }));
    } else {
      console.error(`✓ ${meta.platform} | ${segs.length} 段 | 来源: ${meta.source} | ${meta.title}`);
      console.error(`  产物目录: ${workDir}`);
      console.log(meta.title);
    }
  } catch (e) {
    console.error(`✗ ${(e as Error).message}`);
    process.exit(1);
  }
}

export { fetchTranscript, parseSubtitle, detect, hms };
export type { Meta, Seg, Opts, Platform };

// ────────────────────────────── B站 AI 字幕修正 ──────────────────────────────
/**
 * B 站标着 ai-zh 的字幕实际常有成段的错乱：前后颠倒、句子重复、中英混杂乱码。
 * 只做安全修正：重叠去重 + 同文合并 + 过滤空/纯标点段。不改用词。
 */
function fixBilibiliAi(segs: Seg[]): { segs: Seg[]; dropped: number } {
  const out: Seg[] = [];
  let dropped = 0;
  for (const s of segs) {
    let text = s.text.replace(/\s+/g, " ").trim();
    if (!text || /^[\s\p{P}\p{S}]+$/u.test(text)) { dropped++; continue; }
    const prev = out.at(-1);
    if (prev) {
      // 整句完全重复
      if (prev.text === text) { prev.end = Math.max(prev.end, s.end); dropped++; continue; }
      // 包含关系：后一段包含了前一段（B站常见的滚动式拼接）
      if (text.startsWith(prev.text) && text.length > prev.text.length) {
        prev.text = text; prev.end = Math.max(prev.end, s.end); dropped++; continue;
      }
      if (prev.text.endsWith(text) && prev.text.length > text.length) { prev.end = Math.max(prev.end, s.end); dropped++; continue; }
    }
    out.push({ start: s.start, end: s.end, text });
  }
  return { segs: out, dropped };
}
