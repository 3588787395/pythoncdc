# FACTS.md — R73 fix2（F-ABSORB 主体）端到端读数

- 基线 HEAD `8d136040`（R72），generator sha `6203253987adedcf` / analyzer `8ca47f7d6b9244cf` / comprehension `b432a35580989852`（原始记录见 `dump/` 与 `center/G3v_pycverify_r72.json`）。
- 工作区 `D:/Temp/opencode/r73gate/fix2`；repo `F:/Downloads/pythoncdc-main` 全程只读（未改、未提交、未 push、未跑 402 全量）。
- 臂：`abs1`（单候选）、`absm`（合并臂＝本件仅此 1 条 edit）。镜像 `center/mirr_abs1`、`center/mirr_absm`，产品 `center/build_abs1`、`center/build_absm`，基线 `center/build_landed`。
- 靶支 41 文件清单：`dump/abs1_targets.txt`（source = 41 failure 支 / 88 单元）。

---

## 0. TL;DR

| 项 | 结果 |
|---|---|
| 用户裁定的「嵌套 try-except 归约」根因假设 | **主体证伪**（见 §1），try 只是「共享尾吸收」的一种载体形态 |
| 真根因 | `_is_nested_if_else_pattern` 把**全部成员同跳一块**的 `if A and B: X else: Y` 误判成嵌套 if-else → boolop 链被弃 → 共享 else 被内层吞 |
| mandated（41 支 pyc_verify single） | 1671/1759 = 95.00% → **1675/1759 = 95.22%（+4）**，全绿文件 0 → **1**（`IQCommon/data/local_finance.pyc` 20/21→**21/21 failure→success**） |
| 官方口径（h62 official，41 支） | 1493/1522 = 98.09% → **1494/1522 = 98.16%**，`Σ\|Δ\|` **186→185**，`Σjump_diffs` **130→123**，失配函数 29→28 |
| a) 官方 ab vs landed | `TALLY SAME=36 IMPROVED=1 REGRESSION=0 MOVED=4 ERR=0`，fully matched 33/33 |
| c) 金丝雀 | landed / abs1 / absm 四支 sha16 全部 == pin（`quotation 3eb76e512df9ab1e`、`market_time af77224b34b203c4`、`IQCommon datetime_func e711b8ea86d49a15`、`IQData datetime_func 9d09af09249da177`）；`quotation` 官方 143/143 两臂不变 |
| d) battery（82 repros） | **candidate worse-than-landed = 0**；`round69_diag1/r69d1_gma.pyc` 1/2 → **2/2 改善** |
| e) strict（75 支 strict777） | ok 1639/1718 → **1643/1718**，defects **79 → 75**；**新增缺陷 0**，修复 4，**恶化 1**（见 §5） |
| synth 复现 | `abs_a01` landed **failure 3/4 → abs1 success 4/4**；`abs_a02`（真嵌套负例）两臂 sha 完全相同 `969e761c46399149` |
| 未过项 | klinedata `get_multiminute_his_data` 产品**丢 1 条尾语句（-11 指令）**，详见 §5，**交中心裁定** |

---

## 1. 用户裁定假设的判决：try-except 归约 —— **主体证伪**

裁定内容（最高优先级）：头部 cf 根因 = 嵌套 try-except，R71/R72 否定结论作废；探针优先打 try/except 归约路径。

实测（`dump/tfirst_*.txt`，原 pyc ↔ 已落地产品的**首分歧点**定位 + 原 pyc 异常表归属）：

| 批 run | 单元 | 首分歧在原 pyc 异常表内 | 在外 | 无分歧 |
|---|---|---|---|---|
| `tfirst_finance` | 3 | 1 | 2 | 0 |
| `tfirst_t1` | 5 | 2 | 3 | 0 |
| `tfirst_t2` | 12 | 1 | 11 | 0 |
| `tfirst_t3` | 4 | 3 | 1 | 0 |
| `tfirst_t4` | 14 | 0 | 14 | 0 |
| **合计** | **38** | **7（18.4%）** | **31** | **0** |

