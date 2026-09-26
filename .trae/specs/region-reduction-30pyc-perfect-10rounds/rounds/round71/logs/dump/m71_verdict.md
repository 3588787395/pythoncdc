# R71 中心验证判决书 — 第二阶段：合并 m71 臂 + 五连复测

日期：2026-09-26　工作区：`D:/Temp/opencode/r71gate/center`　repo：`F:/Downloads/pythoncdc-main`（只读，`git status --porcelain --untracked-files=no` = 0 行改动）
产物：合并 spec `D:/Temp/opencode/r71gate/m71_region_ast_generator.py.json`、`m71_region_analyzer.py.json`；臂镜像 `center/mirr_m71`
所有原始输出均在 `center/dump/`。

---

## 0. 前置自检（步骤 1）— PASS

`dump/m71_precheck.txt`

- `R71-analyzer-merged.json` 的 edits 数 = 5 = `R71-exctable-analyzer.json`(2) + `R71-assert.json`(3)，anchor 集合相等；
- 对 repo 的 LF 归一文本：`apply(apply(base, A), B)` 与 `apply(base, merged)` 结果**逐字节相同**（len=1512965，28220 行）；
- 每步 anchor 均恰出现 1 次。
→ 判定：**等价，继续**。

## 1. mkfinal（步骤 2）— PASS

`dump/m71_mkfinal.txt`

| 文件 | edits | 净行数 | 来源 |
|---|---|---|---|
| `core/cfg/region_ast_generator.py` | 5 | **+137** | R71-exception_exit ×1、r71f2_full ×2、R71-exctable ×2 |
| `core/cfg/region_analyzer.py` | 5 | **+80** | R71-analyzer-merged ×5 |

链式锚点断言全过（每次替换前 anchor 出现恰好 1 次）。

## 2. mbuild（步骤 3）— PASS

`dump/m71_build.txt`、`dump/m71_mirr_stat.txt`

| 文件 | edits | 净行 | 字节 worktree → mirror | BOM | 行尾 |
|---|---|---|---|---|---|
| `region_ast_generator.py` | 5 | +137 | 3199517 → **3210453** | 保留（True→True） | 全 CRLF（51505/51505），无混排 |
| `region_analyzer.py` | 5 | +80 | 1763461 → **1769596** | 保留（False→False） | 全 CRLF（28220/28220），无混排 |

断言全部通过：镜像先与 worktree 字节相同、每个 anchor 各恰 1 次、BOM 保留、行尾统一、净行数与 spec 声明一致（+137 / +80）。

`dump/m71_armspec.txt`（附带校验）：`c1`、`r71f2f`、`f3ab`、`m71` 四个既有臂镜像逐字节等于「对应**已采纳** spec 施加于 worktree」的文本，且除 spec 文件外**无**其它 core 文件与 worktree 不同，`pycdc.py` 全部一致 → 步骤 g 用的对照臂确系已采纳候选。

---

## 3. 五连复测（步骤 4）

### a) 官方尺 56 靶 — **PASS**
`dump/m71_56.jsonl`、`dump/m71_ab56.txt`

```
TALLY SAME=38 IMPROVED=0 REGRESSION=0 MOVED=18 ERR=0  (unpaired lists=0)
files fully matched: a=48 b=48
```
判据 REGRESSION=0 ✅（IMPROVED=0 亦允许）。18 支 MOVED 均为 `gained=[] lost=[]`，即缺陷集合不变、仅产物文本变化。

### b) 金丝雀 — **PASS**
`dump/m71_canary.jsonl`、`dump/m71_abcanary.txt`、`dump/m71_quo_pv.txt`

| 支 | landed sha | m71 sha | 判据 |
|---|---|---|---|
| `fly/common/market_time` | `af77224b34b203c4` | `af77224b34b203c4` | SAME ✅ |
| `IQCommon/util/datetime_func` | `e711b8ea86d49a15` | `e711b8ea86d49a15` | SAME ✅ |
| `IQData/utils/datetime_func` | `9d09af09249da177` | `9d09af09249da177` | SAME ✅ |
| `fly/data/quotation` | `4d41187e356544e0` | **`3eb76e512df9ab1e`** | = 中心新 pin ✅ |

