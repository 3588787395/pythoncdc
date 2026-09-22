# Round 39 OUTCOME —— 落地 R39-B：if 臂尾的回边块只有在「本臂私有」（唯一前驱就是臂末块）时才认给这条臂

## 一、结论

* 本轮靶＝Round 38 线 B 留下的子形状 A（重复回边并成一条 ⇒ `continue` 被挪到 if/elif 链外）：
  `IQCommon/strategy/wizard_quant_api.pyc :: wizard_quant_check_limit`（严格尺 `orig=91 decomp=90`，
  官方尺该文件 `49/53`）。线 A（子形状 B，`_if_generate_normal` 的 `_mb_meaningful` 门）本轮未动。
* 根因在**块归属层**（与 R37-A 同层），不在发射侧：臂尾那条纯回边块（见证 @58／语料 @340）被外层
  `LoopRegion` 认领，`_process_if_blocks` 只能把它的 `Continue` 发到整条 if/elif 链之后，重编译时
  它与循环自身的尾回边块（@60／@342）塌缩成同一条 `JUMP_BACKWARD` ⇒ 臂尾终止符少发一条。
* **R39-B**（同层判据，站点 `_process_if_blocks` 末尾，`core/cfg/region_ast_generator.py`）：
  本臂末块 L 直落（终止符非 `JUMP`）到唯一非异常入口后继 T，且 T 只含一条
  `JUMP_BACKWARD→当前循环 header`、T ∉ 本区域块集、T 未被认领、T 不是该循环的
  `back_edge_block(s)`、**且 `T.predecessors == [L]`** ⇒ T 认给本臂，`stmts.append({'type':'Continue'})`
  并标 T 已生成。判据与逐条实测见 `DIAGNOSIS.md` §八–§九。
* 发货效果：靶函数在**两把尺上同时**由不匹配转为匹配（官方尺 `49/53 → 50/53`；严格尺同文件
  `50/56 → 51/56`，`FIXED=[wizard_quant_check_limit]`、`BROKEN=[]`）；全 402 A/B 无任何回退。

## 二、门禁（严格串行）

| 门禁 | 判据 | 实测 |
|---|---|---|
| **G0** 合成电池 `test_repros/round39_arm_tail_continue/`（见证 1 ＋对照 5） | 见证须由 DEFECT 转 CLEAN，对照不得新坏 | head 臂 `r39w_witness DEFECT 1 ctl_two_cont:seq_-1`；r39b 臂 `cases=2 CLEAN=2 DEFECT=0`，无 DEGRADED／无 EXC（`logs/g0_head.txt`、`logs/g0_r39b.txt`） |
| **G1** deficit-1／-2／-3／-4+ 四池 | 靶池改进、余池不得回退 | `5 SAME`／`11 SAME`／`2 SAME`／`IMPROVED 1`（`wizard_quant_api 49/53 → 50/53`）＋`8 SAME`，四池 `REGRESSION=0`（`logs/g123_r39b.txt`） |
| **G2′** 上一轮钉住的电池 `reprobat59` | 逐条 SAME | 59 SAME，fully matched 48→48 |
| **G3** 承重锚点 `anchors107` | 逐条 SAME | 107 SAME，fully matched 77→77 |
| **G4** 全 402 A/B（发货唯一权威） | `REGRESSION=0` 且 `IMPROVED≥1` | `TALLY SAME=401 IMPROVED=1 REGRESSION=0 MOVED=0 ERR=0`，fully matched `a=375 b=375`（`logs/g4_r39b.txt`，逐片 `logs/c39b.s[0-2].jsonl`） |
| **G4′** 唯一变更产物按严格尺逐函数复核（旧产物取 `git show HEAD:`） | `BROKEN=[]` | `50/56 → 51/56`，`FIXED=[<module>.wizard_quant_check_limit]`，其余 5 支（`filter_desicion`、`params_analysis`、`region_mean_desicion`、`get_DMI.calculate_di`、`init_stock_pool_filter`）改前改后逐条相同（`logs/g4prime39.py`、`logs/g4p_out.txt`） |
| **G5** `single` 靶 ＋ 金丝雀 | 官方尺改进、金丝雀逐字节不变 | 靶 `50/53`（缺项表里已无 `wizard_quant_check_limit`）；`site-packages/fly/data/quotationOK.py` sha256[:20] `3f2242e73d7fd56a0096` 改前＝改后 |
| **G6** `batch --index pyc_index.json --all --round 39` | 402/402 复验、索引逐条目差异可解释 | 402 条读完、`failed_pyc 0`；索引差异 404 处＝402 条 `last_tested_round → 39` ＋ **仅 1 支文件的 2 个字段**（`wizard_quant_api.pyc`：`matched_functions 49→50`、`bytecode_match_rate 0.9245283→0.9433962`），无其他状态翻转（`logs/g6_round39.log.txt`、`logs/g6_index_diff.txt`） |
| **G7** `stats` 原样 | 见 §三 | — |

