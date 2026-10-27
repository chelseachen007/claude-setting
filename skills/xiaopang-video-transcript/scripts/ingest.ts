#!/usr/bin/env bun
/**
 * 视频学习编排层 —— 一条命令从链接到 Obsidian 笔记
 *
 *   抓取层  xiaopang-video-transcript/scripts/fetch.ts  → 出 segments.json
 *   排版层  xiaopang-video-transcript/scripts/render.ts → 出分段正文
 *   落库层  本脚本                                       → 出 视频学习/{作者} — {标题}.md
 *
 * 本脚本不做整理（不提纯、不摘要、不写章节标题）——那是 media-transcriber 的活。
 * 它只保证：格式对、frontmatter 对、不覆盖已有笔记、不重复抓取。
 *
 * 用法:
 *   bun ingest.ts <url-or-path> [--mode raw|summary] [--title 副标题] [--duration 07:38]
 *                                [--job <已存在的抓取目录>] [--force] [--dry-run]
 *                                [--vault <库路径>] [--out <直接指定的输出 md>]
 *
 *   --mode raw      原始转录，段落 + [HH:MM:SS → HH:MM:SS]（默认）
 *   --mode summary  留出章节标题占位，供上层用 media-transcriber 填正文
 *   --job           跳过抓取，复用已有工作目录（重试/换模式时不重跑 ASR）
 */

import { existsSync, mkdirSync, readFileSync, writeFileSync } from "node:fs";
import { join, resolve } from "node:path";
import { fetchTranscript, type Meta, type Seg } from "./fetch.ts";
import { group, hms } from "./render.ts";

const VAULT_DEFAULT = "/Users/chenjie/Documents/study/github/Obsidian";

// ────────────────────────────── 参数 ──────────────────────────────

type Args = {
  input: string; mode: "raw" | "summary"; title?: string; duration?: string;
  job?: string; force: boolean; dryRun: boolean; vault: string; out?: string;
};

function parseArgs(argv: string[]): Args {
  const a: Args = {
    input: "", mode: "raw", force: false, dryRun: false, vault: VAULT_DEFAULT,
  };
  for (let i = 0; i < argv.length; i++) {
    const cur = argv[i];
    const next = () => argv[++i];
    if (cur === "--mode") a.mode = next() as Args["mode"];
    else if (cur === "--title") a.title = next();
    else if (cur === "--duration") a.duration = next();
    else if (cur === "--job") a.job = next();
    else if (cur === "--vault") a.vault = next();
    else if (cur === "--out") a.out = next();
    else if (cur === "--force") a.force = true;
    else if (cur === "--dry-run") a.dryRun = true;
    else if (!cur.startsWith("-")) a.input = cur;
  }
  if (!a.input && !a.job) {
    console.error("用法: bun ingest.ts <url-or-path> [--mode raw|summary] [--job dir] [--force] [--dry-run]");
    process.exit(2);
  }
  if (!["raw", "summary"].includes(a.mode)) {
    console.error(`✗ --mode 只支持 raw | summary，收到: ${a.mode}`);
    process.exit(2);
  }
  return a;
}

// ────────────────────────────── 工具 ──────────────────────────────

