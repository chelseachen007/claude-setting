#!/usr/bin/env python3
"""飞书语音闪念 → Whisper 转写 → Obsidian/闪念/YYYY-MM-DD.md

两种取数方式：
  --from-history  查私聊历史补漏（默认安全，不依赖长连接）
  事件模式由 feishu-watch.sh 负责，把事件 JSON 从 stdin 灌进来

用法：
  python3 voiceflash.py --from-history            # 处理所有未处理的语音
  python3 voiceflash.py --event-file msg.json     # 处理单条事件
  python3 voiceflash.py --from-history --dry-run  # 只看会处理什么
"""
from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
import sys
import time
from datetime import datetime, timezone, timedelta
from pathlib import Path

HOME = Path.home()
VOICE_DIR = HOME / "ai/voice"
STATE_FILE = VOICE_DIR / "state.json"
INBOX = VOICE_DIR / "inbox"
LOG = VOICE_DIR / "logs/voiceflash.log"

VAULT = HOME / "Documents/study/github/Obsidian"
FLASH_DIR = VAULT / "闪念"

LARK = str(HOME / ".npm-global/bin/lark-cli")
PY_ASR = "/opt/homebrew/bin/python3"
ASR_MODEL = "mlx-community/whisper-large-v3-turbo"
MAGPIE = "http://127.0.0.1:3425/v1/chat/completions"
MAGPIE_MODEL = "deepseek/deepseek-v4-pro"

CST = timezone(timedelta(hours=8))
SHORT_SEC = 60  # 短于这个长度算"闪念"，长于等于算"会议"

# 用户与「飞书 CLI」的私聊，事件里已实测确认
DEFAULT_CHAT_ID = "oc_af90b050c12148a7298a37bc3dda8077"


def log(msg: str) -> None:
    LOG.parent.mkdir(parents=True, exist_ok=True)
    line = f"[{datetime.now(CST):%Y-%m-%d %H:%M:%S}] {msg}"
    print(line, file=sys.stderr)
    with LOG.open("a", encoding="utf-8") as f:
        f.write(line + "\n")


# ---------------------------------------------------------------- lark-cli

def run_lark(args: list[str]) -> dict:
    """调 lark-cli，返回解析后的 JSON。lark-cli 会把提示混进 stdout，所以只取第一个 '{' 开始的部分。"""
    p = subprocess.run([LARK, *args], capture_output=True, text=True, timeout=300)
    out = p.stdout
    start = out.find("{")
    if start < 0:
        raise RuntimeError(f"lark-cli 无 JSON 输出: {out[:300]} {p.stderr[:300]}")
    return json.loads(out[start:])


def list_audio_messages(chat_id: str, limit: int = 30) -> list[dict]:
    """拉私聊最近消息，返回 audio 类型的，按时间正序。"""
    d = run_lark([
        "im", "+chat-messages-list",
        "--chat-id", chat_id,
        "--order", "desc",
        "--page-size", str(limit),
    ])
    if not d.get("ok"):
        raise RuntimeError(f"拉历史失败: {d.get('error')}")

    out = []
    for m in d["data"].get("messages", []):
        if m.get("msg_type") != "audio":
            continue
        content = m.get("content", "")
        key = re.search(r'key="([^"]+)"', content)
        dur = re.search(r'duration="(\d+s?)"', content)
        if not key:
            continue
        seconds = 0
        if dur:
            raw = dur.group(1).rstrip("s")
            seconds = int(raw) if raw.isdigit() else 0
        # lark-cli 的历史接口给的是 "YYYY-MM-DD HH:MM" 字符串，不是毫秒时间戳
        ct = str(m.get("create_time", ""))
        try:
            ts_ms = int(datetime.strptime(ct, "%Y-%m-%d %H:%M").replace(tzinfo=CST).timestamp() * 1000)
        except ValueError:
            ts_ms = 0
        out.append({
            "message_id": m["message_id"],
            "file_key": key.group(1),
            "duration": seconds,
            "create_time": ts_ms,
        })
    out.sort(key=lambda x: x["create_time"])
    return out