候选 R39-A（缺 `T.predecessors == [L]` 两项）在 G4 被否证：`SAME=383 IMPROVED=0 REGRESSION=16
MOVED=3`、fully matched `375 → 366`，16 处回退全是「产物比原始多一条 `continue`」——靶却确实被它修好，
所以留下的不是废弃结论而是那条区分判据（`DIAGNOSIS.md` §九 表格，`logs/probe39h.py`）。

## 三、G7 `stats` 原样

```
累计统计:
  total_pyc:             402
  verified_pyc:          402
  ok_pyc:                375
  partial_pyc:           27
  failed_pyc:            0
  total_functions:       5746
  matched_functions:     5651
  cumulative_match_rate: 98.35%
```

## 四、落地字节

* 靶轮字节基线：核 sha256[:20] `6b0759b1a0a566a4eb8f`，2 984 567 字节／CRLF 48 421／BOM 在位；
  全部测量在私有镜像 `mirr_head`／`mirr_build_r39b` 上做，G4 之后才写工作区。
* 落地：`land38.py land --spec=spec39b.json --mirror=mirr_build_r39b --apply` ⇒ 重放字节与实测
  镜像逐字节相同；`core/cfg/region_ast_generator.py` 2 984 567 → **2 988 464** 字节，
  CRLF 48 474，UTF-8 BOM 保留，sha256[:20] `cc1254fa30410f2b9954`；本轮 `core/` 仅此一支文件改动，
  插入 53 行、无删除行。产物变更集亦仅 `site-packages/IQCommon/strategy/wizard_quant_apiOK.py` 一支。

## 五、残余与移交下一轮

1. `IQEngine/klinedata.pyc :: get_all_real_daily_kline 188/187`（同簇另一支）：R39-A 曾把它的指令数
   复原（187→188）但 R39-B 依私有性一项不再触发——该站点是**合流型**（前驱 ≥2）。它与子形状 B
   （Round 38 线 A：`_if_generate_normal` 的 `_mb_meaningful` 门、`D:/Temp/r39diagB/ANALYSIS.md` 未采纳）
   同族，需要的是合流点自身的表示不变量，不是臂尾认领。
2. 不得为多修那两支而放宽 `T.predecessors == [L]`：`add_to_strategy_info`（臂尾＝循环
   `back_edge_block`）与 `get_vip_user_info`（臂尾＝本区域 `merge_block`）两支正是被这一项挡住的
   过火形态（§九 表格）。
3. 下一轮 **G2′＝`reprobat59` ＋ 本轮新电池 `test_repros/round39_arm_tail_continue/`**（2 例；head 侧
   见证仍 `DEFECT 1 ctl_two_cont:seq_-1`，是天然的阳性对照）；**G3＝`anchors107`**。
4. 台账未动项照旧：8 条布局等价行、`matcher :: match 713/689`、`clock_worker +6`、
   `decrypt_database_url 295/324`、`events 510/508`、`_init_config 86/84`、`OverNightOrder.__init__ 172/148`、
   `#61` ＋ `r29x_01 <module> 142/138`。

## 六、push 状态

提交 `065633a8` 三次 push 均未成功（前两次 `Failed to connect`，第三次 `Authentication failed`），
本地 `ahead(refs/remotes/origin/main)=1` ⇒ **本轮发货已提交、尚未推送**，下一轮开工先补交
（同 Round 36 情形，`Task 36` 亦曾补交）。
