#!/usr/bin/env bun
/**
 * 错别字修正：只对 ASR 产出的文本做替换，官方字幕默认不动。
 *
 * 词典在 config/whisper-typo-fixes.json，格式 { "category": [["错", "对"], ...] }。
 * 长的替换优先，避免「胡思」被「胡思派」抢先吃掉。
 *
 * 用法:
 *   bun fix_typos.ts <file-or-workdir> [--dry-run] [--force]
 *     --dry-run  只报告会改哪些，不写盘
 *     --force    官方字幕也修正（默认只修 source=asr 的产物）
 */

import { existsSync, readFileSync, readdirSync, statSync, writeFileSync } from "node:fs";
import { join, resolve } from "node:path";

type Rule = [string, string];

function loadRules(): Rule[] {
  const p = join(import.meta.dir, "..", "config", "whisper-typo-fixes.json");
  if (!existsSync(p)) return [];
  const j = JSON.parse(readFileSync(p, "utf-8"));
  const rules: Rule[] = [];
  for (const [k, v] of Object.entries(j)) {
    if (k.startsWith("_") || !Array.isArray(v)) continue;
    for (const pair of v) if (Array.isArray(pair) && pair.length === 2) rules.push([String(pair[0]), String(pair[1])]);
  }
  rules.sort((a, b) => b[0].length - a[0].length);
  return rules;
}

function fixText(text: string, rules: Rule[], hits: Map<string, number>): string {
  let out = text;
  for (const [bad, good] of rules) {
    const n = out.split(bad).length - 1;
    if (n <= 0) continue;
    out = out.split(bad).join(good);
    hits.set(`${bad}→${good}`, (hits.get(`${bad}→${good}`) ?? 0) + n);
  }
  return out;
}

const argv = process.argv.slice(2);
const target = argv.find((a) => !a.startsWith("-"));
const dry = argv.includes("--dry-run");
const force = argv.includes("--force");

if (!target) {
  console.error("用法: bun fix_typos.ts <file-or-workdir> [--dry-run] [--force]");
  process.exit(2);
}

const root = resolve(target);
if (!existsSync(root)) { console.error(`✗ 路径不存在: ${root}`); process.exit(1); }

const files: string[] = [];
if (statSync(root).isDirectory()) {
  const metaPath = join(root, "meta.json");
  const isAsr = existsSync(metaPath) && JSON.parse(readFileSync(metaPath, "utf-8")).source === "asr";
  if (!isAsr && !force) {
    console.error(`✗ ${root} 的 meta.json 显示来源不是 asr，跳过（要强行修正加 --force）`);
    process.exit(0);
  }
  for (const f of readdirSync(root)) if (/^segments\.json$|^transcript\..*\.md$|^transcript\.txt$/.test(f)) files.push(join(root, f));
} else {
  files.push(root);
}

const rules = loadRules();
const hits = new Map<string, number>();
let changed = 0;

for (const f of files) {
  const raw = readFileSync(f, "utf-8");
  if (f.endsWith("segments.json")) {
    const segs = JSON.parse(raw) as { text: string }[];
    for (const s of segs) s.text = fixText(s.text, rules, hits);
    const next = JSON.stringify(segs, null, 2);
    if (next !== raw) { changed++; if (!dry) writeFileSync(f, next); }
  } else {
    const next = fixText(raw, rules, hits);
    if (next !== raw) { changed++; if (!dry) writeFileSync(f, next); }
  }
}

console.log(JSON.stringify({
  ok: true,
  dryRun: dry,
  rules: rules.length,
  filesChanged: changed,
  hits: Object.fromEntries([...hits].sort((a, b) => b[1] - a[1])),
}, null, 2));
