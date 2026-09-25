# FACTS — Round 69 diag3 (klinedata / fileio_utils / api_base)

Prefix: r69diag3. Repo F:/Downloads/pythoncdc-main read-only for this agent.
Local CPython 3.11.7 == target pyc magic a70d0d0a.

## Step 0 — precheck (all MATCH, no correction needed)

### 0.1 targets.md official yardstick vs live run
| target | official (norm/strict/defect) | live recompute | verdict |
|---|---|---|---|
| IQCommon/api/klinedata | 43/45, 58/63, 5 defects | 43/45, 58/63, 5 | MATCH |
| IQCommon/util/fileio_utils | 12/14, 13/15, 2 defects | 12/14, 13/15, 2 | MATCH |
| IQData/api/api_base | 24/25, 26/27, 1 defect | 24/25, 26/27, 1 | MATCH |
| **total** | **79/84, 97/105, 8 defects** | same | MATCH |

per-function (targets.md):
- get_multiminute_his_data 479/478/3/16 ; kline_datetime_list 389/389/9/228
- FileLock.acquire 96/93/3/52 ; FileIO.write 637/636/0/38
- get_history_df 1742/1742/11/89

### 0.2 canary sha + counts (all MATCH)
- IQCommon/quotation.py 4d41187e356544e0 143/143
- IQCommon/market_time.py af77224b34b203c4 10/10
- IQCommon/IQCommon/datetime_func.py e711b8ea86d49a15 26/26
- IQData/IQData/datetime_func.py 9d09af09249da177 25/25

### 0.3 45-item battery landed
`closeout67.py battery landed` -> **182/200, defect functions 18, worse=0, ERR=0** (dump/repro65_landed.jsonl, header `closeout67.py battery landed`).

### 0.4 strict yardstick landed (`sstrict67.py build_landed targets.txt`)
- klinedata 58/63, defects 5
- fileio_utils 13/15, defects 2
- api_base 26/27, defects 1
- missing 0, extra 0; total **97/105, defects 8**

### 0.5 instruments confirmed
h62.py (build/run/ab, ROOT=D:/Temp/opencode/r69gate/diag3, build_<arm> + mirr_<arm>), nested_diff.py (normalizes EXTENDED_ARG), sstrict67.py, closeout67.py battery, mk_spec.py, disf.py, idx.py, probe_chain.py.
Known instrument defects: nhunks.py same-co-name AssertionError; nested_diff.py does NOT normalize EXTENDED_ARG -> insert artifacts.

## Step 1 — normalized hunk table (nested_diff.py)

### klinedata
| region | orig | decomp | hunks | judge |
|---|---|---|---|---|
| `<root>` | 545 | 541 | 2 | NOP artifact |
| `/get_multiminute_his_data#54` | 535 | 536 | 2 | TRUE DEFECT |
| `/kline_datetime_list#57` | 413 | 417 | 7 | 3x EXTENDED_ARG artifact + 4 true |
| `/get_price_common#67` | 594 | 596 | 2 | artifact |

### api_base
| region | orig | decomp | hunks | judge |
|---|---|---|---|---|
| `/get_history_df#26` | 1900 | 1900 | 4 | TRUE DEFECT (pure-shift family) |

### fileio_utils
| region | orig | decomp | hunks | judge |
|---|---|---|---|---|
| `/FileLock#9/acquire#7` | 114 | 108 | 3 | TRUE DEFECT |
| `/FileIO#11/write#6` | 720 | 719 | 2 | hunk=0 on target yardstick |

## Step 2 — root cause (byte-level measured, not inferred from source)

### 2.1 probes run
`probe1.py <pyc> <lo> <hi> <func>` — monkeypatches `RegionAnalyzer._build_basic_if_region`
and `_build_elif_region`, prints entry / then / else / merge / condition_block offsets.

### 2.2 kline_datetime_list + get_history_df — SAME SHAPE (2 of 5 defects)

Emitted indentation measured (`build_landed/…`), api_base get_history_df:
```
295 ind=12 if not include and frequency==MINUTE and cur not in (...):
296 ind=16     if pm_open > cur > am_close or cur > pm_close:
297 ind=20         if frequency==MINUTE: ... elif ...: ... else: ...
312 ind=16     time_count -= 1
```
TRUTH (byte-identical CPython 3.11.7 local compilation, jump deltas 32/26/6/13/1/5 exact):
```
295 if not include and freq==MINUTE and cur not in (...) and not (D or E):
296     time_count -= 1
297 if frequency==MINUTE: ... elif ...: ... else: ...      <- sibling of 295
```
i.e. block 2254 (line 297 if/elif/else head) is the region's **merge/continuation** of
`if COND: time_count -= 1` (fall-through from S at 2244 AND all condition false-jumps).

