#!/usr/bin/env node
/**
 * PicGo 上传 helper —— 剪藏图片一律走这里，不落本地附件。
 *
 * 本机没有 picgo CLI（只有 /Applications/PicGo.app），Electron 二进制不接受 CLI 参数。
 * 这个脚本把 PicGo.app 内置的 picgo core 取出来用：
 *   - 首次运行：npx @electron/asar extract <app.asar> /tmp/picgo-asar（已存在则跳过）
 *   - 之后：new PicGo(~/.picgo/config.json) → picgo.upload([files])
 *
 * 用法：
 *   node picgo-upload.cjs img-01.png img-02.png ...（绝对路径或相对当前目录）
 *   node picgo-upload.cjs --json a.png b.png   只输出 JSON，用机器读
 *
 * 输出（stdout）：每行一个 "filename<TAB>url"，最后一行是 JSON 数组。
 * 退出码：0 全部成功；1 有失败（失败的 URL 为空）。
 */
const path = require('path');
const fs = require('fs');
const os = require('os');
const { execFileSync } = require('child_process');

const APP_ASAR = '/Applications/PicGo.app/Contents/Resources/app.asar';
const CORE_DIR = path.join(os.tmpdir(), 'picgo-asar');
const CORE = path.join(CORE_DIR, 'node_modules/picgo/dist/index.cjs.js');
const CONFIG = path.join(os.homedir(), '.picgo', 'config.json');
const BATCH = 8;

function ensureCore() {
  if (fs.existsSync(CORE)) return;
  if (!fs.existsSync(APP_ASAR)) {
    console.error(`[picgo] 找不到 ${APP_ASAR}，请确认 PicGo 已安装`);
    process.exit(1);
  }
  fs.mkdirSync(CORE_DIR, { recursive: true });
  execFileSync('npx', ['--yes', '@electron/asar', 'extract', APP_ASAR, CORE_DIR], {
    stdio: 'inherit',
  });
  if (!fs.existsSync(CORE)) {
    console.error('[picgo] 解包后没找到 picgo core，检查 @electron/asar 是否可用');
    process.exit(1);
  }
}

async function main() {
  const args = process.argv.slice(2).filter((a) => a !== '--json');
  if (!args.length) {
    console.error('用法: node picgo-upload.cjs <图片1> <图片2> ...');
    process.exit(1);
  }
  if (!fs.existsSync(CONFIG)) {
    console.error(`[picgo] 找不到配置 ${CONFIG}`);
    process.exit(1);
  }
  ensureCore();

  // 关键：命名导出 PicGo，不是默认导出
  const { PicGo } = require(CORE);
  const picgo = new PicGo(CONFIG);
  picgo.on('notification', () => {}); // 静默，避免污染 stdout
  picgo.on('beforeUpload', (ctx) => {
    // 用文件原名（已是 {文章短名}-{序号}.png）当 OSS key，不改成时间戳
    const files = ctx.output || [];
    for (const f of files) f.fileName = path.basename(f.input?.[0]?.path || f.fileName);
  });

  const results = [];
  for (let i = 0; i < args.length; i += BATCH) {
    const chunk = args.slice(i, i + BATCH).map((f) => path.resolve(f));
    // upload 必须传数组
    const res = await picgo.upload(chunk);
    for (const r of res || []) {
      results.push({ fileName: r.fileName, imgUrl: r.imgUrl });
      console.log(`${r.fileName}\t${r.imgUrl}`);
    }
  }

  const known = new Set(results.map((r) => r.fileName));
  for (const f of args) {
    const base = path.basename(path.resolve(f));
    if (!known.has(base)) results.push({ fileName: base, imgUrl: '' });
  }
  console.log(JSON.stringify(results));
  process.exit(results.every((r) => r.imgUrl) ? 0 : 1);
}

main().catch((e) => {
  console.error('[picgo] 上传失败:', e && (e.message || e));
  process.exit(1);
});