def download_audio(message_id: str, file_key: str) -> Path:
    """下载语音到 inbox。注意 --type 只能是 image|file，语音走 file。"""
    INBOX.mkdir(parents=True, exist_ok=True)
    d = run_lark([
        "im", "+messages-resources-download",
        "--message-id", message_id,
        "--file-key", file_key,
        "--type", "file",
    ])
    if not d.get("ok"):
        raise RuntimeError(f"下载失败: {d.get('error')}")
    src = Path(d["data"]["saved_path"])
    dst = INBOX / f"{message_id}.ogg"
    if src != dst:
        src.replace(dst)
    return dst


# ---------------------------------------------------------------- ASR

def to_wav(src: Path) -> Path:
    wav = src.with_suffix(".wav")
    if wav.exists() and wav.stat().st_size > 0:
        return wav
    subprocess.run(
        ["ffmpeg", "-y", "-v", "error", "-i", str(src),
         "-ar", "16000", "-ac", "1", "-c:a", "pcm_s16le", str(wav)],
        check=True, timeout=600,
    )
    return wav


# whisper 在静音上会吐出的训练数据泄漏短语（YouTube 字幕、Amara 致谢等）。
# 判据来自 silverstein/minutes 的 crates/whisper-guard：只做整行精确匹配，不做子串匹配，
# 否则「感谢观看我们的演示」这种真话会被误杀。
HALLUCINATION_PHRASES = {
    "请不吝点赞 订阅 转发 打赏支持明镜与点点栏目",
    "字幕由amara.org社区提供",
    "字幕志愿者 杨茜茜",
    "amara.org",
    "thanks for watching",
    "thank you for watching",
    "字幕by索兰娅",
    "中文字幕提供",
    "请订阅我的频道",
    "subtitles by the amara.org community",
}

# 这些「永远不是内容」的标记，出现在任何位置都可以丢
NOISE_TOKENS = {
    "[music]", "[音乐]", "[音乐]", "[applause]", "[掌声]", "[laughter]", "[笑声]",
    "[blank_audio]", "[silence]", "[noise]", "[inaudible]", "♪", "♪♪",
    "(music)", "(applause)", "(laughter)", "音乐", "掌声",
}

# 尾部语音指令，whisper 常把它们粘在结尾
TRAILING_COMMANDS = ("stop recording", "end recording", "停止录音", "结束录音", "停止录制")

# 转写段置信度阈值，来自 ryamabra/mlx-transcribe 的 is_hallucination()。
# 实测对照：真话 avg_logprob≈-0.82、compression_ratio=1.0；
# 2 秒静音幻觉 avg_logprob≈-5.13 且漂成韩文。阈值取中间偏保守。
LOGPROB_MIN = -1.0
COMPRESSION_MAX = 2.4
NO_SPEECH_MAX = 0.6


def _seg_is_bad(seg: dict) -> bool:
    """按 whisper 自身的置信度信号丢段，不依赖音频特征。"""
    text = (seg.get("text") or "").strip()
    if not text:
        return True
    if seg.get("no_speech_prob", 0.0) > NO_SPEECH_MAX:
        return True
    if seg.get("avg_logprob", 0.0) < LOGPROB_MIN:
        return True
    if seg.get("compression_ratio", 0.0) > COMPRESSION_MAX:
        return True
    # 词重复率过低 = 循环签名
    words = text.lower().split()
    if len(words) > 4 and len(set(words)) / len(words) < 0.35:
        return True
    # 与中文无关的书写系统（韩文/日文假名/西里尔/阿拉伯）—— 语言已锁定 zh，出现即幻觉
    foreign = re.findall(r"[\uac00-\ud7af\u3040-\u30ff\u0400-\u04ff\u0600-\u06ff]", text)
    cjk = re.findall(r"[\u4e00-\u9fff]", text)
    if foreign and len(foreign) > len(cjk):
        return True
    return False


