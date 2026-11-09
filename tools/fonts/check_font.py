import ast
import re
import sys

src = open('GUI/fonts.c', encoding='utf-8').read()
for name in ('u8g2_font_wqy9_t_lunar', 'u8g2_font_wqy12_t_lunar'):
    m = re.search(r'const uint8_t ' + name + r'\[(\d+)\][^=]*=\s*((?:"(?:\\.|[^"\\])*"\s*)+);', src)
    data = ast.literal_eval('(' + m.group(2) + ')').encode('latin-1')
    table = 23 + ((data[21] << 8) | data[22])  # start_pos_unicode 指向查找表
    codes, p = set(), 23
    while p + 2 <= table:  # ASCII 段：[编码 1B][长度 1B][数据]
        enc, size = data[p], data[p + 1]
        if not enc or not size:
            break
        codes.add(enc)
        p += size
    q, off, blocks = table, 0, []
    while q + 4 <= len(data):  # Unicode 查找表：[偏移 2B][起始码点 2B]
        delta, uni = (data[q] << 8) | data[q + 1], (data[q + 2] << 8) | data[q + 3]
        if not delta and not uni:
            break
        off += delta
        blocks.append(table + off)
        q += 4
        if uni == 0xFFFF:
            break
    for start in blocks:  # Unicode 段：[码点 2B][长度 1B][数据]
        p = start
        while p + 3 <= len(data):
            enc, size = (data[p] << 8) | data[p + 1], data[p + 2]
            if not enc or not size:
                break
            codes.add(enc)
            p += size
    print(name, 'glyphs:', len(codes))
    for ch in sys.argv[1:]:
        print('  U+%04X %s %s' % (ord(ch), ch, ord(ch) in codes))
        