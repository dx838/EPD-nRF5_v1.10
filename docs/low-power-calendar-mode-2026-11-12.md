# 日历模式低功耗改造（2026-11-12）

> 变更记录 + 设计说明。全部改动只落在 `main.c`，共 6 处。
> 文中的行号为 **2026-11-12 改完后** 的 `main.c` 行号，后续再改动请以宏名 / 函数名定位。

## 一、目标

1. 上电 / 复位后 **15 分钟内可蓝牙连接**，之后不再发广播。
2. 时钟 tick 从 **1 s 放宽到 10 s**，减少 CPU 周期性唤醒。
3. 停播后不设任何唤醒源，**仅断电 / 复位才重新开窗**（静态计数变量复位归零天然实现）。
4. 不改日历刷新逻辑、不改睡眠方式、不进 System OFF。

省电来源：广播占空比从 100% 降到 `15 min / 24 h ≈ 1%`；CPU 唤醒次数降低 90%。
注意这**不是**省到极限：IDLE 下 10 s tick、SoftDevice RTC0、LFCLK（内部 RC 周期校准）、每天一次刷屏仍在耗电。

## 二、改动清单

### A 组：15 分钟广播窗口

| # | 位置 | 原值 | 新值 |
|---|---|---|---|
| A1 | `main.c:56-59` | `APP_ADV_TIMEOUT_IN_SECONDS 120` | `150`，并新增 `APP_ADV_WINDOW_RESTARTS 5` |
| A2 | `main.c:111` | 无 | `static uint8_t m_adv_restarts;`（放在 `// clang-format on` 之前） |
| A3 | `main.c:446` | `} else { advertising_start(); }` | `} else if (m_adv_restarts++ < APP_ADV_WINDOW_RESTARTS) { advertising_start(); }` |

- 单段 150 s × 6 段（初始 1 段 + 续播 5 段）= **900 s = 15 min**。
- `BLE_ADV_EVT_IDLE` 里的 `wakeup_pin != 0xFF` 分支**一个字都没动**，图片模式 / GPIOTE 唤醒行为保持不变；只改默认配置（`wakeup_pin = 0xFF`，见 `EPD/EPD_service.c:27`）下原本无限重播的那条路径。
- 旧代码全部以注释形式保留在 `main.c` 中，便于对照和回滚。

#### A 组代码（改前 → 改后）

> 说明：以下按变化点分段截取，只列相关行；改后块中不再重复列出未变化的行（如 `APP_ADV_INTERVAL`）。`/* ... */` 是文档的分组标注，不属于源码；带"（A 组）/（B 组）"及被注释掉的旧值行，是 `main.c` 中实际保留的注释。

改前（改造前的 `main.c:55-56, 98-104, 404-418`）：

```c
/* 宏区 */
#define APP_ADV_INTERVAL                 1600                                           /**< The advertising interval (in units of 0.625 ms. This value corresponds to 1 s). */
#define APP_ADV_TIMEOUT_IN_SECONDS       120                                            /**< The advertising timeout (in units of seconds). */

/* 全局变量区末尾 */
static uint32_t                          m_resetreas;
// clang-format on

/* on_adv_evt() */
static void on_adv_evt(ble_adv_evt_t ble_adv_evt) {
    switch (ble_adv_evt) {
        case BLE_ADV_EVT_FAST:
            break;
        case BLE_ADV_EVT_IDLE:
            NRF_LOG_INFO("advertising timeout\n");
            if (m_epd.config.wakeup_pin != 0xFF) {
                if (m_epd.config.display_mode == MODE_PICTURE)
                    sleep_mode_enter();
                else
                    setup_wakeup_pin(m_epd.config.wakeup_pin);
            } else {
                advertising_start();
            }
            break;
        default:
            break;
    }
}
```

改后（当前 `main.c:56-60, 109-114, 423-455`，旧行保留为注释）：