Probe output `get_history_df`:
```
[basic#85] entry@2144 then=[2202,2218,2230,2228,2232,2244] else=[] merge=2254 cond=2190
[basic#84] entry@2232 then=[2244] else=[] merge=2254
```
- condition blocks 2144/2148/2190 each `POP_JUMP_IF_* -> 2254` (= merge)  -> recognized as condition, chain stops.
- block 2202 `POP_JUMP_IF_FALSE 2230` (else-target is an **in-chain continuation**, not the merge)
  -> NOT recognized as a condition block -> swept into `then_blocks`.
- block 2232 `POP_JUMP_IF_TRUE 2254` (= merge) / fall-through 2244 (S).

=> The trailing `or` sub-chain of the guard sits in `then`. Generator, emitting that nested
conditional inside the then-branch, sees its forward target == the parent region's **merge**
and inlines the merge body into the nested if's then-branch (api_base) or pushes S after the
merge body (klinedata: `time_count -= 1` at ind=933 after the whole if/elif/else).
Both are the same root cause; different emission outcome.

Judgment: **guard-condition chain walk terminates as soon as a conditional block's
else-target is not the region merge; the remaining condition sub-chain falls into then.**

### 2.3 get_multiminute_his_data — merge attribution

Probe output:
```
[basic#95] entry@68 then=[82,170,418,718,472,730,824,816,820,1090,1314,2758,1094,…,2708,1594,…] else=[] merge=2710
[basic#93] entry@718 then=[730,816,820] else=[824,…] merge=2758
```
- True convergence (all paths: idx161@822 jump, idx518@2708 jump, else fall-through) = **2758**
  (`LOAD his_data_dict; RETURN`).
- Root region reports **merge=2710**, and `then` contains 2758 which is at a HIGHER offset than
  its own merge -> structurally impossible for a well-formed region.
- Consequence: the shared tail `return his_data_dict` is attached to the then-branch;
  the else path falls past it and is terminated with `LOAD_CONST None; RETURN`.
Judgment: **`_build_basic_if_region` picked the wrong merge (a block inside the else path)
instead of the common post-dominator; the shared tail consequently landed in then.**

### 2.4 FileLock.acquire — region attribution + lost JUMP_BACKWARD

Probe output:
```
[basic#3] entry@152 then=[214] else=[532,582] merge=None   (timeout check @~188..212)
[basic#4] entry@108 then=[150] else=[152,532,582] merge=None
```
- `if timeout` region: then = **[214] only** (warning block). The unlink/try/`raise
  FileLockException` blocks (304..502) are NOT in the then; they are attached at the
  handler/try level, so emission becomes `if timeout: warning else: sleep` followed by
  try/raise as a SIBLING.
- else = [532, 582] pulls the loop back-edge (`EXTENDED_ARG; JUMP_BACKWARD` at 107/108)
  into the else of the timeout-if.
- Decompiled form is therefore not control-equivalent to ORIG (ORIG: then contains
  warning+unlink+try+raise; else is `time.sleep` + loop back).
Judgment: **then-block collection for the timeout-if stops after the first block (the
following try-region was consumed first, bottom-up), and the loop back-edge is absorbed
into the wrong branch.**

### 2.5 FileIO.write — pure-shift family
hunk already 0 (R68 pushed first_diff 38 -> 38, hunk 3 -> 0), residual Σ|Δ|=1 on the
target yardstick: `LOAD_CONST False; RETURN` vs `JUMP_FORWARD`, `LOAD_CONST None` vs
`LOAD_CONST False` (NORETURN-family tail). No hunk left to remove.
Judgment: candidate only if the single Σ|Δ| point can be eliminated without raising
hunk; otherwise **NONE** (better than an overweight candidate).

## Step 3 · 合成复现

- 文件：`synth/s_polarity.py`（真源）、`synth/s_polarity.pyc`（本机 CPython 3.11.7 编译，magic 同目标）、
  `synth/s_polarity.txt`（名单）。
- 形状刻意复刻 §8 指定的「最优形状」：一个 guard `if A and B and C and not (D or E): S`，
  其后接同层 `if/elif/else`（＝ region 的 merge/continuation）。字节级核对：
  与 `api_base::get_history_df` 2144–2254 逐条同构（`SWAP/COPY` 链式比较、`POP_TOP` 落空清理、
  `JUMP_FORWARD`、5 个 `POP_JUMP_FORWARD_IF_*` 全部指向同一 target）。