- 首分歧单元按异常表条目数分三类计数：`IN-TRY=7`、`OUT=16`、`OUT-noET（nET=0，该函数根本没有异常表）=15（39.5%）`。
- **异常表本身没变**：`dump/d4_ti.txt` 里 `trade_info_utils` 4 个单元逐对打印 `A etable:` / `B etable:`，**逐字节相同**（例如 `trade_operation` 18 条、`get_trade_status` 11 条）。全语料 `F-EXCTABLE` 家族仅 **1 单元**（fam72）。
- 结论：**首分歧点大多不在 try 块内，且异常表未被改动** ⇒ 「try/except 归约 → 头部 cf 分歧」不是头部主根因，**本件按事实证伪该主路径**。
- 但 try 不是无关的：try 段只是**共享尾（shared exit / shared else）被吸收**的载体形态之一 —— `finance.get_fields` 即 `IN-TRY k=18`（`dump/tfirst_finance.txt`），其结构与本件修的形同源。**该 try 形本件未修**，列为遗留（§6）。

---

## 2. 根因表（唯一、可判据）

| 层 | 事实 |
|---|---|
| 症状 | 头部 cf 分歧：共享的 else 臂丢失，退化成两层嵌套 if，内层把共享 else 吞掉；产物字节与原 pyc 不等 |
| 判据行 | `core/cfg/region_analyzer.py:26573 _is_nested_if_else_pattern`；调用点 `:26536`；下游 `:25066 _detect_boolop_conditional_chain`、`:23303 _identify_boolop_regions` |
| 机理 | 链成员全部条件跳转指向**同一块**（共享失败出口，语义 = 真 `if A and B: X else: Y`）时，`_is_nested_if_else_pattern` 返回 True → `:26536 return None` → boolop 链被整体放弃 |
| 产物 | 错发嵌套 if：finance `get_financial_and_growth_factors` 链 `[(6,'or'),(10,'or')]` 两成员同跳块 114 → 产物 `ft_has_store & jt_has_store`，原 pyc 为 `or`；块 8 `A→114 / B→118`（`dump/reg_fin_growth.txt`） |
| 同层不可分证据 | `dump/pf_finance.json` 与 `dump/pf_klinedata.json` 显示 klinedata#14 与 finance#6 的同层特征完全一致（`E_in_body=False`、`E_succ_in_body=True`）⇒ 任一「同层可达性」判据都无法在只保收益的前提下把 klinedata 的形与 finance 的形分开（已试 3 种，见 §5） |
| 区域树实证 | `dump/rd2_base.txt` vs `dump/rd2_ns.txt`：base 产出两个顶层 `IfRegion@0`/`IfRegion@68`，abs1 合并为单 `IfRegion@0`+`BoolOpRegion@0`，`Region@2710` 变 child 但不在 `blocks/then_blocks` → 生成器跳过 → 语句丢失（§5 的直接成因） |

### 修法（单 edit）
- spec `specs/abs1_nested_same_exit.json`：锚点 = `_is_nested_if_else_pattern` 定义行 + `last_block, _ = chain[-1]`（LF 归一后**恰 1 次**，行尾/BOM/行数断言全过），替换体含同层三要素注释 + same-target 豁免分支，**+34 行**、BOM=False、CRLF。
- 层次身份判据：不引入函数名/文件名/偏移/阈值启发、不加名字白名单、不加 self 新状态、不用跨层 `region.entry in r.blocks` 模式。
- 负例保护：`specs/abs1_with_cleanup_break.json`、`abs1_with_ext_pred.json`、`abs2_r57b_jump_target.json`、`absm_abs1_abs2.json` 曾致官方 38/40 回归，按 ADR-1 **判为回归件、不可复用**；本件另起文件名。

---

## 3. 镜像臂 a–e 逐项读数

### a) 构建
| 命令 | 结果 |
|---|---|
| `center/mbuild73.py abs1 specs/abs1_nested_same_exit.json` | `patched core/cfg/region_analyzer.py edits=1 lines=+34 bytes 1769617 -> 1771948 BOM=False` |
| `center/mbuild73.py absm specs/abs1_nested_same_exit.json` | 同上（合并臂＝单 edit） |

ALLOWED = `region_ast_generator / region_analyzer / comprehension_generator`，锚点各恰 1 次，均断言通过。

### b) 官方靶支读数（`center/h62.py run --arm=<arm> --list=abs1_targets.txt`，3 shard 并行）
原始：`dump/landed_s0..2.jsonl`、`dump/abs1_s0..2.jsonl`、`dump/absm_s0..2.jsonl`，合并 `*_merged.jsonl`；mandated 原始：`dump/md_landed_s0..2.jsonl`、`dump/md_absm_s0..2.jsonl`。