```c
/* 宏区 */
//#define APP_ADV_TIMEOUT_IN_SECONDS       120                                            /**< The advertising timeout (in units of seconds). */
// 广播宏（A 组）— main.c:56
#define APP_ADV_TIMEOUT_IN_SECONDS       150   /**< 单段广播 150 s，须 < limited disc 的 180 s 上限 */
#define APP_ADV_WINDOW_RESTARTS          5     /**< 续播 5 次：150 s × 6 段 = 上电 15 分钟蓝牙窗口 */
//广播宏（A 组）— main.c:56

/* 全局变量区末尾 */
static uint32_t                          m_resetreas;
//新增计数变量（A 组）— main.c:103 之后、// clang-format on 之前
static uint8_t                          m_adv_restarts;   /**< 广播续播计数；静态变量复位自动归零 = 仅断电/复位才重新开窗 */
//新增计数变量（A 组）— main.c:103 之后、// clang-format on 之前

// clang-format on

/* on_adv_evt() */
static void on_adv_evt(ble_adv_evt_t ble_adv_evt) {
    switch (ble_adv_evt) {
        case BLE_ADV_EVT_FAST:
            break;
        // case BLE_ADV_EVT_IDLE:
        //     NRF_LOG_INFO("advertising timeout\n");
        //     if (m_epd.config.wakeup_pin != 0xFF) {
        //         if (m_epd.config.display_mode == MODE_PICTURE)
        //             sleep_mode_enter();
        //         else
        //             setup_wakeup_pin(m_epd.config.wakeup_pin);
        //     } else {
        //         advertising_start();
        //     }
        //     break;
        //广播超时处理（A 组）— main.c:408-418
        case BLE_ADV_EVT_IDLE:
            NRF_LOG_INFO("advertising timeout\n");
            if (m_epd.config.wakeup_pin != 0xFF) {
                if (m_epd.config.display_mode == MODE_PICTURE)
                    sleep_mode_enter();
                else
                    setup_wakeup_pin(m_epd.config.wakeup_pin);
            } else if (m_adv_restarts++ < APP_ADV_WINDOW_RESTARTS) {
                // 上电 15 分钟内续播；到点后不再续播，广播已由 SoftDevice 超时自然停止
                advertising_start();
            }
            break;
        //广播超时处理（A 组）— main.c:408-418
        default:
            break;
    }
}
```

### B 组：10 秒 tick

| # | 位置 | 原值 | 新值 |
|---|---|---|---|
| B1 | `main.c:90` | `CLOCK_TIMER_INTERVAL TIMER_TICKS(1000)` | `TIMER_TICKS(10000)` |
| B2 | `main.c:243` | `m_timestamp++` | `m_timestamp += 10` |
| B3 | `main.c:142` | `m_timestamp = timestamp;` | `m_timestamp = timestamp - timestamp % 10;` |

- `set_timestamp()` 中的 `app_timer_start(..., CLOCK_TIMER_INTERVAL, NULL)` 用的是宏，自动跟随 B1，未单独改。
- `app_feed_wdt()`（`main.c:148-153`）**故意不改**。

#### B 组代码（改前 → 改后）

改前（改造前的 `main.c:84, 125-129, 222-228`）：

```c
#define CLOCK_TIMER_INTERVAL             TIMER_TICKS(1000)                              /**< Clock timer interval (ticks). */

void set_timestamp(uint32_t timestamp) {
    app_timer_stop(m_clock_timer_id);
    m_timestamp = timestamp;
    app_timer_start(m_clock_timer_id, CLOCK_TIMER_INTERVAL, NULL);
}

static void clock_timer_timeout_handler(void* p_context) {
    UNUSED_PARAMETER(p_context);

    m_timestamp++;

    ble_epd_on_timer(&m_epd, m_timestamp, false);
}
```

改后（当前 `main.c:88-91, 135-145, 238-247`，旧行保留为注释）：

