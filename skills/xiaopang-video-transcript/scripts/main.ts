#!/usr/bin/env bun
/**
 * 统一视频字幕提取工具
 * 支持 YouTube、Bilibili 等平台
 * 优先使用官方字幕，失败时自动使用 Whisper AI 生成
 */
import { existsSync, mkdirSync, writeFileSync } from "fs";
import { dirname, join, resolve } from "path";
import { spawnSync } from "child_process";

type Platform = "youtube" | "bilibili" | "unknown";
type Format = "text" | "srt" | "json";

interface Options {
  urlOrId: string;
  format: Format;
  output: string;
  outputDir: string;
  timestamps: boolean;
  refresh: boolean;
  forceWhisper: boolean;
  whisperModel: string;
  language: string;
  chapters: boolean;
  speakers: boolean;
}

interface TranscriptSegment {
  start: number;
  end: number;
  text: string;
}

interface VideoMeta {
  id: string;
  platform: Platform;
  title: string;
  author: string;
  description: string;
  duration: number;
  url: string;
  coverImage: string;
  language?: string;
}

interface TranscriptResult {
  segments: TranscriptSegment[];
  meta: VideoMeta;
  source: "official" | "whisper";
}

// --- Platform Detection ---

function detectPlatform(input: string): { platform: Platform; videoId: string } {
  input = input.replace(/\\/g, "").trim();

  // YouTube detection
  const ytPatterns = [
    /(?:youtube\.com\/watch\?.*v=|youtu\.be\/|youtube\.com\/embed\/|youtube\.com\/v\/|youtube\.com\/shorts\/)([a-zA-Z0-9_-]{11})/,
    /^([a-zA-Z0-9_-]{11})$/,
  ];
  for (const p of ytPatterns) {
    const m = input.match(p);
    if (m && (input.includes("youtube") || input.includes("youtu.be") || /^[a-zA-Z0-9_-]{11}$/.test(input))) {
      return { platform: "youtube", videoId: m[1] };
    }
  }

  // Bilibili detection - BV号
  const bvMatch = input.match(/BV[a-zA-Z0-9]{10}/);
  if (bvMatch) {
    return { platform: "bilibili", videoId: bvMatch[0] };
  }

  // Bilibili detection - URL
  if (input.includes("bilibili.com") || input.includes("b23.tv")) {
    const urlMatch = input.match(/bilibili\.com\/video\/(BV[a-zA-Z0-9]{10})/);
    if (urlMatch) return { platform: "bilibili", videoId: urlMatch[1] };

    // AV号
    const avMatch = input.match(/av(\d+)/i);
    if (avMatch) return { platform: "bilibili", videoId: `av${avMatch[1]}` };
  }

  return { platform: "unknown", videoId: input };
}

// --- Utility functions ---

function slugify(s: string): string {
  return s
    .toLowerCase()
    .replace(/[^\w\s-]/g, "")
    .replace(/\s+/g, "-")
    .replace(/-+/g, "-")
    .replace(/^-|-$/g, "") || "untitled";
}

function ts(t: number): string {
  const h = Math.floor(t / 3600);
  const m = Math.floor((t % 3600) / 60);
  const s = Math.floor(t % 60);
  return `${String(h).padStart(2, "0")}:${String(m).padStart(2, "0")}:${String(s).padStart(2, "0")}`;
}

function tsMs(t: number, sep: string): string {
  const h = Math.floor(t / 3600);
  const m = Math.floor((t % 3600) / 60);
  const s = Math.floor(t % 60);
  const ms = Math.round((t - Math.floor(t)) * 1000);
  return `${String(h).padStart(2, "0")}:${String(m).padStart(2, "0")}:${String(s).padStart(2, "0")}${sep}${String(ms).padStart(3, "0")}`;
}

function ensureDir(p: string) {
  const dir = dirname(p);
  if (!existsSync(dir)) mkdirSync(dir, { recursive: true });
}

// --- Bilibili Official Transcript (CDP 优先) ---

const CDP_PROXY = "http://127.0.0.1:3456";

async function cdpEval(targetId: string, js: string): Promise<any> {
  const r = await fetch(`${CDP_PROXY}/eval?target=${targetId}`, {
    method: "POST",
    body: js,
  });
  const json = await r.json();
  if (json.error) throw new Error(json.error);
  return json.value;
}

