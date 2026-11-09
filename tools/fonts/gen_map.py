#!/usr/bin/env python3
"""从 GUI/fonts.c 反解两套字库的字符集，生成 bdfconv 用的 map 文件。

把要新增的文字写在下面的 ADD_CHARS 常量里即可。
用法（在工程根目录执行）：
    python tools/fonts/gen_map.py -o tools/fonts/new          # 含 ADD_CHARS
    python tools/fonts/gen_map.py --base -o tools/fonts/base  # 不含新增字，用于校验 BDF
"""
from __future__ import annotations

import argparse
import ast
import re
from pathlib import Path
from typing import cast

ROOT = Path(__file__).resolve().parents[2]
FONTS_C = ROOT / 'GUI' / 'fonts.c'
DEFAULT_OUTDIR = Path(__file__).resolve().parent
FONTS = {'wqy9': 'u8g2_font_wqy9_t_lunar', 'wqy12': 'u8g2_font_wqy12_t_lunar'}

# 需要新增的文字；重复的字、字库里已有的字会自动去重/跳过
ADD_CHARS = ""


def glyphs(src: str, name: str) -> set[int]:
    """解析一个 u8g2 字体数组，返回其中所有 Unicode 码点。"""
    m: re.Match[str] | None = re.search(
        r'const uint8_t ' + name + r'\[(\d+)\][^=]*=\s*((?:"(?:\\.|[^"\\])*"\s*)+);', src)
    if m is None:
        raise SystemExit('找不到字体数组: ' + name)
    raw = cast(str, ast.literal_eval('(' + m.group(2) + ')'))
    data: bytes = raw.encode('latin-1')
    table = 23 + ((data[21] << 8) | data[22])  # start_pos_unicode 指向查找表
    codes: set[int] = set()
    p = 23
    while p + 2 <= table:  # ASCII 段：[编码 1B][长度 1B][数据]
        enc, size = data[p], data[p + 1]
        if not enc or not size:
            break
        codes.add(enc)
        p += size
    q, off = table, 0
    blocks: list[int] = []
    while q + 4 <= len(data):  # Unicode 查找表：[偏移 2B][起始码点 2B]
        delta, start = (data[q] << 8) | data[q + 1], (data[q + 2] << 8) | data[q + 3]
        if not delta and not start:
            break
        off += delta
        blocks.append(table + off)
        q += 4
        if start == 0xFFFF:
            break
    for block in blocks:  # Unicode 段：[码点 2B][长度 1B][数据]
        p = block
        while p + 3 <= len(data):
            enc, size = (data[p] << 8) | data[p + 1], data[p + 2]
            if not enc or not size:
                break
            codes.add(enc)
            p += size
    if len(codes) != data[0]:
        raise SystemExit('%s 解析出 %d 个字形，头部声明 %d 个，解析可能有误' % (name, len(codes), data[0]))
    return codes


def main() -> None:
    ap = argparse.ArgumentParser(description='从 GUI/fonts.c 生成 bdfconv 字符集 map')
    _ = ap.add_argument('--add', default=ADD_CHARS, help='新增文字，默认取脚本顶部的 ADD_CHARS 常量')
    _ = ap.add_argument('--base', action='store_true', help='忽略新增文字，只输出现有字库字符集（用于校验 BDF）')
    _ = ap.add_argument('-o', '--outdir', type=Path, default=DEFAULT_OUTDIR, help='输出目录，默认 tools/font/')
    args = ap.parse_args()

    src = FONTS_C.read_text(encoding='utf-8')
    add_text = '' if cast(bool, args.base) else cast(str, args.add)
    outdir = cast(Path, args.outdir)
    added: set[int] = {ord(c) for c in add_text if ord(c) > 0}
    outdir.mkdir(parents=True, exist_ok=True)
    print('待加入字符: %s（去重后 %d 个）' % (add_text or '（空）', len(added)))
    for key, name in FONTS.items():
        base = glyphs(src, name)
        codes = base | added
        new = sorted(codes - base)
        path = outdir / (key + '.map')
        text = ', '.join(str(c) if c < 128 else '$%04X' % c for c in sorted(codes))
        with path.open('w', encoding='ascii', newline='\n') as f:
            _ = f.write(text + '\n')
        detail = '(' + ', '.join('U+%04X %s' % (c, chr(c)) for c in new) + ')' if new else ''
        print('%s: 原有 %d 个，实际新增 %d 个 %s -> %s' % (name, len(base), len(new), detail, path))


if __name__ == '__main__':
    main()
