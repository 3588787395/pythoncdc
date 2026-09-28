# R74 · fix1 FACTS — abs2（orphan-child 发射）+ abs1 合臂 absj

工作区 `D:/Temp/opencode/r74gate/fix1`；基线 HEAD `6bb9716a`（R73 落地）。
generator `33e22ee451148af8` / analyzer `b9dcc727ea5918ea` / comprehension `b432a35580989852`。
全程 repo 只读：`git -C F:/Downloads/pythoncdc-main status --porcelain core` 为空；`land74` 只 dry-run。
每条命令 <300s；列表 LF 无 BOM；h62 跑前删旧 jsonl。

**结论（先给）**：absj = abs1 + abs2 全项通过，mandate 达成
`IQCommon/data/local_finance.pyc 20/21 → 21/21 success`，klinedata 尾语句恢复，
官方 REGRESSION=0、mandated 零新失败单元、strict NEW=0、battery worse=0、金丝雀 4/4。

---

## 1. 两臂定义与 spec

| 臂 | 文件 | edits | +行 | 产物镜像 |
|---|---|---|---|---|
| `abs1`（R73 复用，原样） | `core/cfg/region_analyzer.py` | 1 | +34 | `center/mirr_abs1`（1778913 → 1781244 B，BOM=False） |
| `abs2`（本轮新增） | `core/cfg/region_ast_generator.py` | 1 | +31 | `center/mirr_abs2`（3214913 → 3217588 B，BOM=True） |
| `absj`（合臂） | 上两个 | 1 + 1 | +34 / +31 | `center/mirr_absj` |

- `specs/abs1.json` SHA256 `c592ebb2b934e275…`（2674 B），与 `r73gate/fix2/specs/abs1_nested_same_exit.json` 逐字节相同；锚点在当前 HEAD 恰 1 次（`mbuild74` 断言过）。
- `specs/abs2_orphan_child_emit.json` SHA256 `4ecf1d93b1148f1b…`（4970 B），锚点恰 1 次。
- `specs/absj.json`（分文件列两条 edit，7799 B）= 两 spec 合并，`mbuild74.py absj specs/abs1.json specs/abs2_orphan_child_emit.json`。

### abs2 判据（同层结构身份，含三要素注释）

在 `generate()` 的孤儿块释放循环里，把原本的 `if _has_top_level_ancestor: continue`
放宽为 `_has_top_level_ancestor and _covered_by_parent`：

- **识别条件**：本块所属子区域带顶级祖先（原豁免），**且**该子区域块集与**它父区域**的
  发射集合（`blocks / then_blocks / else_blocks / body_blocks / elif_conditions /
  cond_blocks / orelse_blocks / finalbody_blocks / handler_blocks / try_blocks`）
  有交集 —— 只读「这一对父子」各自的块集。
- **归约方式**：有交集 = 父区域沿既有子区域发射路径必然走到它，逐字节保持原豁免；
  无交集 = 父区域的 `blocks/then_blocks` 遍历永远走不到它（共享尾 region 合并后 child
  落到覆盖之外），改走**既有**孤儿块路径：释放出 `block_to_region`，按块偏移升序补发射。
- **AST 映射**：被释放的块生成一个 BASIC 区域，追加到顶级区域列表末尾，按 entry 偏移序
  发射为它原本的语句序列 —— 语句只增不减。

无函数名 / 无文件名 / 无偏移阈值 / 无标识符名字白名单 / 无新 `self` 状态 /
不用跨层 `region.entry in r.blocks`（用的是 block-id 集合交集）。

**跨层模式门禁**（`\w+\.entry in \w+\.blocks`，raw / code-only）：

| 文件 | landed raw/code | abs1 | abs2 | absj |
|---|---|---|---|---|
| `core/cfg/region_ast_generator.py` | 9 / 7 | 9 / 7 | 9 / 7 | 9 / 7 |
| `core/cfg/region_analyzer.py` | 3 / 3 | 3 / 3 | 3 / 3 | 3 / 3 |
| `core/cfg/comprehension_generator.py` | 0 / 0 | 0 / 0 | 0 / 0 | 0 / 0 |

→ 零新增。原始输出：`dump/patcounts74.txt`（见 §7）。

---