async function isCdpAvailable(): Promise<boolean> {
  try {
    const r = await fetch(`${CDP_PROXY}/targets`, { signal: AbortSignal.timeout(3000) });
    const text = await r.text();
    return text.startsWith("[");
  } catch {
    return false;
  }
}

/**
 * 通过 CDP 在 Bilibili 页面上下文中提取字幕。
 * 利用用户 Chrome 的登录态和 WBI 签名，无需手动处理认证。
 */
async function fetchBilibiliTranscriptViaCdp(bvid: string): Promise<{ segments: TranscriptSegment[]; meta: VideoMeta }> {
  // 1. 打开视频页面
  const newR = await fetch(`${CDP_PROXY}/new?url=https://www.bilibili.com/video/${bvid}`);
  const { targetId } = await newR.json() as { targetId: string };

  try {
    // 2. 等待页面渲染
    await new Promise(r => setTimeout(r, 4000));

    // 3. 从 __INITIAL_STATE__ 获取基础信息
    const infoRaw = await cdpEval(targetId, `JSON.stringify({
      aid: window.__INITIAL_STATE__?.aid,
      cid: window.__INITIAL_STATE__?.cid || window.__INITIAL_STATE__?.videoData?.cid,
      title: window.__INITIAL_STATE__?.videoData?.title,
      author: window.__INITIAL_STATE__?.videoData?.owner?.name,
      desc: window.__INITIAL_STATE__?.videoData?.desc,
      duration: window.__INITIAL_STATE__?.videoData?.duration,
      pic: window.__INITIAL_STATE__?.videoData?.pic,
    })`);
    const info = JSON.parse(infoRaw);
    if (!info.aid || !info.cid) throw new Error("页面信息提取失败");

    // 4. 在页面上下文调用 player API（自动带 Cookie 和签名）
    const playerRaw = await cdpEval(targetId, `
(async () => {
  const url = 'https://api.bilibili.com/x/player/wbi/v2?bvid=${bvid}&cid=${info.cid}&aid=${info.aid}';
  const res = await fetch(url, {credentials: 'include'});
  const data = await res.json();
  if (data.code !== 0) return JSON.stringify({error: data.message});
  const subs = data.data?.subtitle?.subtitles || [];
  return JSON.stringify(subs.map(s => ({
    subtitle_url: s.subtitle_url,
    lan: s.lan,
    lan_doc: s.lan_doc,
  })));
})()
`);
    if (playerRaw.startsWith?.('{"error"')) throw new Error(`Player API 失败: ${JSON.parse(playerRaw).error}`);
    const subtitles: Array<{ subtitle_url: string; lan: string; lan_doc: string }> = JSON.parse(playerRaw);
    if (!subtitles.length) throw new Error("该视频没有官方字幕");

    // 5. 选择字幕语言
    const target = subtitles.find(s => s.lan === "zh-CN") ||
                   subtitles.find(s => s.lan.startsWith("zh")) ||
                   subtitles[0];
    const subtitleUrl = target.subtitle_url.startsWith("http") ? target.subtitle_url : `https:${target.subtitle_url}`;

    // 6. 下载字幕内容
    const subRaw = await cdpEval(targetId, `
(async () => {
  const res = await fetch('${subtitleUrl}');
  const data = await res.json();
  return JSON.stringify(data.body || []);
})()
`);
    const body: Array<{ from: number; to: number; content: string }> = JSON.parse(subRaw);

    const segments: TranscriptSegment[] = body.map(s => ({
      start: s.from,
      end: s.to,
      text: s.content,
    }));

    const meta: VideoMeta = {
      id: bvid,
      platform: "bilibili",
      title: info.title || "",
      author: info.author || "",
      description: info.desc || "",
      duration: info.duration || 0,
      url: `https://www.bilibili.com/video/${bvid}`,
      coverImage: info.pic || "",
      language: target.lan,
    };

    return { segments, meta };
  } finally {
    // 始终关闭 tab
    await fetch(`${CDP_PROXY}/close?target=${targetId}`).catch(() => {});
  }
}

/**
 * 直接调用 Bilibili API 获取字幕（降级方案，不依赖 CDP）。
 */
