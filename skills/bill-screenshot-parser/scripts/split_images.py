#!/usr/bin/env python3
"""
账单截图分割工具
将长截图分割为 2000px 高度的片段，用于后续 OCR 识别。
所有临时文件生成在 /tmp/bill_parts/ 下，自动清理。
"""

import hashlib
import json
import os
import shutil
import sys
from PIL import Image

PART_HEIGHT = 2000
OUTPUT_DIR = '/tmp/bill_parts'


def split_image(image_path, output_dir=OUTPUT_DIR, part_height=PART_HEIGHT):
    """分割单张图片，返回 parts 路径列表"""
    img = Image.open(image_path)
    width, height = img.size

    if height <= part_height:
        return [image_path]

    name_hash = hashlib.md5(image_path.encode()).hexdigest()[:8]
    parts_dir = os.path.join(output_dir, f'parts_{name_hash}')
    os.makedirs(parts_dir, exist_ok=True)

    num_parts = (height + part_height - 1) // part_height
    parts = []

    for i in range(num_parts):
        top = i * part_height
        bottom = min((i + 1) * part_height, height)
        part = img.crop((0, top, width, bottom))
        part_path = os.path.join(parts_dir, f'part_{i:02d}.png')
        part.save(part_path)
        parts.append(part_path)

    return parts


def main():
    if '--clean' in sys.argv:
        if os.path.exists(OUTPUT_DIR):
            shutil.rmtree(OUTPUT_DIR)
        print(json.dumps({"cleaned": True}))
        return

    image_paths = [a for a in sys.argv[1:] if not a.startswith('--')]

    # 清理旧的临时文件
    if os.path.exists(OUTPUT_DIR):
        shutil.rmtree(OUTPUT_DIR)
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    result = {"images": []}

    for img_path in image_paths:
        if not os.path.exists(img_path):
            print(f"Warning: {img_path} not found, skipping", file=sys.stderr)
            continue

        img = Image.open(img_path)
        width, height = img.size
        parts = split_image(img_path)
        needs_split = height > PART_HEIGHT

        result["images"].append({
            "source": img_path,
            "width": width,
            "height": height,
            "needs_split": needs_split,
            "parts": parts,
            "num_parts": len(parts)
        })

    print(json.dumps(result, ensure_ascii=False))


if __name__ == '__main__':
    main()
