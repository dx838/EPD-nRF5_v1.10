# 放假 / 调休数据维护说明

`GUI/GUI.c` 中的 `HOLIDAY_YEAR` 与 `holidays[]` 用于日历上标注「休 / 班」，需每年更新。
`DrawMonthDays()` 仅在 `year == HOLIDAY_YEAR` 时调用 `GetHoliday()`，其它年份只按周末着色，不显示休/班。

## 一、数据规则

每个日期编码为一个 `uint16_t`，写作 `0xABCD`：

| 位 | 含义 | 说明 |
|---|---|---|
| A (bit15~12) | 类型 | `0` = 放假（休），`1` = 调休上班（班） |
| B (bit11~8) | 月 | 1~9 与十进制相同，10/11/12 写作 `A`/`B`/`C` |
| CD (bit7~0) | 日 | 十进制日号的**十六进制写法**，占两位 |

等价表达式：`value = (work << 12) | (month << 8) | day`，其中 `month`、`day` 均为十进制数值。

示例：

| 日期 | 编码 | 计算 |
|---|---|---|
| 1/1 休 | `0x0101` | `(0<<12) \| (1<<8) \| 1` |
| 1/31 班 | `0x111F` | 31 = `0x1F` |
| 2/10 休 | `0x020A` | 10 = `0x0A` |
| 9/15 休 | `0x090F` | 15 = `0x0F` |
| 9/26 班 | `0x191A` | 26 = `0x1A` |
| 10/9 班 | `0x1A09` | 10 月 = `0xA` |

**易错点**

- 不是 BCD，不能按字面写日期：9 月 26 日是 `0x091A`，不是 `0x0926`（后者会被解码成 9 月 38 日）。
- `GetHoliday()` 用 `(v >> 8) & 0xF` 取月、`v & 0xFF` 取日，与十进制的 `mon` / `day` 直接比较；`(v >> 12) & 0xF` 非 0 即为「班」。
- 数组按日期升序排列；放假需覆盖**整个连休区间的每一天**（含区间内的普通周末），另外加上所有补班上班日。
- `GetHoliday()` 的循环下标是 `uint8_t`，数组长度必须小于 256（2026 年 38 项、2027 年 34 项）。

## 二、数据源

官方通知一般在每年 11 月前后发布，结构化数据源都由此派生，最终以国务院公告为准。
下列「实测」为 2026-11-07 的验证结果。

### 权威原文

| 来源 | 地址 | 用途 |
|---|---|---|
| 国务院办公厅《关于 YYYY 年部分节假日安排的通知》 | 2027: `https://www.gov.cn/zhengce/zhengceku/202611/content_7085102.htm`、`https://www.gov.cn/zhengce/content/202611/content_7085101.htm` | 人工核对的最终依据 |

### 推荐：结构化年度 JSON

| 来源 | 地址 | 字段 / 判定 | 实测 |
|---|---|---|---|
| **chinese-days 按年 JSON**（首选，直接生成数组） | `https://fastly.jsdelivr.net/npm/chinese-days/dist/years/{YYYY}.json`<br>备用：`https://cdn.jsdelivr.net/npm/chinese-days/dist/years/{YYYY}.json` | `holidays` 日期键 = 休；`workdays` 日期键 = 班；`inLieuDays` = 调休来源，可忽略 | ✅ 2027 有 34 个日期，自动生成的数组与 `GUI.c` 逐项一致 |
| **chinese-days 复核数据**（人工核对） | `https://github.com/vsme/chinese-days/blob/main/data/holiday-reviews/{YYYY}.json`<br>raw：`https://raw.githubusercontent.com/vsme/chinese-days/main/data/holiday-reviews/{YYYY}.json` | `review.holidays[].rest[]` 放假、`work[]` 补班、`inLieu[]` 调休日；`evidence[].quote` 附国务院原文 | ✅ 2027 已收录 |
| **holiday-cn**（备选，MIT，每日自动抓取国务院公告） | `https://fastly.jsdelivr.net/gh/NateScarlet/holiday-cn@master/{YYYY}.json`<br>`https://raw.githubusercontent.com/NateScarlet/holiday-cn/master/{YYYY}.json`<br>仓库 `https://github.com/NateScarlet/holiday-cn` | `days[]: {name, date, isOffDay}`，`isOffDay=true` 休 / `false` 班；`papers[]` 指向国务院公告；另有 `{YYYY}.ics` | ✅ 2027 有 34 条，与上述数据一致 |

`holiday-cn` 按国务院文件标题年份归档，跨年的 12 月 / 1 月日期可能落在相邻年份文件里，必要时同时检查两年。

