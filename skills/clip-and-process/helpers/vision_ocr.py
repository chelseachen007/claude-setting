#!/usr/bin/env python3
"""macOS Vision.framework 本地 OCR，替代远程 API。"""

import sys
import urllib.request

from Vision import (
    VNRecognizeTextRequest,
    VNImageRequestHandler,
    VNRequestTextRecognitionLevelAccurate,
)


def ocr_image(source: str) -> str:
    """对 URL 或本地文件路径做 OCR，返回识别文字。"""
    if source.startswith(("http://", "https://")):
        data = urllib.request.urlopen(source, timeout=15).read()
    else:
        with open(source, "rb") as f:
            data = f.read()

    results = []

    def handler(req, err):
        if err:
            return
        for obs in req.results():
            results.append(obs.topCandidates_(1)[0].string())

    req = VNRecognizeTextRequest.alloc().initWithCompletionHandler_(handler)
    req.setRecognitionLevel_(VNRequestTextRecognitionLevelAccurate)
    req.setRecognitionLanguages_(["zh-Hans", "zh-Hant", "en"])
    req.setUsesLanguageCorrection_(True)

    handler = VNImageRequestHandler.alloc().initWithData_options_(data, None)
    handler.performRequests_error_([req], None)

    return "\n".join(results)


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: vision_ocr.py <url_or_path>", file=sys.stderr)
        sys.exit(1)
    text = ocr_image(sys.argv[1])
    print(text)
