#!/usr/bin/env python3
"""ASR 兜底引擎：mlx-whisper / faster-whisper。仅在 WhisperKit 不可用时使用。

输出 <out>/segments.json = {"segments":[{"start":1.2,"end":3.4,"text":"..."}]}
"""
import argparse
import json
import os
import subprocess
import sys


def to_wav(media: str, outdir: str) -> str:
    wav = os.path.join(outdir, "audio16k.wav")
    if os.path.exists(wav):
        return wav
    subprocess.run(
        ["ffmpeg", "-y", "-v", "error", "-i", media, "-vn", "-ac", "1", "-ar", "16000",
         "-c:a", "pcm_s16le", wav],
        check=True,
    )
    return wav


def run_mlx(wav: str, language: str):
    import mlx_whisper  # type: ignore

    result = mlx_whisper.transcribe(
        wav,
        path_or_hf_repo="mlx-community/whisper-large-v3-turbo",
        language=None if language == "auto" else language,
        word_timestamps=False,
        verbose=False,
    )
    return [{"start": s["start"], "end": s["end"], "text": s["text"]} for s in result.get("segments", [])]


def run_faster(wav: str, language: str):
    from faster_whisper import WhisperModel  # type: ignore

    model = WhisperModel("small", device="cpu", compute_type="int8")
    segments, _ = model.transcribe(
        wav, language=None if language == "auto" else language, vad_filter=True, beam_size=5
    )
    return [{"start": s.start, "end": s.end, "text": s.text} for s in segments]


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("media")
    ap.add_argument("--out", required=True)
    ap.add_argument("--language", default="zh")
    ap.add_argument("--engine", choices=["mlx", "faster-whisper"], default="faster-whisper")
    a = ap.parse_args()

    os.makedirs(a.out, exist_ok=True)
    wav = to_wav(a.media, a.out)
    segs = run_mlx(wav, a.language) if a.engine == "mlx" else run_faster(wav, a.language)
    segs = [{"start": float(s["start"]), "end": float(s["end"]), "text": str(s["text"]).strip()}
            for s in segs if str(s["text"]).strip()]

    with open(os.path.join(a.out, "segments.json"), "w", encoding="utf-8") as f:
        json.dump({"engine": a.engine, "segments": segs}, f, ensure_ascii=False, indent=2)
    return 0 if segs else 1


if __name__ == "__main__":
    sys.exit(main())
