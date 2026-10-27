#!/usr/bin/env bun
/**
 * 分段与排版（抓取层的最后一公里）
 *
 * 把 segments.json 排成「可读的段落 + 时间戳」Markdown，供两种下游用法：
 *   --mode raw      原始转录：逐字保留，按停顿/长度切段，段尾挂 [HH:MM:SS → HH:MM:SS]
 *   --mode speakers 说话人转录：同上，但在明显换人处插入「**说话人 N**」占位
 *
 * 不做任何措辞修改。要清洗/整理请交给上层（media-transcriber 或 model）。
 *
 * 用法:
 *   bun render.ts <workdir> [--mode raw|speakers] [--max-chars 120] [--gap 0.8] [--out file]
 */

import { existsSync, readFileSync, writeFileSync } from "node:fs";
import { join } from "node:path";

type Seg = { start: number; end: number; text: string };

export function hms(t: number): string {
  const s = Math.max(0, Math.floor(t));
  return [Math.floor(s / 3600), Math.floor((s % 3600) / 60), s % 60]
    .map((n) => String(n).padStart(2, "0")).join(":");
}

/**
 * 把细碎字幕合并成可读段落。
 * - gap: 相邻段间隔超过该秒数就断段（自然停顿）
 * - maxChars: 单段字数上限，避免出现超长一段
 * - maxDur: 单段时长上限（默认 12s：与用户既有视频学习笔记的段长分布一致，8-10s 为主）
 */
export function group(
  segs: Seg[],
  { gap = 0.8, maxChars = 120, maxDur = 12 }: { gap?: number; maxChars?: number; maxDur?: number } = {},
): { start: number; end: number; text: string }[] {
  const out: { start: number; end: number; text: string }[] = [];
  let cur: { start: number; end: number; text: string } | null = null;

  for (const s of segs) {
    const t = s.text.trim();
    if (!t) continue;
    if (cur) {
      const gapOk = s.start - cur.end <= gap;
      const sizeOk = cur.text.length + t.length <= maxChars;
      const durOk = s.end - cur.start <= maxDur;
      if (gapOk && sizeOk && durOk) {
        // 中文不加空格，其余语言补空格
        const needSpace = /[A-Za-z0-9]$/.test(cur.text) && /^[A-Za-z0-9]/.test(t);
        cur.text += (needSpace ? " " : "") + t;
        cur.end = Math.max(cur.end, s.end);
        continue;
      }
      out.push(cur);
    }
    cur = { start: s.start, end: s.end, text: t };
  }
  if (cur) out.push(cur);
  return out;
}

/**
 * 说话人占位：只在「有明显停顿」处打标，不猜身份。
 * 明确写「待补」，避免让下游误以为已识别。
 */
function withSpeakerHints(blocks: { start: number; end: number; text: string }[], gap = 1.5) {
  return blocks.map((b, i) => {
    const prev = blocks[i - 1];
    const newSpeaker = prev && b.start - prev.end >= gap ? true : i === 0;
    return { ...b, newSpeaker: !!newSpeaker };
  });
}

export function render(
  blocks: { start: number; end: number; text: string; newSpeaker?: boolean }[],
  mode: "raw" | "speakers",
): string {
  const lines: string[] = [];
  let speaker = 1;
  for (let i = 0; i < blocks.length; i++) {
    const b = blocks[i];
    if (mode === "speakers" && b.newSpeaker && i > 0) {
      speaker++;
      lines.push(`\n**说话人 ${speaker}**（待核对）\n`);
    }
    lines.push(`${b.text} [${hms(b.start)} → ${hms(b.end)}]\n`);
  }
  return lines.join("\n");
}

if (import.meta.main) {
  const argv = process.argv.slice(2);
  const dir = argv.find((a) => !a.startsWith("-"));
  if (!dir) {
    console.error("用法: bun render.ts <workdir> [--mode raw|speakers] [--max-chars 120] [--gap 0.8] [--out file]");
    process.exit(2);
  }
  const get = (flag: string) => {
    const i = argv.indexOf(flag);
    return i >= 0 ? argv[i + 1] : undefined;
  };
  const mode = (get("--mode") ?? "raw") as "raw" | "speakers";
  const maxChars = Number(get("--max-chars") ?? 120);
  const gap = Number(get("--gap") ?? 0.8);

  const segFile = join(dir, "segments.json");
  if (!existsSync(segFile)) {
    console.error(`✗ 找不到 ${segFile}`);
    process.exit(1);
  }
  const segs: Seg[] = JSON.parse(readFileSync(segFile, "utf-8"));
  const blocks = group(segs, { maxChars, gap });
  const out = render(mode === "speakers" ? withSpeakerHints(blocks) : blocks, mode);

  const dest = get("--out") ?? join(dir, mode === "speakers" ? "transcript.speakers.md" : "transcript.grouped.md");
  writeFileSync(dest, out);
  console.log(JSON.stringify({ ok: true, file: dest, blocks: blocks.length, segments: segs.length }));
}