## 2. a. 基线复现（abs1 读数可复现）

`mbuild74.py abs1 specs/abs1.json` → 锚点/BOM/CRLF/行数断言全过。
官方 35 靶 `h62 run --arm=abs1`（3 分片）→ `dump/abs1_s0..s2.jsonl`：

| 臂 | matched/total | Σ\|Δ\| | Σjump_diffs | 失配函数 |
|---|---|---|---|---|
| landed | 1342 / 1371 | 186 | 130 | 29 |
| abs1 | 1343 / 1371 | 185 | 123 | 28 |
| abs2 | 1342 / 1371 | 187 | 130 | 29 |
| **absj** | **1343 / 1371** | **175** | **123** | **28** |

mandated 35 靶（`mand74.py`，4 分片，35/35 记录，`dump/md_abs1_summary.txt`）：

- landed `1512/1589` → abs1 `1516/1589`（+4）；TURN-GREEN 仅 `local_finance`；
  `finance 29/32 → 31/32`；`trade_live_broker 114 → 115`；零新失败单元。

R73 的 +4 已复现。

---

## 3. b. 丢语句现场（klinedata）

`rd74.py base|abs1 IQCommon/api/klinedata.pyc get_multiminute_his_data`
→ `dump/rd_base_klmulti.txt` / `dump/rd_abs1_klmulti.txt`；探针 `probe_gen74.py` → `dump/pg_base.txt` / `dump/pg_abs1.txt`。

- **41 blocks 不变**；base 35 regions / **2 个顶级区域**，abs1 33 regions / **1 个顶级区域**。
- base：`IfRegion@0`（children=`[Region@0]`）+ `IfRegion@68`（children=`[Region@68, IfRegion@82,
  IfRegion@718, Region@2710, Region@2758]`）→ `Region@2710` 的祖先是**顶级** `IfRegion@68`，
  释放循环把它判成孤儿 BASIC，`block_to_region[2710]=None`，**照常发射**（base 无丢失）。
- abs1：`_is_nested_if_else_pattern` same-target 豁免把 boolop 双块合并，
  只剩 `IfRegion@0`，children=`[BoolOpRegion@0, IfRegion@82, IfRegion@718, Region@2710, Region@2758]`，
  而 `IfRegion@0.blocks` 里**没有 2710**（有 2708、2758）→ 释放循环读到
  `_has_top_level_ancestor=True` 就 `continue` → 永不发射。
- 覆盖检查：base 未覆盖 offset 恰 `[2710]`；abs1 未覆盖 offset 恰 `[2710]`。
- `dis` 证据：原 pyc `66/80 POP_JUMP_FORWARD_IF_FALSE to 2710`（顶层 `if A and B` 的假臂
  直指尾块），`822`/`2708 JUMP_FORWARD to 2758`（if 体出口跨过 2710 直达共享 return）。
  尾块 2710 = `get_kline_by_count_new(...)` 那条赋值语句。
- **对照原文件**：`dump/diff_klinedata_landed_vs_abs1.txt` —— abs1 只比 landed 少
  `his_data_dict = get_kline_by_count_new(...)` 这一条（另加 `kline_datetime_list` 的
  `if not include` 合并，abs1 既有成因）。

官方读数（`get_multiminute_his_data = [orig, decomp, jump_diffs, true_diffs]`）：

| 臂 | 官方 | strict `seq_len` |
|---|---|---|
| landed | [479, **478**, 3, 16] | orig=481 / decomp=**482** |
| abs1 | [479, **467**, 3, 16]（−11，语句丢） | orig=481 / decomp=**471** |
| abs2 | [479, **478**, 3, 16] | — |
| **absj** | [479, **478**, 3, 16] | orig=481 / decomp=**482** |

`get_kline_by_count_new` load 数：landed `2`、absj `2`（`dump/kl_tailcheck.txt`）。
mandated `pyc_verify single` 四臂均 `61/64`（该条语句 mandated 尺不计，靠官方尺 + strict 抓）。

---

## 4. c/d. abs2 单臂 + 合臂

- `mbuild74.py abs2 specs/abs2_orphan_child_emit.json` → 断言全过。
- 单臂官方 35 靶：唯一差异是 `fly/data/quote :: get_real_from_zeromq`
  `[703,700,1,551] → [703,699,1,550]`；klinedata `[479,478]` 保住，trade_live_broker 不动。
