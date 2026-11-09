# 字库 / 字体数据维护说明

日历上的中文不是运行时加载字体文件，而是**编译进固件的裁剪版 u8g2 点阵字库**（`GUI/fonts.c` 中的 C 数组）。
想显示字库里没有的汉字（例如把生日名称改成「大宝节」「小宝节」，其中「宝」缺失），必须重新生成字库并重新编译固件。
本文记录字库结构、字体资源下载地址，以及添加单个文字的完整步骤。

## 一、字库结构与现状

| 数组（`GUI/fonts.c`） | 用途 | 头注释中的字体 | 字形数 |
|---|---|---|---|
| `u8g2_font_wqy9_t_lunar` | 小屏（4.2 寸）中文 | `-wenquanyi-...-bold-...--12-...`（12px） | 228（96 ASCII + 132 个非 ASCII 码点） |
| `u8g2_font_wqy12_t_lunar` | 大屏（7.5 寸）中文 | `-wenquanyi-...-bold-...--16-...`（16px） | 142（10 ASCII + 132 个非 ASCII 码点） |
| `u8g2_font_helvB14_tn` / `helvB18_tn` | 日期数字 | Helvetica Bold 20px / 25px | 各 18（只含数字及少量符号） |

- 选择逻辑在 `GUI/GUI.c:269`：`large ? u8g2_font_wqy12_t_lunar : u8g2_font_wqy9_t_lunar`，其中 `large_layout` 为 `height >= 400`（`GUI/GUI.c:16`）。
- 渲染链路：`GFX_printf()` → UTF-8 解码成 Unicode 码点（`GUI/Adafruit_GFX.c`）→ `u8g2_font_get_glyph_data()` 在字库内嵌的 Unicode 查找表中定位字模 → 解压绘制。
- **没有独立的「字符 → 字模」映射表**，映射关系内嵌在压缩字库数组里；字库不是 GB2312/HZK 文件，也不是按节日名分文件的。
- 查不到字形时**静默不绘制，不报错**（`GUI/u8g2_font.c:409-413`），表现为名称中间出现空白。
- `GUI/fonts.h:6-25` 的「文字列表」是字符集清单**注释**，不是运行时配置；清单可能与字库实际内容有出入，重新生成时以第三节脚本从 `GUI/fonts.c` 反解出的码点为准。
- 两套中文字库的**非 ASCII 字符集合完全相同（131 个汉字 + `℃`，共 132 个码点）**，只是 ASCII 范围不同。新增汉字必须两套都补，否则只在一种屏幕上显示。

现有 131 个汉字（从 `GUI/fonts.c` 解析得到）：

```
一丁七万三丑丙中乙九二五亥亲人休儿元兔党八六军冬分初动劳十午卯周四国圣壬处夏夕夜大天头女妇子安宵寅寒小己巳师平年庆庚建廿恩情惊愚感戊戌抬教日旦明星春暑月有期未树植正母水清满父牛狗猪猴班甲申癸白离秋种立童端羊腊至节芒虎蛇蛰衣诞谷辛辰还酉重闰阳降除雨雪霜露青马鸡鼠龙
```

此外还需 `℃`（U+2103）与 ASCII（`fonts.h` 注释写 32-128；实际小字库含 96 个 ASCII 字形，大字库含 10 个）。

## 二、字体资源下载地址

生成字库需要两样东西：**`bdfconv` 工具** + **BDF 点阵字体源文件**（文泉驿 Bitmap Song，两套字号）。
以下文件都仅供 PC 端生成使用，建议统一放在 `tools/fonts/`，不要加入固件编译（BDF 约 4~7 MB）。

### 工具

| 资源 | 地址 |
|---|---|
| u8g2 官方 `bdfconv` 源码与目录 | <https://github.com/olikraus/u8g2/tree/master/tools/font/bdfconv> |
| 官方 Windows 可执行文件 | <https://raw.githubusercontent.com/olikraus/u8g2/master/tools/font/bdfconv/bdfconv.exe> |
| 社区打包仓库（含 exe、map、BDF、生成命令 README） | <https://github.com/OceanSkyFly/EPD_fonts> |
| 社区 `bdfconv.exe` | <https://raw.githubusercontent.com/OceanSkyFly/EPD_fonts/main/bdfconv.exe> |
| 社区 `myfont.map`（字符集示例） | <https://raw.githubusercontent.com/OceanSkyFly/EPD_fonts/main/myfont.map> |
| 社区 `README.md`（生成命令） | <https://raw.githubusercontent.com/OceanSkyFly/EPD_fonts/main/README.md> |

> 社区 `myfont.map` 的码点数量少于本工程现有字库的 132 个非 ASCII 码点，**不能直接拿它重新生成**（会丢字），只能作为格式参考；正确做法见第三节用 `tools/font/gen_map.py` 从 `GUI/fonts.c` 反解完整字符集。