- quotation 官方读数 **143/143**（h62）✅
- mandated：`pyc_verify.py single .../fly/data/quotation.pyc --source build_m71/fly__data__quotationOK.py`
  → **`status=failure units=152/153`**，failure 集 = `{change_his_to_forward}`
  landed 基线 = `151/153`，failure 集 = `{change_his_to_forward, get_trend}`
  → `get_trend` **转绿**，0 新增，failure 集 ⊂ landed ✅
- sha 既非旧 pin 也非新 pin 的情况未出现；无新增 failure → 不触发停止条件。

### c) 电池 — **PASS**
`dump/m71_battery.txt`（82 个 repro = round63/64/65/66/67/68/69 批次 + 11 个 R62 pinned witness）

```
candidate columns worse-than-landed on 0 repro(s)
```
判据 worse-than-landed on 0 ✅（逐格对照 82 行全部 `landed == m71`）。

### d) 严格尺 — **PASS**
`dump/strict_m71_r71.json` vs `dump/strict_landed_r71.json` → `dump/m71_strict_ab.txt`

| 项 | landed | m71 |
|---|---|---|
| files / functions | 48 / 1819 | 48 / 1819 |
| ok | 1776 | **1780** |
| defects | 43 | **39** |
| target_diff | 20 | **17** |

```
NEW defect functions=0  NEW target_diff=0  FIXED defect functions=4
VERDICT: PASS
```
修绿的 4 个：`wizard_quant_api.init_stock_pool_filter`、`fly_api/base.OverNightOrder.__init__`、`quotation.get_trend`、`load_daily.filter_abnormal_data`。
补充（同样 0 新增）：all56 严格 87→80 缺陷（`dump/strict_m71_all56.json`）、f3 22 靶 54→48（`dump/strict_m71_f3tgt.json`）、cf1 31 靶 20→20（`dump/strict_m71_cf1.json`）。

### e) mandated 尺（sha 变化的 18 支）— **PASS**
`dump/m71_sha_changed.txt`、`dump/m71_pv_m71.txt`、`dump/m71_pv_landed.txt` → `dump/m71_pv.txt`

```
total failures: landed=45  m71=28  net=-17  fixed=17  NEW=0
VERDICT: PASS
```
18 支逐文件对照：9 支转为全绿（`IQCommon/exception`、`IQData/entry`、`IQData/utils/exception`、`fly_api/base`、`plugin_system_accounts/__init__`、`benchmark_account`、`stock_account`、`IQEngine/utils/exception`、`risk_calculation/function`），其余失败单元只减不增，**0 新增 failure**。

### f) 合成咬合 — **PASS**（10/10）
`center/dump/synth/`（编译产物 + `dump/m71_synth.txt`）

| 用例 | 期望 | landed | m71 | 结果 |
|---|---|---|---|---|
| t01 if_absorb_following_if (F-THENOVER) | success | failure 1/2 | **success 2/2** | PASS |
| t02 if_absorb_trailing_stmts (F-THENOVER) | success | failure 1/2 | **success 2/2** | PASS |
| t22 cross_loop_tail_stmt (F-THENOVER) | success | failure 1/2 | **success 2/2** | PASS |
| t24 assert_in_try (assert/exctable) | success | failure 1/2 | **success 2/2** | PASS |
| t27 try_except_else_range (assert/exctable) | success | failure 1/2 | **success 2/2** | PASS |
| exc_A (fix1) | success | failure 4/5 | **success 5/5** | PASS |
| t03 andchain_else（负） | 与 landed 同 | failure 1/2, sha 同 | failure 1/2, **sha 同** | PASS |
| t04 orchain_else（负） | 与 landed 同 | success 2/2, sha 同 | success 2/2, **sha 同** | PASS |
| t15 assert_then_unreachable（负） | 与 landed 同 | success 3/3, sha 同 | success 3/3, **sha 同** | PASS |
| t20 two_try_except_seq（负） | 与 landed 同 | success 2/2, sha 同 | success 2/2, **sha 同** | PASS |

（臂加载断言 `pycdc.__file__` 指向 `mirr_m71`；判定用 `scripts/pyc_verify.py single`。）

### g) 叠加一致性 — **PASS**
`dump/m71_union.txt`（9 个视角：56 靶 / f3 22 靶 / 金丝雀 / 电池 / 严格 div48 / 严格 all56 / 严格 f3 22 / 严格 cf1 / mandated all56）