```c
//#define CLOCK_TIMER_INTERVAL             TIMER_TICKS(1000)                              /**< Clock timer interval (ticks). */
//时钟定时器宏（B 组）— main.c:84
#define CLOCK_TIMER_INTERVAL             TIMER_TICKS(10000)   /**< 每 10 s 唤醒一次，减少 CPU 唤醒；30 s 喂狗仍安全（WDT 60 s） */
//时钟定时器宏（B 组）— main.c:84

void set_timestamp(uint32_t timestamp) {
    // app_timer_stop(m_clock_timer_id);
    // m_timestamp = timestamp;
    // app_timer_start(m_clock_timer_id, CLOCK_TIMER_INTERVAL, NULL);
    //对齐时间戳（B 组）— main.c:125-129
    app_timer_stop(m_clock_timer_id);
    // 对齐到 10 s：否则 timestamp % 60 / % 86400 永远不成立，日历和时钟都不再刷新
    m_timestamp = timestamp - timestamp % 10;
    app_timer_start(m_clock_timer_id, CLOCK_TIMER_INTERVAL, NULL);
    //对齐时间戳（B 组）— main.c:125-129
}

static void clock_timer_timeout_handler(void* p_context) {
    UNUSED_PARAMETER(p_context);

    // m_timestamp++;
    //时间戳步进（B 组）— main.c:225
    m_timestamp += 10;   // 与 CLOCK_TIMER_INTERVAL 保持一致，否则时间走慢 10 倍
    //时间戳步进（B 组）— main.c:225

    ble_epd_on_timer(&m_epd, m_timestamp, false);
}
```

## 三、关键约束与原因（注释要点）

### 为什么是 150 s × 6，而不是把 timeout 直接写 900

`ble_adv_fast_timeout` 最终写入 `ble_gap_adv_params_t::duration`（`SDK/17.1.0_ddde560/components/ble/ble_advertising/ble_advertising.c:311`），该字段是 `uint16_t`、单位 10 ms（`components/softdevice/s112/headers/ble_gap.h:681`），上限 655.35 s；90000 会被截断成约 245 s。另外当前广播标志是 `BLE_GAP_ADV_FLAGS_LE_ONLY_LIMITED_DISC_MODE`，limited discoverable 上限 180 s（`ble_gap.h:343`）。150 s 同时满足两个限制。

`APP_ADV_TIMEOUT_IN_SECONDS` 是**跨目标共用宏**：`main.c:177`（`advertising_config_get`）、`main.c:654`（S112 初始化，×100 = 15000 / 10 ms = 150 s）、`main.c:678`（nRF51 分支，直接按秒用）。改成 150 后 nRF51 目标的单段广播时长也同步变化。

### 为什么 IDLE 后不需要主动停广播

`BLE_ADV_EVT_IDLE` 产生时 `ble_advertising` 不会重配广播参数（`ble_advertising.c:637-639, 661-664`），SoftDevice 的广播已因 timeout 自然停止，因此不用调 `sd_ble_gap_adv_stop()`，只要不再续播即可。

### 为什么 B3 的对齐不能省（最容易漏的一处）

`EPD/EPD_service.c:431-438` 靠 `timestamp % 86400 == 0`（日历 0 点）和 `timestamp % 60 == 0`（时钟整分）触发刷新。1 s tick 时无论起点是什么都会撞上边界；改成 10 s 后，`m_timestamp` 只在固定的模 10 序列上走，而 `SET_TIME` 传来的 unix 秒几乎必然不是 10 的倍数（`EPD_service.c:198-199`，时区偏移 3600 是 10 的倍数但救不了它）。不对齐的话两个取模**永不成立，日历和时钟都不再刷新**。

上电默认值 `1735689600` 恰好是 10 的倍数，所以会出现"不校时看着正常、一校时就不刷新"的隐蔽故障。向下对齐到 10 s 后，60 和 86400 都能被 10 整除，序列必命中。代价：时间最多慢 9 秒，每次校时都向下取整、**不累积**；日历显示日期、时钟显示到分钟，无感。

### 为什么 WDT 不用改，以及 10 s 为什么是安全档