async function fetchBilibiliTranscriptViaApi(bvid: string): Promise<{ segments: TranscriptSegment[]; meta: VideoMeta }> {
  const headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
    "Referer": "https://www.bilibili.com",
  };

  const videoR = await fetch(`https://api.bilibili.com/x/web-interface/view?bvid=${bvid}`, { headers });
  const videoData = await videoR.json();
  if (videoData.code !== 0) throw new Error(`获取视频信息失败: ${videoData.message}`);

  const info = videoData.data;
  const playerR = await fetch(`https://api.bilibili.com/x/player/wbi/v2?aid=${info.aid}&cid=${info.cid}`, { headers });
  const playerData = await playerR.json();
  if (playerData.code !== 0) throw new Error(`获取播放器信息失败: ${playerData.message}`);

  const subtitles = playerData.data?.subtitle?.subtitles || [];
  if (!subtitles.length) throw new Error("该视频没有官方字幕");

  const targetSubtitle = subtitles.find((s: any) => s.lan === "zh-CN") ||
                         subtitles.find((s: any) => s.lan.startsWith("zh")) ||
                         subtitles[0];

  const subtitleUrl = targetSubtitle.subtitle_url.startsWith("http")
    ? targetSubtitle.subtitle_url
    : `https:${targetSubtitle.subtitle_url}`;

  const subR = await fetch(subtitleUrl, { headers });
  const subData = await subR.json();

  return {
    segments: (subData.body || []).map((s: any) => ({ start: s.from, end: s.to, text: s.content })),
    meta: {
      id: bvid,
      platform: "bilibili",
      title: info.title || "",
      author: info.owner?.name || "",
      description: info.desc || "",
      duration: info.duration || 0,
      url: `https://www.bilibili.com/video/${bvid}`,
      coverImage: info.pic || "",
      language: targetSubtitle.lan,
    },
  };
}

async function fetchBilibiliTranscript(bvid: string): Promise<{ segments: TranscriptSegment[]; meta: VideoMeta }> {
  // CDP 优先：利用用户 Chrome 登录态，无需处理 WBI 签名
  if (await isCdpAvailable()) {
    try {
      console.error("  → 使用 CDP 模式获取字幕（浏览器登录态）...");
      return await fetchBilibiliTranscriptViaCdp(bvid);
    } catch (e) {
      console.error(`  → CDP 模式失败: ${(e as Error).message}，降级到直接 API...`);
    }
  } else {
    console.error("  → CDP 不可用，使用直接 API 模式...");
  }
  return fetchBilibiliTranscriptViaApi(bvid);
}

// --- Whisper AI Transcript ---

function runWhisper(url: string, model: string, language: string, outputDir: string): TranscriptSegment[] {
  const scriptPath = resolve(join(dirname(new URL(import.meta.url).pathname), "whisper_transcribe.py"));

  const result = spawnSync("python3", [
    scriptPath,
    url,
    "--model", model,
    "--language", language,
    "--output-dir", outputDir,
    "--format", "json",
  ], {
    encoding: "utf-8",
    stdio: ["inherit", "pipe", "pipe"],
  });

  if (result.status !== 0) {
    throw new Error(`Whisper failed: ${result.stderr || result.stdout}`);
  }

  // Parse JSON from stdout
  const stdout = result.stdout.trim();
  const jsonMatch = stdout.match(/\[.*\]/s);
  if (!jsonMatch) throw new Error(`Could not parse Whisper output: ${stdout}`);

  return JSON.parse(jsonMatch[0]);
}

// --- Format functions ---

function formatSrt(segments: TranscriptSegment[]): string {
  return segments
    .map((s, i) => `${i + 1}\n${tsMs(s.start, ",")} --> ${tsMs(s.end, ",")}\n${s.text}`)
    .join("\n\n") + "\n";
}