- **landed 读数**（`pycdc.decompile_pyc('synth/s_polarity.pyc')`，重编译后与真源逐指令比）：
  `orig=60 / decomp=56`（seq_len −4，缺失/过冲族）、`first_diff=2`、`mismatch=33`。
- **失败签名**（三条，缺一不成立）：
  1. `#27 orig=('POP_JUMP_FORWARD_IF_TRUE', 92)` → `decomp=('POP_JUMP_FORWARD_IF_FALSE', 160)`
     —— **极性反**，与 §8 的 `kline_datetime_list #151` / `get_history_df #419` 同签名；
  2. `time_count -= 1`（真源 S 语句）在产物中**整体丢失**；
  3. region 的 merge 体（`if/elif/else`）被搬进嵌套 `if D or E:` 的 then 臂。
- 反编译产物（landed）：
  ```python
  if not include and frequency == MINUTE and cur_datetime not in (min_datetime, pm_open):
      if pm_open > cur_datetime > am_close or cur_datetime > pm_close:
          if frequency == MINUTE: ... elif ...: ... else: ...
  return out            # <- time_count -= 1 丢失
  ```
- `probe1.py synth/s_polarity.pyc 0 300 guard` 实测：
  `[basic#4] entry@0 then=[40,56,68,66,70,82] else=[] merge=92 cond=28`、
  `[basic#3] entry@70 then=[82] else=[] merge=92`
  —— 与真实靶支 `get_history_df` 的 `entry@2144 then=[2202,2218,2230,2228,2232,2244] else=[] merge=2254 cond=2190`
  **结构完全同形**（合成见证咬合 landed 失败）。

## Step 4 · 候选与 A/B

**候选：NONE（本轮不产出 spec）**，因此无 A/B、无 `specs/cand_r69_*.json`。

### Step 4 · 五列读数（无候选 ⇒ 臂 == landed，全部为轮初基线原值）
| 列 | 读数 |
|---|---|
| targets（官方尺，3 支） | klinedata **43/45**、fileio_utils **12/14**、api_base **24/25**，合计 **79/84**，缺陷 **8**（函数级 5+2+1） |
| battery（45 项公开电池） | **182/200**，缺陷函数 **18**，worse-than-landed **0**，ERR **0** |
| canary（4 金丝雀） | `4d41187e356544e0` 143/143、`af77224b34b203c4` 10/10、`e711b8ea86d49a15` 26/26、`9d09af09249da177` 25/25（逐字节不变） |
| strict（`sstrict67.py build_landed targets.txt`） | **97/105**，缺陷 **8**，missing **0**，extra **0** |
| synth（`synth/s_polarity.pyc`） | orig **60** / decomp **56**，first_diff **2**，mismatch **33**，失败签名见 Step 3 |

无臂 ⇒ 无新增 `target_diff`、无 ERR、无不可反编译；锚点 `count==1` 一项本轮不适用（未提交 spec）。


理由按判据逐条给出（三要素已在 Step 2 写实测，此处写「为什么不能落成 spec」）：

1. **§8 指定的最优形状（kline_datetime_list #151 + get_history_df #419，2 支）——根因可写，改法过重。**
   根因（Step 2.2 实测）：`region_analyzer._identify_conditional_regions` 的 and 链游走
   （`[R68-b2 and-chain]` L16841 起，断链判据 L16896 `_main_ft_last.argval != _main_merge_offset -> break`
   + L16879 `'IF_TRUE' in opname -> break`）在 guard 的**尾部 `or` 子链**处必然断链——
   子链首块 `40` 的条件跳目标是链内续块 `68`（链式比较的落空清理）而非 region merge，
   且子链成员以 `IF_TRUE -> merge`（＝「真则退出」）收尾。于是 `40..70` 落进 `then_blocks`，
   generator 发射嵌套 `if D or E:` 时把该跳转目标（＝region merge）当作 then 臂体，merge 被内联、
   S 被挤出/丢弃，`IF_TRUE` 也随之翻成 `IF_FALSE`。
   **要修就修成 `if A and B and C and not (D or E): S`**：需要
   (a) 分析端把 `40..70` 折进条件并把 `condition_block` 重定向到链末块 `70`、`chain_blocks` 并入；
   (b) `IfRegion.inline_boolop_chains` 的 value 格式从 `{blocks, op, negate}` 单层
   **扩成可嵌套的 `and` 前缀 + `not(or)` 后缀**——该 dict 至少有 6 个读点
   （generator L12664 / L15797 / L16244 / L16519 / L16685 / L17797，analyzer L19688 / L19973），
   且 L17839 现有的 `op=='and'` 逐块取反规则对本形给出
   `… and pm_open > cur and not (cur > am_close) and not (cur > pm_close)`（De Morgan 不等价，已推演证伪）；
   (c) `then`/`else`/`merge` 重算并保证不破「每块每层唯一归属」。
   按 §2「每条新规则须写齐三要素、禁止过重」——这是一次**跨 6 个读点的格式扩展 + 区域重归约**，
   属于过重候选；在本轮轮次预算内无法完成 45 项电池 + 金丝雀 + 3 靶支 + 严格尺的完整回验。
   按 §3 任何一项不过即回退，宁可 NONE。