| 指标 | landed | abs1 | absm |
|---|---|---|---|
| mandated `units` | 1671/1759 = 95.00% | **1675/1759 = 95.22%** | 1675/1759 = 95.22% |
| mandated 全绿文件 | 0 | **1**（`IQCommon/data/local_finance.pyc` 20/21→21/21） | 同 |
| 官方 `matched/total` | 1493/1522 = 98.09% | 1494/1522 = 98.16% | 1494/1522 = 98.16% |
| `Σ\|orig-decomp\|` | 186 | **185** | 185 |
| `Σjump_diffs` | 130 | **123** | 123 |
| 失配函数数 | 29 | **28** | 28 |

mandated 逐文件变化（唯一 3 处，**全部向上**）：

```
trade_live_broker.pyc   114/128 -> 115/128   (get_max_amount 转绿)
local_finance.pyc        20/21  ->  21/21    failure -> success
finance.pyc              29/32  ->  31/32    (get_financial_and_growth_factors,
                                              get_financial_statements_pit_mode 转绿)
```

`h62 ab --a=landed_merged --b=absm_merged`：

```
TALLY SAME=36 IMPROVED=1 REGRESSION=0 MOVED=4 ERR=0  (unpaired lists=0)
files fully matched: a=33 b=33
IMPROVED  trade_live_broker.pyc  111/119 -> 112/119
MOVED     klinedata.pyc      get_multiminute_his_data [479,478,3,16] -> [479,467,3,16]   ← §5
MOVED     api_base.pyc       get_history_df           [1742,1742,11,89] -> [1742,1742,6,89]  (改善)
MOVED     finance.pyc / local_finance.pyc   失配集合不变、产品已变（mismatch 记录相同）
```

### c) 金丝雀
`dump/canary_landed.jsonl`、`dump/canary_abs1.jsonl`、`dump/canary_absm.jsonl`：四支 sha16 三臂**全部 == pin**；`quotation.pyc` 官方两臂均 143/143，mandated 两臂均 **152/153**（`dump/md_landed_*.jsonl` / `md_absm_*.jsonl`）。

### d) battery（`center/closeout69.py battery landed <arm>`，82 repros）
```
candidate columns worse-than-landed on 0 repro(s)
round69_diag1/r69d1_gma.pyc   landed 1/2 bad=1 d=+12   ->  absm 2/2 bad=0 d=+0     ← 改善
round68_diag3/r68_big_sinkreturn.pyc  landed 1/3 bad=2 d=-1  ->  absm 1/3 bad=2 d=-12  ← 同形副作用，见 §5
```
（`abs1` 臂同结果：worse-than-landed = 0。）

### e) strict（`center/sstrict67.py build_<arm> <list> <out>`）
原始 `dump/strict_landed.json`、`dump/strict_abs1.json`、`dump/strict_absm.json`。

| | landed | absm |
|---|---|---|
| ok / functions | 1639 / 1718 | **1643 / 1718** |
| defects | 79 | **75** |
| 修复 | — | 4（`finance.get_financial_and_growth_factors`、`finance.get_financial_statements_pit_mode`、`local_finance.get_local_financial_factors`、`trade_live_broker.get_max_amount`） |
| **新增缺陷** | — | **0** |
| 恶化 | — | 1（klinedata `get_multiminute_his_data` `seq_len orig=481 decomp=482 → 471`） |

### synth（`synth/abs_a01_shared_and_else.py`、`synth/abs_a02_true_nested.py`，`synth/run_synth.py`）
| fixture | landed | abs1 | 判据 |
|---|---|---|---|
| `abs_a01` 共享 else 形（真 `if A and B: X else: Y`） | **failure 3/4**（`Different control flow`） | **success 4/4** | **failure→success** |
| `abs_a02` 真嵌套 if-else（负例） | sha `969e761c46399149` success 2/2 | **sha `969e761c46399149`**（逐字节相同） | 负例不动 |

---

## 4. 交付物
- `specs/abs1_nested_same_exit.json`（本件唯一候选 spec；`absm` = 同 spec）
- `synth/abs_a01_shared_and_else.py|.pyc`、`synth/abs_a02_true_nested.py|.pyc`、`synth/run_synth.py`
- `mdscan.py`（对**已构建产品**跑 mandated pyc_verify single 的驱动）
- `dump/`：全部 a–e 原始 jsonl / json（见文末索引）
- 诊断仪（迭代用）：`exp1.py`（runtime 4 模式探针）、`exp1_all.py`（41 文件分批扫描）、`pf.py`、`rd2.py`、`tfirst.py`、`dz.py`、`probe_b.py`

---

## 5. 副作用与风险（交中心裁定，不自行接受）

**唯一负面**：`IQCommon/api/klinedata.pyc → get_multiminute_his_data`