/** 文件名/标题里不能出现的字符。Obsidian 文件名禁 / 和 :，冒号是全角时保留中文习惯用 — 替换 */
function safeName(s: string): string {
  return s
    .replace(/[\\/:*?"<>|]/g, (m) => (m === ":" ? "：" : " "))
    .replace(/\s+/g, " ")
    .trim();
}

/** duration 秒 → "07:38" 或 "4:12:15"，与既有笔记写法一致（短于 1 小时不补零到小时） */
export function fmtDuration(sec: number): string {
  const s = Math.max(0, Math.round(sec));
  const h = Math.floor(s / 3600), m = Math.floor((s % 3600) / 60), ss = s % 60;
  return h > 0
    ? `${h}:${String(m).padStart(2, "0")}:${String(ss).padStart(2, "0")}`
    : `${String(m).padStart(2, "0")}:${String(ss).padStart(2, "0")}`;
}

/** 既有笔记的 source 取值是 official / whisper，ASR 一律记 whisper 保持兼容 */
function sourceLabel(source: "official" | "asr"): string {
  return source === "official" ? "official" : "whisper";
}

function yamlStr(s: string): string {
  // 库里既有笔记的 url / duration 都裸写（含冒号的 28:58 也裸写），
  // 只有含引号、井号、首尾空格等真正会破坏 YAML 的才加双引号。
  if (/["'#\n\r\t]/.test(s) || /^\s|\s$/.test(s) || s === "") {
    return `"${s.replace(/\\/g, "\\\\").replace(/"/g, '\\"')}"`;
  }
  return s;
}

// ────────────────────────────── 正文渲染 ──────────────────────────────

/**
 * raw 模式：段落 + 段尾时间戳。
 * 分段参数与既有笔记的时间戳分布对齐（8-10s 为主），见 render.ts 的 maxDur 说明。
 */
function renderRaw(segs: Seg[]): string {
  const blocks = group(segs, { maxChars: 140, gap: 0.8, maxDur: 12 });
  return blocks
    .map((b) => `${b.text} [${hms(b.start)} → ${hms(b.end)}]`)
    .join("\n\n");
}

/**
 * summary 模式：只留章节骨架，正文由 media-transcriber 填。
 * 不自己总结——抓取层冒充整理层是这次重构要消灭的问题。
 */
function renderSummarySkeleton(segs: Seg[], meta: Meta): string {
  const blocks = group(segs, { maxChars: 140, gap: 1.5, maxDur: 45 });
  const lines: string[] = [];
  lines.push("> 正文待整理：把工作目录里的 segments.json 连同本文件的章节骨架交给 media-transcriber，");
  lines.push("> 按 `references/writing-standard.md` 出稿后替换这一节。本文件只提供骨架与时间定位。");
  lines.push("");
  lines.push(`- 总段数：${segs.length}`);
  lines.push(`- 时长：${fmtDuration(meta.duration)}`);
  lines.push(`- 转录方式：${sourceLabel(meta.source)}（${
    meta.source === "official" ? "官方/自动字幕，可直接取用" : "本地 ASR，需按错别字词典核对人名家数"
  }）`);
  lines.push("");
  lines.push("## 章节占位");
  lines.push("");
  // 每 ~4 分钟给一个占位锚点，方便人工/上层填章节
  const step = 240;
  let next = 0;
  for (const b of blocks) {
    if (b.start >= next) {
      lines.push(`### [${hms(b.start)}] （待定主题）`);
      lines.push("");
      lines.push(`> ${b.text.slice(0, 60)}…`);
      lines.push("");
      next = b.start + step;
    }
  }
  return lines.join("\n");
}

// ────────────────────────────── 主流程 ──────────────────────────────

async function main() {
  const a = parseArgs(process.argv.slice(2));
  let meta: Meta;
  let segs: Seg[];
  let workDir: string;

  if (a.job) {
    workDir = resolve(a.job);
    const mp = join(workDir, "meta.json");
    const sp = join(workDir, "segments.json");
    if (!existsSync(mp) || !existsSync(sp)) {
      console.error(`✗ ${workDir} 里没有 meta.json / segments.json，不是有效的抓取工作目录`);
      process.exit(1);
    }
    meta = JSON.parse(readFileSync(mp, "utf-8"));
    segs = JSON.parse(readFileSync(sp, "utf-8"));
    if (!segs.length) { console.error(`✗ segments.json 为空`); process.exit(1); }
  } else {
    const jobDir = `/tmp/xvt/ingest-${Date.now()}`;
    const r = await fetchTranscript({
      input: a.input, out: jobDir, lang: "zh", forceAsr: false, quiet: true,
    });
    meta = r.meta as unknown as Meta;
    segs = r.segs;
    workDir = r.workDir;
  }

  // ── 决定标题 ──
  const author = safeName(meta.author || "");
  const mainTitle = safeName(a.title || meta.title || meta.url);
  const noteTitle = author ? `${author} — ${mainTitle}` : mainTitle;

  // ── 决定落点 ──
  const vaultVideoDir = join(a.vault, "视频学习");
  mkdirSync(vaultVideoDir, { recursive: true });
  const dest = a.out ? resolve(a.out) : join(vaultVideoDir, `${noteTitle}.md`);

  if (existsSync(dest) && !a.force) {
    console.error(`✗ 已存在同名笔记，不覆盖：${dest}`);
    console.error(`  确认要覆盖请加 --force；只想更新元信息请手改。`);
    console.error(`  抓取产物保留在：${workDir}`);
    process.exit(3);
  }

  // ── 组装 frontmatter ──
  const today = new Date().toISOString().slice(0, 10);
  const dur = a.duration || fmtDuration(meta.duration);
  const fm = [
    "---",
    "tags:",
    `title: ${yamlStr(noteTitle)}`,
    `date: ${today}`,
    `lastmod: ${today}`,
    `platform: ${yamlStr(meta.platform)}`,
    `url: ${yamlStr(meta.url)}`,
    ...(author ? [`author: ${yamlStr(author)}`] : []),
    `duration: ${yamlStr(dur)}`,
    `source: ${sourceLabel(meta.source)}`,
    "---",
  ].join("\n");

  const body = a.mode === "raw" ? renderRaw(segs) : renderSummarySkeleton(segs, meta);
  const content = `${fm}\n\n# ${mainTitle}\n\n${body}\n`;

  if (a.dryRun) {
    console.log(JSON.stringify({
      ok: true, dryRun: true, dest, noteTitle, mode: a.mode,
      segments: segs.length, source: sourceLabel(meta.source), workDir, bytes: content.length,
    }, null, 2));
    return;
  }

  writeFileSync(dest, content);
  console.log(JSON.stringify({
    ok: true, dest, noteTitle, mode: a.mode,
    segments: segs.length, source: sourceLabel(meta.source),
    workDir, bytes: content.length,
  }, null, 2));
}

if (import.meta.main) {
  main().catch((e) => { console.error(`✗ ${(e as Error).message}`); process.exit(1); });
}