def transcribe(wav: Path) -> str:
    """mlx_whisper 转写，带置信度过滤。

    坑：NO_PROXY 里的 [::1] 会让 httpx 在下载/解析时抛 Invalid port: ':1]'，
    所以必须把代理环境变量全摘掉再跑。
    参考：ryamabra/mlx-transcribe（同栈 MLX）、silverstein/minutes 的 whisper-guard。
    """
    code = f"""
import mlx_whisper, json
r = mlx_whisper.transcribe(
    {str(wav)!r},
    path_or_hf_repo={ASR_MODEL!r},
    language="zh",
    word_timestamps=False,
    verbose=False,
)
print(json.dumps(r.get("segments", []), ensure_ascii=False))
"""
    env = {k: v for k, v in os.environ.items()
           if k.lower() not in ("http_proxy", "https_proxy", "all_proxy", "no_proxy")}
    p = subprocess.run([PY_ASR, "-c", code], capture_output=True, text=True,
                       timeout=3600, env=env)
    if p.returncode != 0:
        raise RuntimeError(f"转写失败: {p.stderr[-500:]}")

    # lark 日志可能混进 stdout，只取最后一个 JSON 数组
    line = [ln for ln in p.stdout.strip().splitlines() if ln.startswith("[")][-1]
    segs = json.loads(line)

    keep, dropped = [], 0
    for s in segs:
        if _seg_is_bad(s):
            dropped += 1
            continue
        keep.append(s)
    if dropped:
        log(f"  置信度过滤丢弃 {dropped} 段")

    text = "".join(s.get("text", "").strip() for s in keep)
    return clean_text(text)


def clean_text(text: str) -> str:
    """whisper-guard 式的文本级清洗，顺序有意为之。"""
    lines = []
    for ln in text.splitlines():
        t = ln.strip()
        if not t:
            continue
        # 1. 训练数据泄漏短语：整行精确匹配
        bare = re.sub(r"[\[\]()（）\s]|字幕|提供", "", t).lower()
        if bare in {re.sub(r"[\[\]()（）\s]|字幕|提供", "", p) for p in HALLUCINATION_PHRASES}:
            continue
        # 2. 噪声标记：整行都是标记就丢
        if t.strip().lower() in NOISE_TOKENS:
            continue
        lines.append(t)

    text = "".join(lines)

    # 3. 行内噪声标记直接剔除（whisper 常把 [music] 拼错成 [misic]/[Music] 等，
    #    所以用「方括号里是纯音乐/噪声词」的正则，而不是精确串匹配）
    text = re.sub(
        r"[\[\(（【]\s*(?:music|musik|misic|applause|laughter|noise|silence|blank[_ ]?audio|"
        r"音乐|掌声|笑声|噪音|静音|无声)\s*[\]\)）】]",
        "", text, flags=re.I,
    )

    # 4. 尾部语音指令（含中英文，可能在末尾多次粘连）
    changed = True
    while changed:
        changed = False
        for cmd in TRAILING_COMMANDS:
            for tail in (cmd, cmd + ".", cmd + "。", cmd + "！"):
                if text.rstrip().lower().endswith(tail):
                    text = text.rstrip()[: -len(tail)].rstrip()
                    changed = True

    # 清掉剔除标记后留下的双空格
    text = re.sub(r"[ \t]{2,}", " ", text)

    return text.strip(" ，。,").strip()


# ---------------------------------------------------------------- 整理

FLASH_PROMPT = """把下面这段语音转写的口语稿整理成一条闪念记录。

只输出一个 JSON 对象，不要任何解释、不要代码块围栏。schema：
{"title": "不超过 20 字的主题，取具体的人/事/判断，不要泛泛的类别词",
 "summary": "一句话说清这条闪念到底在讲什么",
 "cleaned": "整理后的正文（Markdown），要求见下"}

cleaned 的整理要求：
1. 去掉「嗯、那个、就是说、然后」这类口水话、重复、说错重来的开头
2. 修正明显的同音错别字，按上下文判断（比如"零叉剧"可能是"零差评"）
3. 保持说话人自己的口吻和第一人称，不要改成报告腔
4. 保留全部实质细节：人名、数字、日期、意图、判断依据
5. 不加原文没有的内容，不要升华为「这说明」「这意味着」这种总结句
6. 短段落，不要用标题，自然的才用 bullet
7. 如果原话本身就短，cleaned 可以很短，不要把一句话灌水成一段

语音转写稿：
{text}"""

