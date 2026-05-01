#!/usr/bin/env bun
/**
 * 统一视频字幕提取工具
 * 支持 YouTube、Bilibili 等平台
 * 优先使用官方字幕，失败时自动使用 Whisper AI 生成
 */
import { existsSync, mkdirSync, writeFileSync, unlinkSync, rmSync } from "fs";
import { dirname, join, resolve } from "path";
import { tmpdir } from "os";
import { spawnSync } from "child_process";

type Platform = "youtube" | "bilibili" | "douyin" | "xiaoyuzhou" | "ximalaya" | "unknown";
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

  // Douyin detection
  if (input.includes("douyin.com") || input.includes("v.douyin.com")) {
    // Extract video ID from full URL or short URL
    const dyMatch = input.match(/douyin\.com\/video\/(\d+)/);
    if (dyMatch) return { platform: "douyin", videoId: dyMatch[1] };
    // Short URL — will resolve to full URL via CDP later
    return { platform: "douyin", videoId: input };
  }

  // Xiaoyuzhou (小宇宙) podcast detection
  if (input.includes("xiaoyuzhoufm.com") || input.includes("xiaoyuzhou.com")) {
    const epMatch = input.match(/xiaoyuzhoufm\.com\/episode\/([a-zA-Z0-9]+)/);
    if (epMatch) return { platform: "xiaoyuzhou", videoId: epMatch[1] };
    return { platform: "xiaoyuzhou", videoId: input };
  }

  // Ximalaya (喜马拉雅) podcast detection
  if (input.includes("ximalaya.com") || input.includes("xmly.com")) {
    const xmMatch = input.match(/ximalaya\.com\/\w+\/(\d+\/\d+)/);
    if (xmMatch) return { platform: "ximalaya", videoId: xmMatch[1] };
    return { platform: "ximalaya", videoId: input };
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

// --- Douyin Video Extraction (CDP only) ---

interface DouyinVideoInfo {
  videoUrl: string;
  title: string;
  author: string;
  videoId: string;
}

interface PodcastAudioInfo {
  audioUrl: string;
  title: string;
  author: string;
  description: string;
  episodeId: string;
  targetId: string;
}

/**
 * 下载文件到本地
 */
function downloadFile(url: string, outputPath: string) {
  const result = spawnSync("curl", ["-L", "-s", "-o", outputPath, url], { timeout: 120_000 });
  if (result.status !== 0) {
    throw new Error(`下载失败: ${result.stderr?.toString() || "unknown error"}`);
  }
  if (!existsSync(outputPath)) {
    throw new Error(`下载失败: 文件未创建`);
  }
}

/**
 * 通过 CDP 在播客页面中提取音频播放地址和元信息。
 * 小宇宙和喜马拉雅都在 <audio> 元素中加载音频。
 */
async function fetchPodcastAudioViaCdp(urlOrId: string, platform: string): Promise<PodcastAudioInfo> {
  if (!(await isCdpAvailable())) {
    const label = platform === "xiaoyuzhou" ? "小宇宙" : "喜马拉雅";
    throw new Error(`${label}播客提取需要 CDP（Chrome 远程调试）。请确保 Chrome 已开启远程调试且 CDP Proxy 运行中。`);
  }

  // 1. 打开页面
  const newR = await fetch(`${CDP_PROXY}/new?url=${encodeURIComponent(urlOrId)}`);
  const { targetId } = await newR.json() as { targetId: string };

  // 2. 等待页面渲染
  await new Promise(r => setTimeout(r, 5000));

  // 3. 提取音频 URL 和元信息
  const evalScript = platform === "xiaoyuzhou"
    ? `JSON.stringify({
        audioUrl: document.querySelector("audio")?.currentSrc || document.querySelector("audio source")?.src || "",
        title: document.querySelector("h1")?.textContent?.trim() || document.title,
        author: document.querySelector('[class*="author"]')?.textContent?.trim() || "",
        description: document.querySelector('meta[name="description"]')?.content || "",
      })`
    : `JSON.stringify({
        audioUrl: document.querySelector("audio")?.currentSrc || document.querySelector("audio source")?.src || "",
        title: document.querySelector("h1")?.textContent?.trim() || document.querySelector(".title")?.textContent?.trim() || document.title,
        author: document.querySelector(".username")?.textContent?.trim() || document.querySelector('[class*="host"]')?.textContent?.trim() || "",
        description: document.querySelector('meta[name="description"]')?.content || "",
      })`;

  const infoRaw = await cdpEval(targetId, evalScript);
  const info = JSON.parse(infoRaw);
  if (!info.audioUrl) {
    await fetch(`${CDP_PROXY}/close?target=${targetId}`).catch(() => {});
    throw new Error("未找到音频元素或音频 URL 为空");
  }

  // 4. 提取 episode ID
  const episodeId = urlOrId.match(/episode\/([a-zA-Z0-9]+)/)?.[1]
    || urlOrId.match(/(\d+\/\d+)$/)?.[1]
    || "unknown";

  return { ...info, episodeId, targetId };
}

/**
 * 通过 CDP 在抖音页面中提取视频播放地址和元信息。
 * yt-dlp 的抖音提取器有 bug（需要 fresh cookies），CDP 是唯一可靠方式。
 * 视频地址有时效性，提取后需立即下载，且必须带 Referer 头。
 */
async function fetchDouyinVideoViaCdp(urlOrId: string): Promise<DouyinVideoInfo & { targetId: string }> {
  if (!(await isCdpAvailable())) {
    throw new Error("抖音视频提取需要 CDP（Chrome 远程调试）。请确保 Chrome 已开启远程调试且 CDP Proxy 运行中。");
  }

  // 确定 URL：如果有完整 URL 直接用，否则当作视频 ID
  const pageUrl = urlOrId.includes("douyin.com")
    ? urlOrId
    : `https://www.douyin.com/video/${urlOrId}`;

  // 1. 打开页面
  const newR = await fetch(`${CDP_PROXY}/new?url=${encodeURIComponent(pageUrl)}`);
  const { targetId } = await newR.json() as { targetId: string };

  // 2. 等待页面渲染（短视频通常加载快）
  await new Promise(r => setTimeout(r, 5000));

  // 3. 提取视频 URL 和元信息
  const infoRaw = await cdpEval(targetId, `JSON.stringify({
    videoUrl: document.querySelector("video")?.currentSrc || document.querySelector("video")?.src || "",
    title: document.title.replace(/ - 抖音$/, "").replace(/ - 抖音精选$/, ""),
    author: document.querySelector('.author-card-user-name')?.textContent
           || document.querySelector('[data-e2e="user-info"] h3')?.textContent
           || "",
  })`);
  const info = JSON.parse(infoRaw);
  if (!info.videoUrl) {
    await fetch(`${CDP_PROXY}/close?target=${targetId}`).catch(() => {});
    throw new Error("未找到视频元素或视频 URL 为空");
  }

  // 4. 从页面 URL 获取视频 ID
  const page = await (await fetch(`${CDP_PROXY}/info?target=${targetId}`)).json() as { url: string };
  const idMatch = page.url.match(/video\/(\d+)/);
  const videoId = idMatch ? idMatch[1] : "unknown";

  return {
    videoUrl: info.videoUrl,
    title: info.title || videoId,
    author: info.author || "",
    videoId,
    targetId,
  };
}

/**
 * 下载抖音视频。必须带 Referer: https://www.douyin.com/ 头，否则 CDN 会拒绝。
 */
function downloadDouyinVideo(videoUrl: string, outputPath: string): void {
  const result = spawnSync("curl", [
    "-L", "-o", outputPath,
    "--fail",
    "-H", "Referer: https://www.douyin.com/",
    "-H", "User-Agent: Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36",
    "--max-time", "120",
    videoUrl,
  ], { encoding: "utf-8", stdio: ["inherit", "pipe", "pipe"] });

  if (result.status !== 0) {
    throw new Error(`下载抖音视频失败: ${result.stderr || "未知错误"}`);
  }
}

/**
 * 用 ffmpeg 从视频文件提取 WAV 音频
 */
function extractAudioFromVideo(videoPath: string, wavPath: string): void {
  const result = spawnSync("ffmpeg", [
    "-y", "-i", videoPath,
    "-vn", "-acodec", "pcm_s16le",
    "-ar", "16000", "-ac", "1",
    wavPath,
  ], { encoding: "utf-8", stdio: ["inherit", "pipe", "pipe"] });

  if (result.status !== 0) {
    throw new Error(`ffmpeg 提取音频失败: ${result.stderr || "未知错误"}`);
  }
}

/**
 * 用 faster-whisper 直接在进程内转写（不走 whisper_transcribe.py 子进程）。
 * 抖音场景：已有本地音频文件，不需要 yt-dlp 下载。
 */
const WHISPER_MODELS = ["tiny", "base", "small", "medium", "large"] as const;

function transcribeLocalFile(wavPath: string, model: string, language: string): TranscriptSegment[] {
  if (!WHISPER_MODELS.includes(model as any)) throw new Error(`Invalid whisper model: ${model}`);
  if (!/^[a-z]{2}(-[A-Za-z]{2,4})?$/.test(language)) throw new Error(`Invalid language code: ${language}`);

  const safeWav = wavPath.replace(/"/g, '\\"');
  const script = `
import sys, json
sys.stdout.reconfigure(line_buffering=True)
from faster_whisper import WhisperModel
print("Loading model...", file=sys.stderr)
model = WhisperModel("${model}", device="cpu", compute_type="int8")
print("Transcribing...", file=sys.stderr)
segs, info = model.transcribe("${safeWav}", language="${language}", vad_filter=True, vad_parameters=dict(min_silence_duration_ms=500))
results = []
for s in segs:
    results.append({"start": round(s.start, 2), "end": round(s.end, 2), "text": s.text.strip()})
    if len(results) % 50 == 0:
        print(f"  ... {len(results)} segments, {s.end:.0f}s / {info.duration:.0f}s", file=sys.stderr)
print(json.dumps(results, ensure_ascii=False))
`.trim();

  const tmpScript = join(tmpdir(), `douyin-whisper-${Date.now()}.py`);
  writeFileSync(tmpScript, script);

  try {
    const result = spawnSync("python3", [tmpScript], {
      encoding: "utf-8",
      stdio: ["inherit", "pipe", "pipe"],
      timeout: 600_000,
    });

    if (result.status !== 0) {
      throw new Error(`Whisper 转写失败: ${result.stderr || result.stdout}`);
    }

    const stdout = result.stdout.trim();
    const jsonMatch = stdout.match(/\[.*\]/s);
    if (!jsonMatch) throw new Error(`无法解析 Whisper 输出: ${stdout.slice(0, 200)}`);
    return JSON.parse(jsonMatch[0]);
  } finally {
    try { unlinkSync(tmpScript); } catch {}
  }
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

  // Douyin: only Whisper path via CDP video extraction
  if (platform === "douyin") {
    console.error("抖音视频：通过 CDP 提取视频 URL → Whisper 转写...");
    const tmpDir = join("/tmp", `douyin-${Date.now()}`);
    mkdirSync(tmpDir, { recursive: true });

    try {
      // 1. CDP 提取视频信息
      const dyInfo = await fetchDouyinVideoViaCdp(opts.urlOrId);
      console.error(`  标题: ${dyInfo.title}`);
      console.error(`  作者: ${dyInfo.author}`);

      // 2. 立即下载视频（URL 有时效性，需带 Referer）
      const videoPath = join(tmpDir, "video.mp4");
      console.error("  下载视频中...");
      downloadDouyinVideo(dyInfo.videoUrl, videoPath);

      // 3. 关闭 CDP tab
      await fetch(`${CDP_PROXY}/close?target=${dyInfo.targetId}`).catch(() => {});

      // 4. 提取音频
      const wavPath = join(tmpDir, "audio.wav");
      console.error("  提取音频...");
      extractAudioFromVideo(videoPath, wavPath);

      // 5. Whisper 转写
      console.error(`  Whisper 转写中 (模型: ${opts.whisperModel})...`);
      segments = transcribeLocalFile(wavPath, opts.whisperModel, opts.language);
      console.error(`✓ 抖音视频转写完成，共 ${segments.length} 个片段`);

      meta = {
        id: dyInfo.videoId,
        platform: "douyin",
        title: dyInfo.title,
        author: dyInfo.author,
        description: "",
        duration: segments.length > 0 ? segments[segments.length - 1].end : 0,
        url: `https://www.douyin.com/video/${dyInfo.videoId}`,
        coverImage: "",
        language: opts.language,
      };
      source = "whisper";

      return { segments, meta, source };
    } catch (e) {
      // 尝试关闭可能残留的 CDP tab
      try { rmSync(tmpDir, { recursive: true }); } catch {}
      throw new Error(`抖音视频处理失败: ${(e as Error).message}`);
    } finally {
      try { rmSync(tmpDir, { recursive: true }); } catch {}
    }
  }

  // Podcast platforms (xiaoyuzhou, ximalaya): CDP extract audio → Whisper
  if (platform === "xiaoyuzhou" || platform === "ximalaya") {
    const platformLabel = platform === "xiaoyuzhou" ? "小宇宙" : "喜马拉雅";
    console.error(`${platformLabel}播客：通过 CDP 提取音频 URL → Whisper 转写...`);
    const tmpDir = join("/tmp", `${platform}-${Date.now()}`);
    mkdirSync(tmpDir, { recursive: true });

    try {
      // 1. CDP 打开播客页面，提取音频 URL 和元数据
      const audioInfo = await fetchPodcastAudioViaCdp(opts.urlOrId, platform);
      console.error(`  标题: ${audioInfo.title}`);
      console.error(`  作者: ${audioInfo.author}`);

      // 2. 下载音频
      const audioPath = join(tmpDir, "audio.mp3");
      console.error("  下载音频中...");
      downloadFile(audioInfo.audioUrl, audioPath);

      // 3. 关闭 CDP tab
      if (audioInfo.targetId) {
        await fetch(`${CDP_PROXY}/close?target=${audioInfo.targetId}`).catch(() => {});
      }

      // 4. 转换为 WAV
      const wavPath = join(tmpDir, "audio.wav");
      console.error("  转换音频格式...");
      extractAudioFromVideo(audioPath, wavPath);

      // 5. Whisper 转写
      console.error(`  Whisper 转写中 (模型: ${opts.whisperModel})...`);
      segments = transcribeLocalFile(wavPath, opts.whisperModel, opts.language);
      console.error(`✓ ${platformLabel}播客转写完成，共 ${segments.length} 个片段`);

      meta = {
        id: audioInfo.episodeId,
        platform: platform,
        title: audioInfo.title,
        author: audioInfo.author,
        description: audioInfo.description || "",
        duration: segments.length > 0 ? segments[segments.length - 1].end : 0,
        url: opts.urlOrId,
        coverImage: "",
        language: opts.language,
      };
      source = "whisper";

      return { segments, meta, source };
    } catch (e) {
      try { rmSync(tmpDir, { recursive: true }); } catch {}
      throw new Error(`${platformLabel}播客处理失败: ${(e as Error).message}`);
    } finally {
      try { rmSync(tmpDir, { recursive: true }); } catch {}
    }
  }

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

统一视频字幕提取工具 - 支持 YouTube、Bilibili、抖音(Douyin) 平台

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
  bun main.ts "https://v.douyin.com/xxxxx/"
  bun main.ts "https://v.douyin.com/xxxxx/" --whisper-model medium
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