function formatMarkdown(segments: TranscriptSegment[], meta: VideoMeta, timestamps: boolean): string {
  let md = "---\n";
  md += `title: ${meta.title}\n`;
  md += `author: ${meta.author}\n`;
  md += `platform: ${meta.platform}\n`;
  md += `url: ${meta.url}\n`;
  if (meta.language) md += `language: ${meta.language}\n`;
  md += "---\n\n";
  md += `# ${meta.title}\n\n`;

  // Group into paragraphs
  const paras: { text: string; start: number; end: number }[] = [];
  let buf: TranscriptSegment[] = [];

  for (let i = 0; i < segments.length; i++) {
    buf.push(segments[i]);
    const last = i === segments.length - 1;
    const gap = !last && segments[i + 1].start - segments[i].end > 2;

    if (last || gap || buf.length >= 5) {
      paras.push({
        text: buf.map(s => s.text).join(""),
        start: buf[0].start,
        end: buf[buf.length - 1].end,
      });
      buf = [];
    }
  }

  for (const p of paras) {
    if (timestamps) {
      md += `${p.text} [${ts(p.start)} → ${ts(p.end)}]\n\n`;
    } else {
      md += `${p.text}\n\n`;
    }
  }

  return md.trimEnd() + "\n";
}

// --- Main ---

async function getTranscript(opts: Options): Promise<TranscriptResult> {
  const { platform, videoId } = detectPlatform(opts.urlOrId);

  if (platform === "unknown") {
    throw new Error(`无法识别的视频平台: ${opts.urlOrId}`);
  }

  let segments: TranscriptSegment[] = [];
  let meta: VideoMeta;
  let source: "official" | "whisper" = "official";

  // Try official transcript first (unless force whisper)
  if (!opts.forceWhisper) {
    try {
      console.error(`尝试获取官方字幕 (${platform})...`);

      if (platform === "bilibili") {
        const result = await fetchBilibiliTranscript(videoId);
        segments = result.segments;
        meta = result.meta;
      } else if (platform === "youtube") {
        // YouTube 使用 youtube.ts 脚本处理
        const youtubeScript = resolve(join(dirname(new URL(import.meta.url).pathname), "youtube.ts"));
        const args = [youtubeScript, videoId];
        if (opts.format === "srt") args.push("--format", "srt");
        if (!opts.timestamps) args.push("--no-timestamps");
        if (!opts.chapters) args.push("--no-chapters");
        if (opts.speakers) args.push("--speakers");
        if (opts.refresh) args.push("--refresh");
        if (opts.output) args.push("--output", opts.output);
        if (opts.outputDir) args.push("--output-dir", opts.outputDir);

        const result = spawnSync("bun", args, {
          encoding: "utf-8",
          stdio: ["inherit", "pipe", "pipe"],
        });

        if (result.status !== 0) {
          throw new Error(result.stderr || result.stdout || "YouTube 脚本执行失败");
        }

        // 输出文件路径
        const outputPath = result.stdout.trim();
        console.log(outputPath);
        process.exit(0);
      }

      console.error(`✓ 官方字幕获取成功，共 ${segments.length} 个片段`);
      source = "official";
    } catch (e) {
      console.error(`✗ 官方字幕获取失败: ${(e as Error).message}`);
      console.error(`切换到 Whisper AI 语音识别...`);
    }
  }

  // Fallback to Whisper if no official transcript
  if (segments.length === 0 || opts.forceWhisper) {
    const videoUrl = platform === "bilibili"
      ? `https://www.bilibili.com/video/${videoId}`
      : `https://www.youtube.com/watch?v=${videoId}`;

    segments = runWhisper(videoUrl, opts.whisperModel, opts.language, opts.outputDir);

    // Get basic meta for Whisper
    meta = {
      id: videoId,
      platform,
      title: videoId,
      author: "",
      description: "",
      duration: segments.length > 0 ? segments[segments.length - 1].end : 0,
      url: videoUrl,
      coverImage: "",
      language: opts.language,
    };

    console.error(`✓ Whisper AI 识别完成，共 ${segments.length} 个片段`);
    source = "whisper";
  }

  return { segments: segments!, meta: meta!, source };
}