MEETING_PROMPT = """把下面这段会议/长语音转写稿整理成结构化纪要。

只输出一个 JSON 对象，不要任何解释、不要代码块围栏。schema：
{"title": "不超过 20 字的会议主题",
 "summary": "一句话说清这次谈了什么",
 "cleaned": "结构化纪要（Markdown），要求见下"}

cleaned 的整理要求：
1. 去掉口水话、重复、无意义语气词
2. 按主题分段，每段小标题概括
3. 末尾用 `## 待办` 列出明确提到要做的事（没提到就写"无"）
4. 不要编造原文没有的内容，人名数字日期原样保留

语音转写稿：
{text}"""


def polish(text: str, meeting: bool) -> dict:
    """调 magpie 整理，返回 {"title","summary","cleaned"}；失败返回空 dict。"""
    prompt = (MEETING_PROMPT if meeting else FLASH_PROMPT).replace("{text}", text)
    body = json.dumps({
        "model": MAGPIE_MODEL,
        "messages": [
            {"role": "system", "content": "你只输出严格 JSON，不要任何别的字符。"},
            {"role": "user", "content": prompt},
        ],
        # 坑：deepseek-v4-pro 的 reasoning_content 与 content 共享 max_tokens 预算，
        # 预算给小了会 finish_reason=length 且 content 为空（实测 600 → 空，2000 → 正常）。
        "max_tokens": 4000 if meeting else 2500,
        "temperature": 0.3,
    }).encode()
    p = subprocess.run(
        ["curl", "-s", "--noproxy", "127.0.0.1", "-X", "POST", MAGPIE,
         "-H", "Content-Type: application/json", "--data-binary", "@-"],
        input=body, capture_output=True, timeout=300,
    )
    try:
        d = json.loads(p.stdout)
        choice = d["choices"][0]
        content = (choice["message"].get("content") or "").strip()
        if not content:
            log(f"整理返回空（finish_reason={choice.get('finish_reason')}），退回逐字稿")
            return {}
        # 模型偶尔会套 ```json 围栏
        content = re.sub(r"^```(?:json)?\s*|\s*```$", "", content, flags=re.S)
        start, end = content.find("{"), content.rfind("}")
        if start < 0 or end < 0:
            log(f"整理结果不含 JSON，退回逐字稿：{content[:80]}")
            return {}
        obj = json.loads(content[start:end + 1])
        if not obj.get("cleaned"):
            return {}
        return obj
    except Exception as e:
        log(f"整理失败（保留逐字稿）: {e}")
        return {}


# ---------------------------------------------------------------- 写笔记

def note_path(dt: datetime) -> Path:
    return FLASH_DIR / f"{dt:%Y-%m-%d}.md"


def append_entry(dt: datetime, seconds: int, raw: str, polished: dict) -> Path:
    """把一条闪念追加进当天的文件。按天聚合，不一条一个文件。

    结构参考 Forrest404/forrest-notes：整理稿在上，逐字稿收进可折叠 callout，
    既是安全网（整理稿错了能回溯），又不干扰阅读。
    """
    FLASH_DIR.mkdir(parents=True, exist_ok=True)
    path = note_path(dt)
    meeting = seconds >= SHORT_SEC

    title = (polished.get("title") or "").strip()
    summary = (polished.get("summary") or "").strip()
    body = (polished.get("cleaned") or "").strip()

    if meeting:
        head = f"### {dt:%H:%M} · 会议录音（{seconds}s）"
        if title:
            head += f" · {title}"
        block = [head, ""]
        if summary:
            block += [f"> [!summary] {summary}", ""]
        block += [body or raw, ""]
    else:
        head = f"### {dt:%H:%M}"
        if title:
            head += f" · {title}"
        block = [head, ""]
        if summary and summary != body:
            block += [f"> {summary}", ""]
        block += [body or raw, ""]

    # 逐字稿只在不等于整理稿时才折叠保留
    if body and body != raw:
        block += ["> [!quote]- 原始逐字稿", ">", "> " + raw.replace("\n", "\n> "), ""]

    if not path.exists():
        header = [
            "---",
            f'title: "{path.stem}"',
            f"date: {dt:%Y-%m-%d}",
            f"lastmod: {dt:%Y-%m-%d}",
            "tags:",
            "  - 闪念",
            "---",
            "",
            f"# {dt:%Y-%m-%d} 闪念",
            "",
        ]
        path.write_text("\n".join(header), encoding="utf-8")

    with path.open("a", encoding="utf-8") as f:
        f.write("\n".join(block) + "\n")

    # 更新 lastmod
    txt = path.read_text(encoding="utf-8")
    txt = re.sub(r"^lastmod: .*$", f"lastmod: {dt:%Y-%m-%d}", txt, count=1, flags=re.M)
    path.write_text(txt, encoding="utf-8")
    return path


