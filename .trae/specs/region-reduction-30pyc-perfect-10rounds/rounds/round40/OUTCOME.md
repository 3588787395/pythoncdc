# Round 40 结果 —— 落地 R40-A2（merge_block 不汇合两臂时它就不是 merge）

## 一、结论

发货判据（G4 全 402 私有镜像双臂 A/B）：**IMPROVED=3 文件 / REGRESSION=0**，
修复 4 个函数、零劣化，其余 366 行逐条目 SAME。据此落地一条同层判据 R40-A2，
`core/cfg/region_ast_generator.py` 按被测镜像字节精确重放写入。

修复的 4 个函数（G4′ 用落地字节对提交产物重做严格尺复验，`fixed=4 broken=0`）：

| 函数 | 宿主 `.pyc` | 官方尺 per-file |
| --- | --- | --- |
| `fill_kline_data` | `IQCommon/util/common_func.pyc` | `17/21 → 19/21` |
| `fill_kline_data_by_pre` | `IQCommon/util/common_func.pyc` | 同上（同文件两支） |
| `fill_kline_data_by_pre` | `IQData/utils/common_func.pyc` | `22/24 → 23/24` |
| `is_delisting_stock_real` | `fly/data/quote.pyc` | `67/81 → 68/81` |

## 二、门禁台账（严格串行，全部实测）

| 门禁 | 判据 | 实测 |
| --- | --- | --- |
| G0 合成见证（与语料无关，先对**落地字节**跑） | 见证必须在改前失败、改后 CLEAN，负对照不得翻转 | head：`s2_or:seq_-1`、`s7_nested:seq_-1`、`c4_inner_continue:seq_-1` 三支 DEFECT；R40-A／R40-A2 双臂 `0 bad`；`r40c_*` 五支负对照双臂均 CLEAN ⇒ **PASS** |
| G1 deficit-1（5）＋ deficit-2（11）池 | 无回归、靶行改善 | `SAME=7/4`、`IMPROVED=1`（`IQData/utils/common_func.pyc 22/24→23/24`）、`REGRESSION=0` ⇒ **PASS** |
| G2′ `reprobat59` ＋ Round 39 臂尾电池（61 条目） | 承重电池零翻转 | `SAME=60 REGRESSION=0`，唯一 MOVED 行双臂均 `3/3` 全匹配；`fully matched a=50 b=50` ⇒ **PASS** |
| G3 `anchors107` 承重锚点集 | 承重锚点零翻转 | `SAME=105 REGRESSION=0`，2 行 MOVED（同文件与其 `_dec` 孪生）双臂均全匹配；`fully matched a=77 b=77` ⇒ **PASS** |
| **G4 全 402 双臂 A/B（唯一发货判据）** | 只允许 IMPROVED／count-neutral MOVED | `SAME=366 IMPROVED=3 REGRESSION=0 MOVED=33 ERR=0`；Σmatched `5651 → 5655`（内部一致性：head 侧 Σ=5651 与 G6 前索引同值）；`fully matched a=375 b=375`；33 行 MOVED 逐行核对 `gained=[] lost=[]` 且 per-row 计数不变，唯一指令数变化是 `real_quote.pyc::get_cache_l2_data_by_one` 产物离原码更近一条（仍不匹配，非回归） ⇒ **GO** |
| G4′ 逐产物严格尺复验（落地字节 × 提交产物，36 个受影响文件） | `broken` 必须为 0 | `affected rows 36 of 402`、`fixed=4 broken=0` ⇒ **PASS** |
| G5 `single` 靶 ＋ 金丝雀 | 官方尺改进、金丝雀不得掉函数 | 靶 `IQCommon/util/common_func.pyc` `single` ⇒ `19/21 (90.48%)`，缺项表已无 `fill_kline_data`／`fill_kline_data_by_pre`；提交前复跑 `single`：`pyc_index.json` sha256[:20] 前后同为 `d00a1d63d727843b6f26`（回写未移动任何字段，与 G6 结果一致）⇒ 靶 **PASS**。金丝雀：原判据「`quotationOK.py` 逐字节不变」写错（抄了 Round 39 的数，未复测）；复测 ⇒ 9 支里 **3 支产物文本移动**，**0 支掉官方函数**（`quotation 143/143`、`IQData/manager/plugin_manager 10/10`、`IQEngine/core/plugin_manager 9/9` 全部保持满匹配），与 G4 `REGRESSION=0`、G4′ `broken=0` 一致 ⇒ 按更正后的判据 **PASS**，详见 §五·6 与 `logs/g5_canary_audit.txt` |
| G6 `batch --index pyc_index.json --all --round 40` | 402 条读完、索引差异可解释 | 402 条读完、`failed_pyc 0`；索引差异 = 402 条 `last_tested_round → 40` ＋ **仅 3 支文件的 6 个字段**（`IQCommon/util/common_func.pyc` matched 17→19、`IQData/utils/common_func.pyc` 22→23、`fly/data/quote.pyc` 67→68，各自 `bytecode_match_rate` 同步），无其他状态翻转（`logs/g6_round40.log.txt`、`logs/g6_index_diff.txt`）。注：G5 的 `single` 会把靶文件回写索引，故差异基线取 **Round 39 提交的 HEAD blob** 而非 G6 前的工作区快照 |
| G7 `stats` 原样 | 见 §三 | — |

## 三、G7 `stats` 原样

```
======================================================================
累计统计:
  total_pyc:             402
  verified_pyc:          402
  ok_pyc:                375
  partial_pyc:           27
  failed_pyc:            0
  total_functions:       5746
  matched_functions:     5655
  cumulative_match_rate: 98.42%
======================================================================
```

## 四、落地字节