`WDT_CONFIG_BEHAVIOUR 0` = Pause in SLEEP and HALT（`sdk_config.h:5382`），超时 60 s（`sdk_config.h:5389`）。`app_feed_wdt()` 靠 `m_timestamp - m_wdt_last_feed_time >= 30` 判断：10 s tick 下差值走 10 / 20 / 30，**每 30 s 喂一次**，仍然安全。若把 tick 改成 60 s，差值要等 60 s 才满足 30，正好撞上超时边界会误复位，届时必须把喂狗逻辑与 `m_timestamp` 解耦。

`TIMER_TICKS(10000)` = 163840 tick @16384 Hz，远小于 24 位 RTC 周期，SDK 一次 compare 即可覆盖，不产生额外中断。

## 四、已知未处理项（暂不做，非漏改）

| 项 | 位置 | 影响 |
|---|---|---|
| 断连自动重播 | `ble_advertising.c:113-116` | 15 min 内连上又断开会自动多播一段 150 s，且不增加计数，窗口可能略超 15 min。要严格可在第 6 次 IDLE 时用 `advertising_config_get()` + `ble_adv_on_disconnect_disabled = true` + `ble_advertising_modes_config_set()` 加固（DFU 分支有现成写法）。 |
| GPIOTE 唤醒后重开广播 | `main.c:405` | `gpiote_evt_handler()` 里仍有 `advertising_start()`；默认 `wakeup_pin = 0xFF` 时走不到。 |
| `force_update` 传未对齐值 | `EPD_service.c:202` | 与内部 `m_timestamp` 最多差 9 s，仅在 0 点前后几秒校时时首次刷新可能差一天；介意可改成 `timestamp()`。 |
| 时间回读粒度 | `main.c:132` | `timestamp()` 变成 10 s 粒度，Web 端 `t=...` 最多滞后 9 s。 |
| 时间戳漂移 | `sdk_config.h:10555-10587` | 内部 RC 500 ppm ≈ 43 s/天，且停播后无法重连校时，漂移会一直累积。板上有 32.768 kHz 晶振时建议按 `docs/develop.md:40-44` 改 XTAL / 20 ppm（≈1.7 s/天）。 |

## 五、验证

`Makefile` 只编译 Windows GUI 模拟器（`emulator.c` + `GUI/*.c`），**不含 `main.c`**，固件请用 Keil 编译。

1. 编译无新增告警；IDE 静态诊断 0 条（2026-11-12 已确认）。
2. 抓包：上电 0–15 min 有 ADV_IND，之后静默；复位后重新出现。
3. **不校时**和**校时后**两种情况下，日历都能在 0 点刷新、`MODE_CLOCK` 仍每分钟刷（专门验 B3）。
4. 连续运行 24 h：WDT 不复位、时间戳不漂移。
5. 对比改前 / 改后的 IDLE 静态平均电流与一次刷新的电量积分，并回填第七节 7.5 的实测表。

## 六、回滚

旧代码均以注释形式保留在 `main.c` 中：恢复注释掉的旧行、删除新增的 `APP_ADV_WINDOW_RESTARTS` / `m_adv_restarts` / 新 case，并把 `else if` 改回 `else` 即可。两组改动互不依赖，可以只回滚其中一组。

## 七、预估省电效果（估算，非实测）

> ⚠ 仓库内**没有任何电流实测数据**。以下为基于本项目代码参数 + nRF52 系列典型电流值的数量级估算，用于判断收益优先级，**不能当作规格值**。第五节验证完成后请把实测数据回填到本节末尾的表格。

### 7.1 平均电流分项对比

| 耗电项 | 改前 | 改后 | 依据 |
|---|---|---|---|
| 广播射频（摊到 24 h） | 约 15–30 µA | 约 0.2–0.3 µA | 改前 1 s 间隔 ADV_IND 无限重播；改后仅开机 15 min，占空比 `900/86400 ≈ 1.04%` |
| System ON 基底 | 约 2–3 µA | 约 2–3 µA | **不变**：RAM 保留 + LFCLK(内部 RC + 周期校准) + SoftDevice RTC0/RTC1 |
| 时钟 tick 唤醒 | 约 1 µA | 约 0.1 µA | 1 s → 10 s，唤醒次数降 90% |
| 每日 EPD 刷新（摊到 24 h） | 约 2–5 µA | 约 2–5 µA | **不变**：3 色屏约 15 s / BW LUT 2–3 s（`docs/README.md:124`） |
| **合计平均电流** | **约 20–40 µA** | **约 4–9 µA** | 降幅约 **75–85%** |