# ---------------------------------------------------------------- 状态

def load_state() -> dict:
    if STATE_FILE.exists():
        try:
            return json.loads(STATE_FILE.read_text(encoding="utf-8"))
        except Exception:
            pass
    return {"processed": [], "last_check": 0}


def save_state(st: dict) -> None:
    STATE_FILE.parent.mkdir(parents=True, exist_ok=True)
    st["processed"] = st["processed"][-500:]
    STATE_FILE.write_text(json.dumps(st, ensure_ascii=False, indent=2), encoding="utf-8")


# ---------------------------------------------------------------- 主流程

def process_one(msg: dict, st: dict, dry: bool) -> bool:
    mid = msg["message_id"]
    if mid in st["processed"]:
        return False

    dt = datetime.fromtimestamp(msg["create_time"] / 1000, CST) if msg["create_time"] else datetime.now(CST)
    secs = msg.get("duration") or 0
    kind = "会议" if secs >= SHORT_SEC else "闪念"
    log(f"处理 {mid} {dt:%m-%d %H:%M} {secs}s [{kind}]")

    if dry:
        return True

    try:
        ogg = download_audio(mid, msg["file_key"])
        wav = to_wav(ogg)
        raw = transcribe(wav)
        if not raw:
            log(f"  {mid} 转写为空，跳过")
            return False
        # 整理失败不能吃掉整条语音：空 dict 也能落逐字稿
        try:
            polished = polish(raw, meeting=(secs >= SHORT_SEC))
        except Exception as e:
            log(f"  整理异常，退回逐字稿: {e}")
            polished = {}
        path = append_entry(dt, secs, raw, polished)
        log(f"  → {path.name}  「{(polished.get('title') or raw)[:40]}…」")
        st["processed"].append(mid)
        save_state(st)
        return True
    except Exception as e:
        log(f"  {mid} 失败: {e}")
        return False


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--from-history", action="store_true")
    ap.add_argument("--event-file", help="单条事件 JSON 文件")
    ap.add_argument("--chat-id", default=DEFAULT_CHAT_ID)
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()

    st = load_state()

    if args.event_file:
        ev = json.loads(Path(args.event_file).read_text(encoding="utf-8"))
        msg = ev if "message_id" in ev else ev.get("event", {}).get("message", {})
        if msg.get("message_type") != "audio":
            return 0
        content = msg.get("content", "")
        key = re.search(r'key="([^"]+)"', content)
        dur = re.search(r'duration="(\d+)s?"', content)
        item = {
            "message_id": msg["message_id"],
            "file_key": key.group(1) if key else "",
            "duration": int(dur.group(1)) if dur else 0,
            "create_time": int(msg.get("create_time", "0")),
        }
        process_one(item, st, args.dry_run)
        return 0

    if args.from_history:
        try:
            msgs = list_audio_messages(args.chat_id)
        except Exception as e:
            log(f"拉历史失败: {e}")
            return 1
        fresh = [m for m in msgs if m["message_id"] not in st["processed"]]
        log(f"历史里 {len(msgs)} 条语音，待处理 {len(fresh)} 条")
        for m in fresh:
            process_one(m, st, args.dry_run)
        st["last_check"] = int(time.time() * 1000)
        save_state(st)
        return 0

    ap.print_help()
    return 1


if __name__ == "__main__":
    sys.exit(main())