| 项 | 改前 | 改后 |
| --- | --- | --- |
| 文件 | `core/cfg/region_ast_generator.py` | 同 |
| 字节数 | 2 988 464 | 2 991 175 |
| CRLF 计数 | 48 474 | 48 506 |
| UTF-8 BOM | 在位 | 在位 |
| sha256[:20] | `cc1254fa30410f2b9954` | `f1cde2536f9fa2c9033b` |
| diff | — | +33 / −1 行（唯一改动行：`if not _mb_meaningful:` → `if not _mb_meaningful or _mb_then_escapes:`；其余 32 行为新增判据与其注释） |

写入方式：`land38.py land --spec=spec40a2.json --mirror=mirr_r40a2 --apply`，
落地前断言「重放结果 == 被测镜像字节」（`replay == measured mirror bytes: OK, 2991175 bytes`），
即 shipped 字节与 G4 测量字节同源，不手抄。

## 五、残余与移交

1. **同族第二子形状仍未解**：`real_quote.pyc` 与 `quote.pyc` 的 `one_prod_to_dataframe` 两支各差一条
   `JUMP_BACKWARD`（`orig=485 decomp=484`）。形状是 **多块 then 臂中段的 `continue`**：缺失块
   `B@1818 succs=[742]`（直落内层循环头）位于 `IfRegion(cond=746, then=[18 块], merge=1972)` 的臂内**中段**，
   既非该区域 then 尾块，其 `merge=1972` 也不等于 `back_edge_block=1864` ⇒ R40-A2 正确地不去碰它。
   需另立一条同层判据（臂内逃逸块的归属），下一轮可作线 B。
2. **本轮判据的暴露面已量化**：G4 后 36 行 MOVED 说明「产物文本变了但官方计数不变」是本族的常态副作用
   （`continue` 渲染 ↔ `else:` 渲染互换在指令层面不可见）。`r40c_1_two_tails`／`r40c_5_merge_join`
   两支负对照钉住「只有全部 then 尾逃逸才提升」这一收紧，后续若有人放宽需先过这两支。
3. **承重资产更新**：新电池 `test_repros/round40_merge_not_a_merge/{r40w_witness,r40c_controls}.py` 入库
   （其 `pyc/` 由 `py_compile` 现场重建，仓库按 `.gitignore` 不收 `.pyc`，与既有各轮电池一致）；下一轮 G2′ = `reprobat59` + Round 39 电池 + 本轮电池（已生成 `D:/Temp/r40gate/reprobat61.txt`，
   63 条目），G3 = `D:/Temp/r40gate/anchors109.txt`（109 条目）。落地后本轮见证电池 head 侧将转为全匹配，
   天然阳性对照仍由 `r3_04_loop_branch_continue_lost`（3/3）之外的 `ctl_two_cont` 承担 —— 见 tasks.md 40.9。
4. **结转台账不变**（本轮未触碰）：8 条布局等长行、`matcher::match 713/689`（R37-B NO-GO）、`clock_worker +6`、
   `decrypt_database_url 295/324`、`events 510/508`（不得再从 else 归属下手）、`_init_config 86/84`、
   `OverNightOrder.__init__ 172/148`、#61 ＋ `r29x_01 <module> 142/138`、`get_all_real_daily_kline 188/187`
   （合流形状，不得靠放宽 R39-B 私有性一项去够）。
5. R40-A（「某条 then 尾逃逸」宽版）也过了 G0/G1，但**未被采纳**：它不足以否定 merge 角色，
   与 R40-A2 的差别正是本轮唯一有判别力的负对照 `r40c_1_two_tails`。双臂都留着备查
   （`mirr_r40a` / `mirr_r40a2`，spec 在 `logs/`）。

6. **金丝雀复测更正（提交前抓到的记录性错误）**：§二 G5 行原本抄用 Round 39 的
   `quotationOK.py` sha256[:20] `3f2242e73d7fd56a0096` 并宣称「改前＝改后」，属**未复测的结转值**。
   实测（`logs/g5_canary_audit.txt`，直接比 G4 双臂 402 行转储，零额外开销）：

   * 该值本身是 Round 39 时代**工作区 CRLF 字节**的哈希（HEAD blob 的 LF 形 `9180650d0244cb63` → CRLF 形
     `3f2242e73d7fd56a0096`，差 3693 字节 = 行数），当时为真；
   * 本轮落地后 `quotationOK.py` 的 LF 形变为 `857956e7f8d9e97c`（工作区 183 261 → 183 298 字节，
     `git diff --numstat` = 4 增 3 删）⇒ **「逐字节不变」这条判据本轮被破**，不是被隐瞒；
   * 破它的改动是 §五·2 已预告的同族渲染互换，`get_option_info` 内：
     `if isinstance(value, dict): …; continue` ＋其后平铺的 `dict1[key] = value; continue`
     → `elif …:` ＋ `else: …; continue`。两支互斥分支各自以 `continue` 收尾，`if/if` 与 `if/elif/else`
     编译到同一串指令，故官方尺 `143/143` 不动、严格尺侧 `change_his_to_forward`／`get_trend`
     两支在**双臂同为 still-defective**（G4′ 已列，`broken=0`）；
   * G4 双臂逐行核对：产物文本移动 36 支，其中官方计数不变 33 支、上升 3 支、**下降 0 支**；
     9 支承重金丝雀里文本移动 3 支、比值全保持。
   据此把 G5 的金丝雀判据由「逐字节不变」更正为「**承重文件不得掉官方函数**」，
   并从落地后的 402 产物重新导出下一轮基线 `D:/Temp/r40gate/canary_shas_landed40.txt`。
   教训入档：门禁数值必须本轮实测，任何从上一轮记录里抄来的数都是未验断言。