### BDF 点阵字体

| 对应数组 | 字号 | 下载地址 |
|---|---|---|
| `wqy9`（12px） | 9pt，medium（非 bold） | <https://raw.githubusercontent.com/larryli/u8g2_wqy/master/bdf/wenquanyi_9pt.bdf> |
| `wqy12`（16px） | 12pt，bold | <https://raw.githubusercontent.com/OceanSkyFly/EPD_fonts/main/wenquanyi_12ptb.bdf> |
| `wqy12` 备选（12pt，非 bold） | 12pt | <https://raw.githubusercontent.com/larryli/u8g2_wqy/master/bdf/wenquanyi_12pt.bdf> |

其它字号目录与生成脚本参考：

- <https://github.com/larryli/u8g2_wqy/tree/master/bdf>（9pt / 10pt / 11pt / 12pt / 13px）
- <https://github.com/larryli/u8g2_wqy/blob/master/build.sh>（u8g2 官方 wqy 字体的 `bdfconv` 命令）
- <https://github.com/olikraus/u8g2/issues/455>（wqy 字体来源说明）
- 文泉驿官方页 <https://wenq.org/wqy2/index.cgi?BitmapSong_en>（站点可能不稳定，优先用上面的 GitHub 镜像）
- 若要连数字字体一起重生成：`helvB14.bdf` / `helvB18.bdf` 在 <https://github.com/olikraus/u8g2/tree/master/tools/font/bdf>

> **实测结论**（2026-11-09，按第三节第 3 步用 `base` map 生成后与 `GUI/fonts.c` 比对）：
> - `wenquanyi_12ptb.bdf` 生成的 `wqy12`：`Fontname`、`Glyphs: 142/29889`、数组长度 4830 与现有字库完全一致，可直接使用。
> - `wenquanyi_9pt.bdf` 是 **medium** 版，生成的 `wqy9` 为 `Glyphs: 228/30503`、长度 4430，与现有 bold 字库（`228/29895`、4315）不同；字形数同为 228 说明字符集反解正确，只是笔画更细。要像素级一致需 12px bold 版 BDF（获取方式见下节）；不追求一致可直接用这份，显示功能不受影响。
>
> 授权提示：文泉驿 Bitmap Song 为 GPL 字体，商用 / 闭源产品请自行确认合规性。

### 12px bold 版 BDF 怎么来

实测核对过官方包：SourceForge 的 `wqy-bitmapsong-bdf-1.0.0-RC1.tar.gz`（4.1 MB）里**只有 medium 版**
（`wenquanyi_9pt.bdf` ~ `12pt.bdf`、`13px.bdf`、LiberationSans），没有 bold BDF。
bold 版只以 PCF 形式发行，需转换成 BDF。

> **已下载核对**：`wqy-bitmapfont-pcf-0.9.9-0.tar.gz` 内是 `wenquanyi_9ptb.pcf`（bold，未压缩，约 2.1 MB）与 `wenquanyi_9pt.pcf`（medium）。
> 前者的 `FONT` 属性为 `-wenquanyi-wenquanyi bitmap song-bold-r-normal--12-120-75-75-P-119-ISO10646-1`，
> 与 `GUI/fonts.c:4` 完全相同 —— 它就是项目 12px 字库的源。
> 注意：**不能把 medium BDF 的 `FONT` 行改成 `bold` 冒充**，那只改了注释，字模数据仍是细的。

- PCF 来源（任选其一）：
  - <https://sourceforge.net/projects/wqy/files/wqy-bitmapfont/0.9.9/wqy-bitmapfont-pcf-0.9.9-0.tar.gz/download>（0.9.9 Hero，已核对，优先用这个）
  - <https://sourceforge.net/projects/wqy/files/wqy-bitmapfont/1.0.0-RC1/wqy-bitmapsong-pcf-1.0.0-RC1.tar.gz/download>
  - Debian/Ubuntu `apt install xfonts-wqy`、openSUSE `wqy-bitmap-fonts`，安装后取 `wenquanyi_9ptb.pcf.gz`
- 转换工具：<https://github.com/ganaware/pcf2bdf>（含 `Makefile.vc` / `Makefile.gcc`）；Debian/WSL `sudo apt install pcf2bdf`；纯 Windows 可用 MSYS2 编译
- 命令：`pcf2bdf -o wenquanyi_9ptb.bdf wenquanyi_9ptb.pcf`（工具也接受 `.pcf.gz`）
- 按第三节第 3 步用 `base/wqy9.map` 生成一次验证：`Fontname` 为 `...-bold-...--12-120-...`、`Glyphs: 228/29895`、数组长度 4315，三项全中即与项目原字库像素级一致。
- 另一个渠道：向社区 `OceanSkyFly/EPD_fonts` 作者或本项目群索取现成的 `wenquanyi_9ptb.bdf`（他们已分享同系列 16px 的 `wenquanyi_12ptb.bdf`）。