- `mbuild74.py absj specs/abs1.json specs/abs2_*.json` → 两 edit 各恰 1 次。
- `land74.py land --spec=… --mirror=mirr_absj`（两 spec，**dry-run**）：
  `replay == measured mirror bytes: OK`（analyzer 1781244 B / generator 3217588 B）；
  对 `mirr_abs1` / `mirr_abs2` 同样 OK；未传 `--apply`，repo core 无改动。

### quote 的 ±1 说明（诚实记录）

`get_real_from_zeromq` 在 landed 被反成「两个分支各自 `return None` + 末尾隐式 `return None`」，
丢了原 pyc 的共享尾 `return None, flag`；abs2 把共享尾整条发射出来
（`dis` 原 pyc：`1024 LOAD None / 1026 LOAD flag / 1028 BUILD_TUPLE / 1030 RETURN_VALUE`）。
因此 decomp 700 → 699、`true_diffs` 551 → **550**（更接近原），但 |Δ| 3 → 4（+1）。
该 +1 被 abs1 的收益吸收：**absj Σ|Δ| = 175 ≤ 185**（见 §7）。

---

## 5. e. 验证闭环（absj 全项）

### e1 官方（35 靶 / 41 靶两口径）

`dump/absj_s0..s2.jsonl` → `dump/absj_merged.jsonl`；41 靶 `dump/absj41.jsonl`。

| 口径 | 臂 | matched/total | Σ\|Δ\| | Σjump | 失配 |
|---|---|---|---|---|---|
| 35 靶 | landed | 1342/1371 | 186 | 130 | 29 |
| 35 靶 | abs1 | 1343/1371 | 185 | 123 | 28 |
| 35 靶 | **absj** | **1343/1371** | **175** | **123** | **28** |
| 41 靶 | landed | 1493/1522 | 186 | 130 | 29 |
| 41 靶 | **absj** | **1494/1522** | **175** | **123** | **28** |

门槛：Σ\|Δ\| ≤ 185 ✅、Σjump ≤ 123 ✅、失配 ≤ 28 ✅、逐项 ≥ landed 且 ≥ abs1 ✅。

`h62 ab landed↔absj`（`dump/ab_landed_absj41.txt`）：

```
TALLY SAME=35 IMPROVED=1 REGRESSION=0 MOVED=5 ERR=0   (files fully matched 27→27)
IMPROVED  trade_live_broker 111/119 -> 112/119   |d|=83 -> 71
MOVED     api_base get_history_df  jump_diffs 11 -> 6
MOVED     quote get_real_from_zeromq [703,700,1,551] -> [703,699,1,550]
MOVED     klinedata / finance / local_finance（失配集合不变、产品已变）
```

`h62 ab abs1↔absj`：`SAME=33 MOVED=2 REGRESSION=0`，MOVED = klinedata 尾语句回来 + quote 共享尾回来。

### e2 mandated（35 靶，`mand74.py` 4 分片，`dump/md_absj_s0..s3.jsonl` → `dump/md_absj_summary.txt`）

- **landed `1512/1589` → absj `1516/1589`（+4）**；402 口径按 R73 基数 `6540 → 6544`（`G3v_pycverify_r73.json` 基数 6540/6617，367 success 文件未动：官方 REGRESSION=0 + 金丝雀 4/4 + strict NEW=0 + battery worse=0）。
- **TURN-GREEN：`IQCommon/data/local_finance.pyc 20/21 → 21/21 success`** ✅ mandate
- `IQCommon/data/finance.pyc 29/32 → 31/32` ✅（≥31）
- `IQEngine/.../trade_live_broker.pyc 114/128 → 115/128` ✅（≥115）
- `fly/data/quotation.pyc 152/153` 维持 ✅
- **零新失败单元：0** ✅
- 其余 31 支 units 全部与 landed 相同（`md_absj_summary.txt` 逐支比对）。

### e3 klinedata 靶点

见 §3 表：`seq_len` 471 → **482**（= landed），`get_kline_by_count_new` load 数 2 = landed，
尾语句 `his_data_dict = get_kline_by_count_new(...)` 在 `build_absj` 产品里存在。
`diff landed vs absj` 只剩 abs1 既有 `kline_datetime_list` 两处 `if not include` 合并（26 行 diff）。