2. **`get_multiminute_his_data`（klinedata 缺陷 1）**：根因 = `_build_basic_if_region` 选错 merge
   （取 `2710` 而非真汇合 `2758`），导致 `then` 内含一个偏移**大于自身 merge** 的块（结构不可能）。
   merge 选取在含多重提前 `return` 的巨型区域上是 post-dominator 难题，改动面覆盖全部函数，无窄判据可守 → NONE。
3. **`FileLock.acquire`（fileio_utils 缺陷 1，缺语句族 96/93(3)）**：根因 = timeout-if 的 then 只收到首块
   `[214]`（其后的 unlink/try/`raise` 被下方 TryRegion 先行吃掉，自底向上归约把它们挂到 handler 层），
   且 else 误吸循环回边（`EXTENDED_ARG; JUMP_BACKWARD` 107/108）。修它要动 try/if 层次归属顺序，
   直接命中 §2 禁止的跨区域归属调整，回归面是全部 try 结构 → NONE。
4. **`FileIO.write`（fileio_utils 缺陷 2）**：按 §8 硬规则——hunk 已是 **0**，第二支要求「归一化 hunk 严格下降」
   已无下降空间；除非消掉残余 `Σ|Δ|=1` 或 `seq_len` 637/636 之差，否则如实 **NONE**（本轮未消掉）。

## VERDICTS

| 靶支 | 缺陷 | 根因落点 | 候选 |
|---|---|---|---|
| `klinedata` | `get_multiminute_his_data` merge 误取 | `core/cfg/region_analyzer.py` `_build_basic_if_region` / `_chain_merge_candidates` | **NONE**（无窄判据） |
| `klinedata` | `kline_datetime_list` 极性反 #151 | `region_analyzer._identify_conditional_regions` and 链尾断链 → `inline_boolop_chains` 需格式扩展 | **NONE**（过重） |
| `fileio_utils` | `FileLock.acquire` 缺语句 96/93(3) | if/try 层次归属 + 回边吸错 | **NONE**（过重） |
| `fileio_utils` | `FileIO.write` 637/636 Σ\|Δ\|=1 | NORETURN 尾巴 | **NONE**（§8 硬规则：hunk 已 0，无下降空间） |
| `api_base` | `get_history_df` 极性反 #419 | 同 `kline_datetime_list`，共享同一根因 | **NONE**（过重） |

合成见证（`synth/s_polarity.*`）：**landed 失败**（orig 60 / decomp 56、`IF_TRUE→IF_FALSE` 极性反、S 丢失）——
已具备 §3.5 的前半；因无候选，无「我的臂通过」一侧。

## 对 BRIEF 的更正

- **Step 0 无更正**：targets.md 官方尺 79/84、金丝雀 4 sha、45 项电池 182/200、严格尺 97/105
  全部与预读数**逐字段相符**，以实测为准，无需更正。
- §5 仪器缺陷全部复现确认：`nhunks.py` 同名 code object AssertionError、`nested_diff.py` 不归一
  `EXTENDED_ARG`（klinedata `/kline_datetime_list#57` 7 hunk 中 3 个是该伪影）。
- §8「两支同签名」**成立且已在合成件上复现**：`synth/s_polarity` 的 `#27`
  `POP_JUMP_FORWARD_IF_TRUE 92` → `POP_JUMP_FORWARD_IF_FALSE 160`，与 #151/#419 同签名。
- **新增观察（供中心）**：该形状的最小合成复现已证明 `inline_boolop_chains` 单层
  `{blocks, op, negate}` 格式**表达不了** `A and B and C and not (D or E)`；
  要动它必须一次性改 6 个读点（见 Step 4.1(b)）。建议下一轮按「格式扩展 + 6 点同改」整体立项，
  而不是按单点补丁分轮推进。
- 中心级建议（§1 允许写进 FACTS、不做成 spec）：`region_analyzer` 与 `region_ast_generator` 的
  区域/条件数据契约（`inline_boolop_chains`）目前是隐式单层结构，缺一个集中式读写入口，
  是本轮 NONE 的直接原因。