## 三、添加单个文字（以「宝」为例）

目标：`GUI/GUI.c:24-33` 的生日名称改为「大宝节」「小宝节」。
「大 U+5927」「小 U+5C0F」「节 U+8282」已在字库中，只需补 **「宝」U+5B9D**。

### 0. 准备目录

`tools/fonts/gen_map.py` 已随工程提供（Python 3 标准库，无需安装依赖）。
在 `tools/fonts/` 中另外放入：`bdfconv.exe` 和两份 BDF；map 文件由第 2 步生成。

### 1. 查新字的 Unicode 码点

```powershell
'{0:X4}' -f [int][char]'宝'      # 5B9D
```

```bash
python -c "print(hex(ord('宝')))"  # 0x5b9d
```

`bdfconv` 的 map 文件用 `$` + 十六进制表示码点，所以「宝」写作 `$5B9D`。

### 2. 构造完整字符集（关键：不能丢字）

不要手工整理字符清单：`GUI/fonts.h` 的清单只是注释，可能与字库实际内容有出入。
把要新增的文字写进 `tools/fonts/gen_map.py` 顶部的 `ADD_CHARS` 常量（例如 `ADD_CHARS = '大宝节小宝节'`），
脚本会**直接从 `GUI/fonts.c` 反解两套字库的全部码点**，再把常量里的字合并进去，生成两份 map 文件。
常量里重复的字、以及字库中已有的字都会自动去重/跳过，不会让字库变大。
脚本还会自检「解析出的字形数 == 字库头部声明的字形数」（228 / 142），不一致就报错退出，避免悄悄丢字。

```powershell
python tools/fonts/gen_map.py -o tools/fonts/new
```

Linux / MSYS2 下把 `python` 换成 `python3`。参数：

| 参数 | 说明 |
|---|---|
| `--add` | 临时覆盖 `ADD_CHARS`，不传时使用常量 |
| `--base` | 忽略新增文字，只输出现有字库的字符集（见第 3 步校验） |
| `-o` / `--outdir` | 输出目录，默认 `tools/font/` |

运行后输出（示例）：

```text
待加入字符: 大宝节小宝节（去重后 4 个）
u8g2_font_wqy9_t_lunar: 原有 228 个，实际新增 1 个 (U+5B9D 宝) -> tools/fonts/new/wqy9.map
u8g2_font_wqy12_t_lunar: 原有 142 个，实际新增 1 个 (U+5B9D 宝) -> tools/fonts/new/wqy12.map
```

「大 / 小 / 节」本来就在字库里，常量里重复出现的字也只算一次，所以实际只新增了 `$5B9D`（宝），字形数 228→229、142→143。

生成两份 map 而不是一份，是因为两套字库的 ASCII 范围不同（小字库 96 个、大字库 10 个）；
分开生成能精确复现原字库，不会额外增大 Flash。map 内容为逗号分隔的码点，ASCII 用十进制、其余用 `$` + 十六进制：

```text
32, 33, 34, ... , 127, $2103, $4E00, $4E01, ... , $5B9D, ... , $9F99,
```

`bdfconv` 的 map 语法也支持 `48-57` 范围、`~` 排除；本脚本输出的逐项列举形式最不容易出错。
输出为 ASCII 编码、无 BOM、LF 换行。

### 3. 先验证 BDF 和参数（强烈建议）

用 `--base` 生成一份「原字符集」map（忽略 `ADD_CHARS`），再用它各生成一次，把输出与 `GUI/fonts.c` 现有两个数组逐字节比对。
以下命令均从工程根目录执行：

```powershell
python tools/fonts/gen_map.py --base -o tools/fonts/base
.\tools\fonts\bdfconv.exe -b 0 -f 1 -M tools/fonts/base/wqy9.map  -n u8g2_font_wqy9_t_lunar  -o tools/fonts/wqy9_base.c  tools/fonts/wenquanyi_9ptb.bdf
.\tools\fonts\bdfconv.exe -b 0 -f 1 -M tools/fonts/base/wqy12.map -n u8g2_font_wqy12_t_lunar -o tools/fonts/wqy12_base.c tools/fonts/wenquanyi_12ptb.bdf
```

判定标准：`Glyphs` 的**字形数**必须是 228 / 142（说明字符集反解正确）；`Fontname`、`BBX Build Mode: 0` 与数组长度用于判断 BDF 是否选对。
按第二节实测，`wqy12` 用 `wenquanyi_12ptb.bdf` 应与现有字库完全一致；`wqy9` 用 medium 版 9pt BDF 时 `Fontname`/长度不同属预期，可换 bold 版 BDF，也可接受字形略细继续往下做。