- 产物丢尾语句 `his_data_dict = get_kline_by_count_new(symbols, count, query_date, frequency, fields, fq, include, execution_date, asset, dividends_all)`（`dump/diff_klinedata_landed_vs_absm.txt` 第 1 段），strict `seq_len` **482 → 471（-11 指令）**；该函数在两臂都已失败（official 两臂均记 `[479,…]`），故 official 不计回归，但**确实少发了一条语句**。
- 同函数同时**修正** `kline_datetime_list` 两处 `if not include: if cond: A else: B` → `if not include and cond: A else: B`（`diff` 第 2、3 段），strict `kline_datetime_list` 的 `seq_diff #151` 两臂记录**相同**（未因此变好/变坏）。
- 同形 witness：repro `round68_diag3/r68_big_sinkreturn.pyc` `d=-1 → -12`（matched 不变）。
- 已尝试并放弃的同层判据（都因「与收益形完全同特征」而无法只砍副作用）：`nested_join`（`succ(E) ∩ reachable(body)`）、`nested_nr`（E 不在 body 可达集）—— `dump/exp1_nested_join_*.txt` / `dump/exp1_nested_nr_*.txt` 输出与 `nested_same` **完全相同**，副作用未消。
- 定性：这是**共享尾 region 被合并后生成器跳过 orphan child** 的老 bug 暴露面（§2 区域树实证），不是本 edit 新引入的判据类型；但按 ADR-1「不得以少发射换」，**是否可接受由中心裁定**。若拒，方向 = `region_ast_generator` 侧补 orphan child region 发射（另起 `abs2` 单臂自证，不复用本件）。

**已核无害**：同支 `quotation` 143/143 不变、金丝雀 4/4 不变、battery 0 worse、strict 新增缺陷 0、`get_history_df` jump_diffs 11→6 改善。

---

## 6. 与他批边界

- 本 edit **只落 `core/cfg/region_analyzer.py` 的 `_is_nested_if_else_pattern` 一个点**；不碰 `region_ast_generator`（`pad*` 臂面）、不碰 comprehension。
- 与 `build_pad1..pad6`（fix1）、`build_surg1..2` 臂：**不同判据点**；本臂 strict 新增缺陷 = 0，故在本臂口径下未与其重叠面产生新坏点；重叠支（klinedata / trade_live_broker / quote 等）的具体归属需由中心在合并前用同一 strict 口径复核（`dump/strict_*.json` 可直接比对）。
- 遗留未修（本件刻意不扩面）：
  - try 载体形：`finance.get_fields`（`IN-TRY k=18`），strict 仍 `target_diff #19 JUMP 终点`；
  - `F-OTHER`/`F-PAD` 家族（quote 9+2+1、trade_info_utils 3 F-ABSORB + 2 F-PAD）不在本判据面。

---

## 7. 证据索引（`dump/`）

| 文件 | 内容 |
|---|---|
| `abs1_targets.txt`、`tgt_s0..2.txt` | 41 靶支清单 / mandated 分片 |
| `landed_s0..2.jsonl`、`abs1_s0..2.jsonl`、`absm_s0..2.jsonl`、`*_merged.jsonl` | b) 官方原始读数 |
| `md_landed_s0..2.jsonl`、`md_absm_s0..2.jsonl` | b) mandated 原始读数（对已构建产品） |
| `canary_landed.jsonl`、`canary_abs1.jsonl`、`canary_absm.jsonl` | c) 金丝雀 sha16 |
| `strict_landed.json`、`strict_abs1.json`、`strict_absm.json` | e) strict777 逐函数缺陷 |
| `tfirst_finance.txt`、`tfirst_t1..t4.txt` | §1 首分歧 + 异常表归属（try 判决数据源） |
| `d4_ti.txt`、`d8_qsid.txt`、`dz.py` 输出 | §1 A/B 异常表逐字节对照 |
| `reg_fin_growth.txt`、`pf_finance.json`、`pf_klinedata.json` | §2 根因 / 同层不可分特征 |
| `rd2_base.txt`、`rd2_ns.txt` | §2 区域树差异（orphan child 成因） |
| `diff_klinedata.txt`、`diff_klinedata_landed_vs_absm.txt`、`dis_klmulti.txt`、`dis_kldt.txt` | §5 klinedata 副作用与指令级对照 |
| `exp1_all_nested_same_b0..5.jsonl`、`exp1_nested_join_*`、`exp1_nested_nr_*` | runtime 探针（判据试错） |