各候选臂**各自修绿**的单元（相对其自身 landed 基线、只统计该臂实测过的文件）：

| 臂（= 已采纳候选） | 视角 | 修绿 | 仍在 m71 绿 | LOST | m71 未测 |
|---|---|---|---|---|---|
| fix1 `c1`（R71-exception_exit） | mandated all56 | 7 | **7** | 0 | 0 |
| fix1 `c1` | 56 靶/金丝雀/电池/严格 | 0 | 0 | 0 | 0 |
| fix2 `r71f2f`（r71f2_full） | mandated all56 | 7 | **7** | 0 | 0 |
| fix2 `r71f2f` | 严格 all56 | 6 | **6** | 0 | 0 |
| fix3 `f3ab`（exctable + analyzer-merged） | mandated all56 | 3 | **3** | 0 | 0 |
| fix3 `f3ab` | 严格 all56 / 严格 f3 22 | 1 | **1** | 0 | 0 |

- 跨全部视角的并集 = **17 个 (pyc, 函数)** 单元，**17 仍绿 / 0 LOST / 0 未测**；
- m71 在每个视角上的 **NEW failing units = 0**（无相互干扰、无回退）；
- m71 自身收益恰为并集：mandated 109→92 = −17；严格 all56 87→80 = −7（= fix2 的 6 + fix3 的 1）；严格 div48 43→39 = −4；
- 56 靶 / 金丝雀 / 电池三个视角上四臂读数完全一致（这些尺对三个候选都不敏感，故并集在这些视角为空，m71 亦一致）。
- 附 `dump/m71_armspec.txt`：对照臂镜像与已采纳 spec 逐字节一致，保证 g 的对照有效。

---

## 4. 判决

| 项 | 判据 | 结果 |
|---|---|---|
| 前置自检 | merged ≡ exctable-analyzer + assert 顺序套用 | **PASS** |
| mkfinal | 链式锚点全过，+137 / +80 | **PASS** |
| mbuild | 字节相同/锚点×1/BOM/行尾/净行数 | **PASS** |
| a) 56 靶 | REGRESSION=0 | **PASS**（SAME=38 IMPROVED=0 REGRESSION=0 MOVED=18） |
| b) 金丝雀 | 3 支 sha SAME + quotation 143/143 + 新 pin + 152/153 且 failure ⊂ landed | **PASS** |
| c) 电池 | worse-than-landed on 0 | **PASS** |
| d) 严格尺 | 无新增缺陷函数 / 无新增 target_diff | **PASS**（0/0，−4 缺陷） |
| e) mandated | 失败单元净减、0 新增 | **PASS**（45→28，net −17，NEW=0） |
| f) 合成咬合 | 6 正向 success + 4 负向同 landed | **PASS**（10/10） |
| g) 叠加一致性 | 并集且无干扰 | **PASS**（17/17 仍绿，0 丢失，0 新增失败单元） |

### 裁定：**GO** — 采纳落地建议：将 m71（4 件候选合并件）作为 R71 的落地候选进入下一门禁。

理由：七个复测项判据全绿；三支候选的收益在 m71 上完整保留（并集 17 单元无一丢失），m71 未在任何尺上新增失败单元；金丝雀只出现预期中的 quotation sha 变更（`4d41187e356544e0 → 3eb76e512df9ab1e`，与 fix2 §7 的新 pin 一致），且其 mandated 读数 151/153 → 152/153 属净改善。

无 FAIL 项，故不存在需要归因的冲突来源。

### 附注
- 未修改 repo：`git status --porcelain -uno` = 0 行；`core/cfg/__pycache__` 为 `.gitignore` 命中的非跟踪缓存。
- 未执行 402 全量扫描（G3 归后续门禁）。
- 本次为在候选臂读数之外补充的覆盖性读数（供 g 使用）：`dump/m71_f3tgt.jsonl`、`dump/f3ab_56.jsonl`、`dump/strict_{c1,f3ab}_all56.json`、`dump/strict_m71_{all56,f3tgt,cf1}.json`、`dump/m71_pv_{landed56,c1_56,f2_56,f3_56,all56}_{a,b}.txt`。