### 4. 正式生成（含新字）

```powershell
.\tools\fonts\bdfconv.exe -b 0 -f 1 -M tools/fonts/new/wqy9.map  -n u8g2_font_wqy9_t_lunar  -o tools/fonts/wqy9.c  tools/fonts/wenquanyi_9ptb.bdf
.\tools\fonts\bdfconv.exe -b 0 -f 1 -M tools/fonts/new/wqy12.map -n u8g2_font_wqy12_t_lunar -o tools/fonts/wqy12.c tools/fonts/wenquanyi_12ptb.bdf
```

MSYS2 环境下把 `.\tools\fonts\bdfconv.exe` 换成 `./tools/fonts/bdfconv`。参数含义：

| 参数 | 值 | 说明 |
|---|---|---|
| `-b` | `0` | BBX build mode，须与现有字库头 `BBX Build Mode: 0` 一致 |
| `-f` | `1` | 输出 u8g2 字体格式 |
| `-M` | `tools/fonts/new/wqy9.map` / `wqy12.map` | 字符集文件，两套字库各用各的（与 `-m` 二选一，同时给时 `-M` 优先） |
| `-n` | 数组名 | 必须与 `GUI/fonts.h` 的 `extern` 名称一致 |
| `-o` | 输出 `.c` | 生成结果 |
| 末尾位置参数 | BDF 路径 | 输入点阵字体 |

`bdfconv` 输出的声明格式天然带 `const uint8_t 名称[N] U8G2_FONT_SECTION("名称") = "..."`，与 `GUI/fonts.c` 完全一致，**不需要手工写任何点阵字节**。

### 5. 落地改动

| 文件 | 改动 |
|---|---|
| `GUI/fonts.c` | 用 `tools/fonts/wqy9.c` / `tools/fonts/wqy12.c` 的数组定义段分别替换 `:9`、`:152` 两个数组；保留文件顶部 `#include "fonts.h"`；数组长度由工具自动写好 |
| `GUI/fonts.h` | 在 `:7-25` 的字符集清单里补上「宝」（供以后再次生成） |
| `GUI/GUI.c` | `:24-33` 的名称改为「大宝节」「小宝节」，文件保持 UTF-8 编码 |

`GUI/fonts.h` 的 `extern const uint8_t ... []` 不带长度，**不用改**；`Makefile`、`Keil/*.uvprojx` 已包含 `fonts.c`，也不用改。
`helvB14_tn` / `helvB18_tn` 只画数字，纯汉字改动无需重生成。

### 6. 验证

1. 新输出头注释的 `Glyphs` 应从 228 / 142 变成 229 / 143。
2. `make` 编译模拟器（见 `docs/develop.md`），把日期设到对应节日，分别检查 4.2 寸（`wqy9`）与 7.5 寸（`wqy12`）布局都完整显示，且原有节日、农历、节气文字没有丢失。
3. Keil 编译确认 Flash 占用：新增 1 个汉字约几十字节 × 2，可忽略；若体积暴涨说明字符集/BDF 选错。

## 四、常见坑

- **不要手工往 `fonts.c` 的转义字符串里插字节**：字库包含 Unicode 查找表与各块偏移，手工改动会破坏整个数组，只能通过 `bdfconv` 重新生成。
- **两套中文字库都要更新**，只改一套会在另一种屏幕上缺字。
- **名称最多 3 个汉字**：`GUI/GUI.c:21` 的 `name[10]` 与 `:263` 的 `buf[10]` 是 `3x3+1`，且 `GetFestival()` 用 `strcpy` / `strcat` 无长度保护。超过 3 字需同步加大这两个数组。
- **只用字库里已有的字拼名称**则完全不用动字库，例如「庆」「安」等（见第一节清单）；现有的 `正庆虎`、`节庆蛇` 就是这么处理的。
- map 文件必须**无 BOM**，否则 `bdfconv` 解析首项失败；`gen_map.py` 已按 ASCII 无 BOM 输出，不要再用记事本另存为 UTF-8 BOM。
- 若生成后字形变大、字距变化或 `Fontname` 不同，说明 BDF 字号 / bold 版本 / `-b` 参数与原字库不一致。
- 只改 `GUI.c` 不改字库不会报错，只是新字显示为空白。

## 五、附：检查字库里是否已有某个字

如需单独查询某个字是否已在字库中，可将下面脚本保存为 `tools/fonts/check_font.py`，在工程根目录执行 `python tools/fonts/check_font.py 宝 大 小`。
`tools/fonts/gen_map.py` 内含相同的解析逻辑（并带字形数自检）；下面脚本只用于快速查询，无需编译固件：

```python
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
```