### 其它可用来源

| 来源 | 地址 | 说明 | 实测 |
|---|---|---|---|
| holiday.dreace.top 单日查询 | `https://holiday.dreace.top/?date=2027-01-31` → `{"date":...,"isHoliday":false,"note":"补班工作日","type":"工作日"}` | 逐日校验用；`note="补班工作日"` 即班。仓库 `Dreace/ChinaHolidayAPI` 可自建并下载 2023–2027 全年 JSON | ✅ 放假 / 补班均正确 |
| chinesecalendar（Python，`pip install chinesecalendar`） | 仓库 `https://github.com/liriansu-opus/chinese-calendar`（原 LKI） | 支持 2004–2027，`is_holiday()` / `is_workday()` / `is_in_lieu()`，可离线遍历全年生成数组；每年 11 月左右发新版 | 仓库 README 确认支持 2027 |
| timor.tech 年度接口 | `https://timor.tech/api/holiday/year/{YYYY}` | `holiday` 映射，`holiday:true` 休 / `false` 补班（name 含「补班」，`target` 指对应假期）；需带 UA | ⚠️ 2026 正常，**2027 返回 `{"code":0,"holiday":{}}`（尚未录入）**，等更新后再用 |
| APIHubs | `https://api.apihubs.cn/holiday/get?field=date,holiday_recess,workday&year={YYYY}&size=400&page=1` | 逐日返回 `date/workday/holiday_recess`，字段语义需自行确认 | ✅ 2027 返回 365 天，适合按日查询，不适合直接生成 |
| iCal 订阅（日历客户端订阅，非本固件用） | `https://cdn.jsdelivr.net/npm/chinese-days/dist/years/{YYYY}.ics`、`https://cdn.jsdelivr.net/npm/chinese-days/dist/holidays.ics` | 近三年节假日 + 调休 | 未实测 |

### 不适用 / 勿用

- `https://date.nager.at/api/v3/PublicHolidays/{YYYY}/CN`：只有 6 个法定节日本身，**不含连休区间和补班工作日**，无法生成 `holidays[]`。
- `https://github.com/vsme/chinese-days/blob/main/data/holiday-releases/{YYYY}.json`：只有 `year/version/pr/mergeSha` 发布元数据，无日期明细。
- 需 API Key 的聚合类接口（聚合数据、万维易源等）：本项目是离线固件，不引入运行时依赖。

### 本环境网络备注

- 本机直连：`raw.githubusercontent.com` 200、`fastly.jsdelivr.net` 200；`cdn.jsdelivr.net` SSL 握手失败。
- 内置网页抓取工具对 `raw.githubusercontent.com` / `cdn.jsdelivr.net` 会失败，但 `github.com/.../blob/...` 页面和 `fastly.jsdelivr.net` 可用。生成数据时优先用 `fastly.jsdelivr.net`。

## 三、每年更新步骤

1. 等国务院办公厅发布下一年通知（通常 11 月），确认官方放假区间与补班日。
2. 取 `https://fastly.jsdelivr.net/npm/chinese-days/dist/years/{YYYY}.json`（或 `holiday-cn` 的 `{YYYY}.json`）生成数组，PowerShell 示例：

```powershell
$year = 2027
$j = Invoke-RestMethod "https://fastly.jsdelivr.net/npm/chinese-days/dist/years/$year.json"
$items = @()
foreach ($p in $j.holidays.PSObject.Properties) { $d = [datetime]$p.Name; $items += [pscustomobject]@{m=$d.Month; day=$d.Day; w=0} }
foreach ($p in $j.workdays.PSObject.Properties) { $d = [datetime]$p.Name; $items += [pscustomobject]@{m=$d.Month; day=$d.Day; w=1} }
$items | Sort-Object m,day | ForEach-Object { '0x{0:X1}{1:X1}{2:X2},' -f $_.w,$_.m,$_.day }
```

3. 用 `holiday-reviews/{YYYY}.json` 的 `evidence[].quote` 或国务院原文核对放假区间与补班日；注意不同源对「连休区间内的周末」是否收录可能不同，以官方通知的区间为准。
4. 更新 `GUI/GUI.c` 的 `HOLIDAY_YEAR` 和 `holidays[]`。
5. 反向解码校验：逐项还原 `(month, day, work)`，确认条数、升序、休/班标记与官方一致。

2026-11-07 校验：由 chinese-days 的 2027 JSON 自动生成 34 项，与 `GUI/GUI.c` 中的数组逐项完全一致。