### e4 金丝雀 4 支

`dump/canary_landed.jsonl` / `dump/canary_absj.jsonl`：

| 产品 | pin | landed | absj |
|---|---|---|---|
| `fly/data/quotation.pyc` | `3eb76e512df9ab1e` | 同 | 同 ✅ |
| `fly/common/market_time.pyc` | `af77224b34b203c4` | 同 | 同 ✅ |
| `IQCommon/util/datetime_func.pyc` | `e711b8ea86d49a15` | 同 | 同 ✅ |
| `IQData/utils/datetime_func.pyc` | `9d09af09249da177` | 同 | 同 ✅ |

`MISS = 0/4`；quotation 官方 143/143、mandated 152/153 维持。

### e5 battery

`closeout69.py battery landed absj` → **`candidate columns worse-than-landed on 0 repro(s)`**
（82 支 repro 全量；`round69_diag1/r69d1_gma.pyc` 顺带 1/2 → 2/2）。原文 `dump/battery_absj.txt`（stdout 见 §7）。

### e6 strict

`sstrict67.py build_landed dump/tgt41.txt` → `dump/strict_landed41.json`：
**ok 1643/1718，defects 75**（与基线 75 一致）。
`sstrict67.py build_absj dump/tgt41.txt` → `dump/strict_absj41.json`：
**ok 1647/1718，defects 71 ≤ 75**，**NEW = 0**，CLEARED = 4：

- `finance :: get_financial_and_growth_factors` (target_diff)
- `finance :: get_financial_statements_pit_mode` (target_diff)
- `local_finance :: get_local_financial_factors` (target_diff)
- `trade_live_broker :: get_max_amount` (seq_len)

### e7 synth

| 文件 | 落地 landed | abs1 | abs2 | absj |
|---|---|---|---|---|
| `abs_a01_shared_and_else.pyc`（R73 复用） | **failure 3/4** | success 4/4 | failure 3/4 | **success 4/4** ✅ |
| `abs_a02_true_nested.pyc`（R73 复用，负例） | sha16 `969e761c46399149` | 同 | 同 | 同 ✅ 逐字节相同 |
| `abs_a03_tail_after_topif.pyc`（本轮新增） | success 2/2 | success 2/2 | success 2/2 | **success 2/2**，尾语句 2/2 在场 ✅ |

`abs_a03` = 「合并后 child 含尾语句」最小复现：直接取见证者
`IQCommon/api/klinedata.pyc::get_multiminute_his_data`（74 行，源即落地产品形态），
判据 = 函数尾 `his_data_dict = get_kline_by_count_new(...)` 在四臂产物中都不丢，absj 必在场。

**如实记录的限制**：把落地产品源重新 `py_compile` 得到的 CFG **复现不了原 pyc 的块序**——
原 pyc 里 if 体出口 `822/2708` 跳到**位于尾块之后**的共享 return（`2758`），而重编译产物把
return 放在尾块**之前**（`2720 < 2724`），于是尾块只成为「新的顶级区域」而不是「顶级
IfRegion 的未覆盖 child」。因此**丢语句本身只在原 pyc 上可观测**；已试 5 个源级候选
（verbatim / trim / quote 共享尾 / boolop+for / nested-else）产物四臂全等。
该限制不影响 a03 的判据（absj 下语句不丢），但**「abs1 会丢」的负向证据以原 pyc 为准**：
abs1 官方 479→467、strict seq_len 471，absj 回到 479→478 / 482。
synth 脚本：`synth/mk_a03.py`、`synth/try_a03.py`、`synth/try_a03b.py`、`synth/try_a03c.py`、`run_synth74.py`。

---

## 6. ADR-1 自判

- **WORSE = 0**：官方 REGRESSION=0（35/41 两口径）、mandated 零新失败单元、
  strict NEW=0、battery worse=0、金丝雀 4/4、跨层模式零新增；
  语句只增不减（klinedata +11 指令恢复、quote +1 条共享尾恢复、trade_live_broker get_max_amount 清掉）。