async function main() {
  const args = process.argv.slice(2);
  if (args.length === 0 || args.includes("-h") || args.includes("--help")) {
    console.log(`Usage: bun main.ts <video-url-or-id> [options]

统一视频字幕提取工具 - 支持 YouTube、Bilibili 等平台

选项:
  --format <fmt>        输出格式: text, srt, json (默认: text)
  --output <path>       输出文件路径
  --output-dir <dir>    输出目录 (默认: video-transcript)
  --no-timestamps       不包含时间戳
  --no-chapters         不进行章节分割 (仅 YouTube)
  --speakers            说话人识别模式 (仅 YouTube)
  --refresh             强制重新获取
  --whisper             强制使用 Whisper AI
  --whisper-model <m>   Whisper 模型: tiny, base, small, medium, large (默认: small)
  --language <lang>     音频语言 (默认: zh)
  -h, --help            显示帮助

示例:
  bun main.ts "https://www.youtube.com/watch?v=xxx"
  bun main.ts "https://www.bilibili.com/video/BV1xx411c7mD"
  bun main.ts BV1xx411c7mD --whisper --whisper-model medium
`);
    process.exit(args.length === 0 ? 1 : 0);
  }

  const opts: Options = {
    urlOrId: "",
    format: "text",
    output: "",
    outputDir: "",
    timestamps: true,
    refresh: false,
    forceWhisper: false,
    whisperModel: "small",
    language: "zh",
    chapters: true,
    speakers: false,
  };

  for (let i = 0; i < args.length; i++) {
    const arg = args[i];
    if (arg === "--format") {
      const v = args[++i]?.toLowerCase();
      if (v === "text" || v === "srt" || v === "json") opts.format = v as Format;
    } else if (arg === "--output" || arg === "-o") {
      opts.output = args[++i] || "";
    } else if (arg === "--output-dir") {
      opts.outputDir = args[++i] || "";
    } else if (arg === "--no-timestamps") {
      opts.timestamps = false;
    } else if (arg === "--no-chapters") {
      opts.chapters = false;
    } else if (arg === "--speakers") {
      opts.speakers = true;
    } else if (arg === "--refresh") {
      opts.refresh = true;
    } else if (arg === "--whisper") {
      opts.forceWhisper = true;
    } else if (arg === "--whisper-model") {
      opts.whisperModel = args[++i] || "small";
    } else if (arg === "--language" || arg === "-l") {
      opts.language = args[++i] || "zh";
    } else if (!arg.startsWith("-")) {
      opts.urlOrId = arg;
    }
  }

  if (!opts.urlOrId) {
    console.error("错误: 请提供视频 URL 或 ID");
    process.exit(1);
  }

  // YouTube 使用独立的 youtube.ts 脚本
  const { platform } = detectPlatform(opts.urlOrId);
  if (platform === "youtube" && !opts.forceWhisper) {
    const youtubeScript = resolve(join(dirname(new URL(import.meta.url).pathname), "youtube.ts"));
    const ytArgs = [youtubeScript, opts.urlOrId];
    if (opts.format === "srt") ytArgs.push("--format", "srt");
    if (!opts.timestamps) ytArgs.push("--no-timestamps");
    if (!opts.chapters) ytArgs.push("--no-chapters");
    if (opts.speakers) ytArgs.push("--speakers");
    if (opts.refresh) ytArgs.push("--refresh");
    if (opts.output) ytArgs.push("--output", opts.output);
    if (opts.outputDir) ytArgs.push("--output-dir", opts.outputDir);

    const result = spawnSync("bun", ytArgs, {
      encoding: "utf-8",
      stdio: "inherit",
    });

    process.exit(result.status || 0);
  }

  // Bilibili 或 Whisper 模式
  const baseDir = resolve(opts.outputDir || "video-transcript");
  const { segments, meta, source } = await getTranscript(opts);

  // Create output directory
  const videoDir = join(baseDir, slugify(meta.author), slugify(meta.title));
  ensureDir(join(videoDir, "dummy"));

  // Save raw data
  writeFileSync(join(videoDir, "transcript.json"), JSON.stringify(segments, null, 2));
  writeFileSync(join(videoDir, "meta.json"), JSON.stringify({ ...meta, source }, null, 2));

  // Format output
  let content: string;
  let ext: string;

  if (opts.format === "srt") {
    content = formatSrt(segments);
    ext = "srt";
  } else if (opts.format === "json") {
    content = JSON.stringify(segments, null, 2);
    ext = "json";
  } else {
    content = formatMarkdown(segments, meta, opts.timestamps);
    ext = "md";
  }

  const outputPath = opts.output || join(videoDir, `transcript.${ext}`);
  ensureDir(outputPath);
  writeFileSync(outputPath, content);

  console.log(outputPath);
}

main();