其中：

- **广播是绝对大头**，贡献了降幅的 90% 以上，与"停广播"这个改动直接对应。
- **10 s tick 只再省约 1 µA**（约占降幅 3–5%）。它改动小、风险低，但不要期待它带来第二次数量级改善。
- 15 min 窗口期内电流仍是改前水平（约 20–40 µA），只是占全天 1% 而已。

### 7.2 续航示例（理想化）

以 CR2032 / 220 mAh 为例，仅按平均电流线性折算：

| | 平均电流 | 理论续航 |
|---|---|---|
| 改前 | 30 µA（取中值） | `220 mAh / 0.030 mA ≈ 7300 h ≈ 10 个月` |
| 改后 | 6.5 µA（取中值） | `220 mAh / 0.0065 mA ≈ 34000 h ≈ 3.9 年` |

即**从"月级"提升到"年级"**。但这个年限没有工程意义：纽扣电池内阻高，EPD 刷新瞬间的 10–30 mA 脉冲会造成明显压降和容量损失；电池自放电、shelf life、温度也都没计入。真实续航必须实测。

### 7.3 假设与误差来源

- 3.0 V 供电、室温、**未启用 DC/DC**（`sdk_config.h:2197, 2220, 4282, 4307` 全为 0，代码也未调 `sd_power_dcdc_mode_set()`）。
- TX power 取 SoftDevice 默认值 0 dBm（源码未设置，无法从仓库确认实际值）。
- 广播含 `FULL_NAME` + scan response 里的 128-bit UUID（`main.c:645-650`）；被主动扫描时每轮多发一包，估算按偏保守取值。
- LFCLK 为内部 RC + 500 ppm、需周期校准（`sdk_config.h:10555-10587`），校准时的 HFCLK 唤醒已计入基底。
- **最大不确定项是 EPD 面板刷新电流**：屏型、LUT、升压电路差异极大，仓库无原理图/BOM。
- System ON 基底、射频峰值电流取 nRF52 系列公开典型值，非本板实测。
- 未计入：电池自放电与内阻压降、温度、BLE 连接 / 传图 / DFU、FDS 写入、WDT 唤醒、低电压下的刷新失败重试。
- 估算按"日历模式、每天只刷一次、无连接"的稳态场景；`MODE_CLOCK`（每分钟刷）不适用此表。

### 7.4 改完后剩下的大头

IDLE 下剩余耗电主要是 **System ON 基底（2–3 µA）** 和 **每天一次 EPD 刷新（2–5 µA）**，而不是 CPU tick。所以继续把 tick 拉到 30 s / 60 s 收益不到 1 µA，反而要处理 WDT 喂狗解耦（见第三节）。更有效的下一步是：

1. 3 色屏改用 BW LUT，把刷新从 15 s 降到 2–3 s（`docs/README.md:124`）——直接砍掉每天最大的一笔电量。
2. 板上有 32.768 kHz 晶振时改 XTAL / 20 ppm（`docs/develop.md:40-44`），省掉 RC 周期校准，同时抑制时间戳漂移。
3. 板上有 DC/DC 电感时开启 DC/DC，降低射频与 CPU 峰值电流。

以上均不在本次改动范围内。

### 7.5 实测回填

| 场景 | 实测值 | 测量条件 / 日期 |
|---|---|---|
| 改前 IDLE 平均电流 | ____ µA | |
| 改后 IDLE 平均电流 | ____ µA | |
| 15 min 窗口期平均电流 | ____ µA | |
| 一次 EPD 刷新的电量 | ____ mC | |
| 电池型号 / 实测续航 | | |

---

### 备注（自行补充）

<!-- 在此记录实测电流、编译结果、抓包结论或后续调整 -->