- **位移族**：absj 对 landed 的 hunk = abs1 的 hunk ∪ abs2 的 quote 尾语句；
  `Σ|Δ| 186 → 175`（不升，且下降 11），`Σjump 130 → 123`。
- **abs1 收益不回吐**：local_finance 21/21 ✅、finance 31/32 ✅、trade_live_broker 115/128 ✅、+4 单元全保。
- 未改 repo、未手改 `*OK.py`、未跑 402 全量、无 `--apply`。

---

## 7. 与 fix2 / fix3 的重叠面

absj 会改写 6 支产品（官方 MOVED/IMPROVED）：

| 产品 | absj 变化 | 与 fix2 重叠 | 与 fix3 重叠 |
|---|---|---|---|
| `fly/data/quote.pyc` | `get_real_from_zeromq` 共享尾恢复 | ✅ `check_frequency` / `run_tick_socket` / `load_get_price` | ✅ `run_tick_socket`（fix3 标注与 fix2 重叠） |
| `IQEngine/.../trade_live_broker.pyc` | `get_max_amount` 缺陷清掉（+1 单元） | ✅ `etf_basket_order` / `_sync_worker` | — |
| `IQCommon/data/finance.pyc` | 2 条 target_diff 清掉 | — | ✅ `finance :: get_fields` |
| `IQCommon/data/local_finance.pyc` | 转 success（mandate） | — | — |
| `IQCommon/api/klinedata.pyc` | 尾语句恢复 + `kline_datetime_list` 合并 | — | — |
| `IQData/api/api_base.pyc` | `get_history_df` jump 11 → 6 | — | — |

`trade_info_utils.pyc`（fix2/fix3 都有靶）absj 官方 **SAME 40/40**，本臂不动它 ——
fix2 提的「trade_info_utils 2 单元属 F-ABSORB，可能需与 fix1 合臂」仍在中心待办：
本臂只清了 `trade_live_broker.get_max_amount`，`trade_info_utils::trade_operation` 等未动。

---

## 8. 交付清单

- `FACTS.md`（本文件）
- `specs/abs1.json`（复用，字节未改）、`specs/abs2_orphan_child_emit.json`、`specs/absj.json`
- `synth/`：`abs_a01_shared_and_else.*`、`abs_a02_true_nested.*`（R73 复用）、
  `abs_a03_tail_after_topif.*` + `mk_a03.py` / `try_a03*.py` / `run_synth74.py`
- `dump/`：
  - 官方：`tgt35.txt`、`tgt41.txt`、`landed_s0..s2.jsonl`、`abs1_s0..s2.jsonl`、
    `abs2_s0..s2.jsonl`、`absj_s0..s2.jsonl` + `*_merged.jsonl`、
    `landed41.jsonl`、`absj41.jsonl`、`ab_landed_absj41.txt`
  - mandated：`md_abs1_s0..s3.jsonl`、`md_absj_s0..s3.jsonl`、`md_abs1_summary.txt`、`md_absj_summary.txt`
  - strict：`strict_landed41.json`、`strict_absj41.json`
  - 金丝雀：`canary.txt`、`canary_landed.jsonl`、`canary_absj.jsonl`
  - 诊断：`rd_base_klmulti.txt`、`rd_abs1_klmulti.txt`、`pg_base.txt`、`pg_abs1.txt`、
    `diff_klinedata_landed_vs_abs1.txt`、`klmulti.txt`、`kl_abs1.jsonl`、`kl_abs2.jsonl`、
    `kl_tailcheck.txt`、`patcounts74.txt`、`battery_absj.txt`、`crosstab74.txt`
- 脚本：`mbuild74.py`、`mand74.py`、`sum74.py`、`run_synth74.py`、`probe_gen74.py`、`rd74.py`、
  `sstrict67.py`（复用）、`closeout69.py`（复用）、`land74.py`（复用）

**复测建议（中心）**：`mbuild74.py absj specs/abs1.json specs/abs2_orphan_child_emit.json`
→ `h62 run --arm=absj --list=<35 靶>` → `mand74.py <35 靶> absj` →
`sstrict67.py build_absj <41 靶>` → `closeout69.py battery landed absj` →
`land74.py land --spec=specs/absj.json`（需先拆成两条单 file spec）→ 金丝雀 4 sha16。
