# Round 41 结果 —— 落地 R41-B2（臂中段逃逸回边：CONTINUE 早退路径必须补出 `continue`）

## 一、结论

发货判据（G4 全 402 私有镜像双臂 A/B）：**IMPROVED=2 文件 / REGRESSION=0 / MOVED=0**，
其余 400 行逐条目 `sha` 与 per-file 计数全等 —— 本轮在整个语料上**零附带文本移动**。
据此落地一条同层判据 R41-B2，`core/cfg/region_ast_generator.py` 按被测镜像字节精确重放写入。

修复的 2 个函数（G4′ 用落地字节对提交产物重做严格尺复验，`fixed=2 broken=0`）：

| 函数 | 宿主 `.pyc` | 官方尺 per-file |
| --- | --- | --- |
| `one_prod_to_dataframe` | `fly/data/quote.pyc` | `68/81 → 69/81` |
| `one_prod_to_dataframe` | `IQData/plugins/plugin_system_realquote/real_quote.pyc` | `38/44 → 39/44` |

正是 Round 40 移交的「同族第二子形状」：两支孪生 `one_prod_to_dataframe`，缺块 `B@1818→742`
既非该区域 then 尾、`merge=1972` 也不等于 `back_edge_block=1864`。R40-A2 正确地不去碰它，
本轮按移交结论另立「臂内逃逸块归属」判据把它收掉。

## 二、根因（实测，非推断）

`_process_if_blocks` 的 `role in (CONTINUE, PURE_CONTINUE)` 早退路径：块带「有意义指令」时发射它的
语句、登记 `generated_blocks` / `generated_offsets`，随后直接 `continue` —— 于是该块的**逃逸终止符**
（回边到当前循环头）被静默丢弃。逃逸只有在两种既有情形下能再生：

1. 块是该区域的**最后一块**（后接连接器，R100 / R4-H 负责补终止符）；
2. `region.merge_block` **就是**循环头（区域以回边为汇合点，即自然尾）。

两支靶点都是 17 块 then 臂的**中段**（运行时指纹 `is_last=False`、`merge=1972 ≠ hdr=742`），
两条都不成立 ⇒ `continue` 消失 ⇒ 循环体在该分支多走一轮 ⇒ 其后指令序列整体错位（`seq_-1`）。

## 三、判据（唯一一条，同层）

在上述早退路径发射语句之后、登记块之前，追加一条 `Continue`，当且仅当：

- ① 该块终止符是 `JUMP_BACKWARD` / `JUMP_BACKWARD_NO_INTERRUPT`，且其目标块**即** `self._current_loop.header_block`（块身份比较，不读偏移数值）；
- ② 承载它的区域是 `IfRegion`，其 `merge_block` 存在且不等于该循环头（即 merge 不是回边本身）；
- ③ 该块在 `blocks` 中存在且**不是最后一个**（否则情形 1 已负责发射，追加即为过火）。

一致性：原则 1 保持（块的其余语句＋这条补出的 `continue` 恰为一个终止符）；原则 2 不新增归属；
判据只读结构事实（块身份、区域角色、区域 merge 关系、终止符操作码类），不读名字/常量/绝对偏移/指令计数/历史。

## 四、门禁台账（严格串行，全部实测）

| 门禁 | 判据 | 实测 |
| --- | --- | --- |
| G0 合成见证（与语料无关，先对**落地字节**跑） | 见证必须改前失败、改后 CLEAN，负对照不得翻转 | head 臂（与工作区字节全等）：`r41w7_corpus_shape DEFECT 1 one_prod_to_dataframe:seq_-1`，另 3 支 CLEAN ⇒ 见证确实失败。v1（缺 ③）翻坏 `r41w_2_guard_break:seq_-6`、`r41w5_break_then_merge_escape:seq_-5` ⇒ **G0 否决 v1**（`g0_r41b.txt`／`g0_r41b2.txt`）。R41-B2：`cases=4 CLEAN=4 DEFECT=0`（`g0_r41b3.txt`、`g0_w41cand.txt`），`r41c_*` 六支负对照双臂均 CLEAN ⇒ **PASS** |
| ③ 的来源（运行时指纹，只读插桩） | 追加条件必须由测量的触发分布支撑，不得由叙事推出 | 11 次触发中**只有语料那次** `is_last=False`（`blk=1818 idx=3 nblocks=17`），其余 10 次均为 `idx == nblocks-1`（`fire.txt`）⇒ 「非最后块」正是把语料形状与既有形状分离的那一条 |
| G1 deficit-1＋deficit-2 池（17 行）＋ 2 支靶点 | 无回归、靶行改善 | 池：`SAME=17 IMPROVED=0 REGRESSION=0 MOVED=0`；靶：`quote.pyc 68/81→69/81`、`real_quote.pyc 38/44→39/44` ⇒ **PASS** |
| G2′ `reprobat61` ＋ Round 40 电池（63 条目） | 承重电池零翻转 | `SAME=63 REGRESSION=0 MOVED=0 ERR=0` ⇒ **PASS** |
| G3 `anchors109` 承重锚点集（109 条目） | 承重锚点零翻转 | `SAME=109 REGRESSION=0 MOVED=0 ERR=0` ⇒ **PASS** |
| **G4 全 402 双臂 A/B（唯一发货判据）** | 只允许 IMPROVED／count-neutral MOVED | `SAME=400 IMPROVED=2 REGRESSION=0 MOVED=0 ERR=0`；Σmatched `5655 → 5657`（head 侧 Σ 与 G6 前索引同值 ⇒ 内部一致性）；`files fully matched a=375 b=375` ⇒ **PASS** |
| G4′ 严格尺（对 2 个受影响产物，落地字节） | 不得破任何已干净函数 | `affected=2 fixed=2 broken=0`（产物各增 1 行 `continue`，别无差异） ⇒ **PASS** |
| 落地 | 字节精确重放 | `land38.py land --spec=spec41b2.json --mirror=mirr_r41b2 --apply`，断言「重放 == 被测镜像字节」为 True ⇒ **PASS** |
| G5 `single` 靶 ＋ 承重金丝雀 | 靶行复测；金丝雀不得掉官方函数 | `fly/data/quote.pyc matched 69 rate 85.19%`、`real_quote.pyc matched 39 rate 88.64%`；`canaries=9 baseline-sha mismatches=0 text-moved=0 lost-official-function=0`（`logs/g5_canary_audit.txt`）⇒ **PASS** |
| G6 `batch --all --round 41` | 读完 402、`failed_pyc 0`、索引差异可解释 | `verified 402 / failed 0`；差异 = 402 条 `last_tested_round → 41` 加**仅 2 支**字段变化：`quote.pyc [68→69, 0.8395→0.8519]`、`real_quote.pyc [38→39, 0.8636→0.8864]` ⇒ **PASS** |
| G7 `stats` | 原样，见 §五 | — |

## 五、G7 `stats` 原样

```
======================================================================
累计统计:
  total_pyc:             402
  verified_pyc:          402
  ok_pyc:                375
  partial_pyc:           27
  failed_pyc:            0
  total_functions:       5746
  matched_functions:     5657
  cumulative_match_rate: 98.45%
======================================================================
```

## 六、落地字节

- `core/cfg/region_ast_generator.py`：2 991 175 → 2 994 079 字节，CRLF 48 506 → 48 540（+34 行，全部 LF→CRLF 一致），UTF-8 BOM 在位，`git diff --numstat` = `34  0`，sha256[:20] `f1cde2536f9fa2c9033b` → `11e2c67e2d7681735f9d`。
- 唯一改动点：`_process_if_blocks` 的 CONTINUE/PURE_CONTINUE 早退路径内、`stmts.extend(bs)` 与 `self.generated_blocks.add(block)` 之间。
- 提交产物同步更新：`site-packages/fly/data/quoteOK.py`、`site-packages/IQData/plugins/plugin_system_realquote/real_quoteOK.py`（各 +1 行 `continue`）；`pyc_index.json` 由 G6 写回。

## 七、残余与移交

1. **新承重电池并入 G2′**：`test_repros/round41_mid_arm_continue/`（`r41w_witness`、`r41c_controls`、
   `r41w2_merge_escape`、`r41w7_corpus_shape` 四支 `.py`，`pyc/` 由 G0 驱动再生）。其中
   `r41w_2_guard_break` 与 `r41w5_break_then_merge_escape` 正是**钉住判据 ③** 的两支，
   下一轮 G2′ = `reprobat61` ＋ Round 40 电池 ＋ Round 41 电池。
2. **G5 金丝雀基线需重导**：本轮有 2 支产物文本移动，`D:/Temp/r40gate/canary_shas_landed40.txt`
   对这 2 支已陈旧（9 支金丝雀本身逐字节未变，故本轮判据仍满足）。下一轮基线以 landed-41 重导。
3. **Round 42 线（已交付、未发货、必须独立复测）**：线 A 给出第二条同层候选 ——
   `core/cfg/region_analyzer.py:24631-24637` 的 W14-A break，靶 `handle_exrights`
   （`IQData/utils/common_func.pyc`，若成立则该行翻为全匹配、deficit 文件 27 → 26）；
   spec `D:/Temp/r41diagA/spec41a.json`（+9 行，BOM=False），见证电池 `D:/Temp/r41diagA/witness/`，
   代理自测 A/B `SAME=400 IMPROVED=1 MOVED=1 REGRESSION=0`。为保证一轮一条判据，本轮不采纳；
   采纳前必须在**新落地字节 `11e2c67e2d7681735f9d`** 上重做锚点唯一性、见证改前失败与真实双臂 A/B，
   且其 witness 需迁入 `test_repros/`。
4. **结转台账（本轮未触碰）**：8 条布局等价行（`_all_bars_of_cache 230/231`、`trade_logs_control 193/194`、
   `check_stock 88/89`、`get_history_new 322/323`、`get_multiminute_his_data 481/482`、5 条等长 `finally` 换位）；
   `matcher::match 713/689`（R37-B NO-GO）；`clock_worker +6`；`decrypt_database_url 295/324`；
   `events 510/508`（不得再从 else 归属边进攻）；`_init_config 86/84`；`OverNightOrder.__init__ 172/148`；
   #61 ＋ `r29x_01 <module> 142/138`；`get_all_real_daily_kline 188/187`（不得靠放宽 R40-A2 的
   「无人抵达 merge」项去够）；`quote.pyc` 余 12 处（含 `get_price 230/188`、`get_real_from_zeromq 703/669`）；
   `real_quote.pyc` 余 5 处（含 `one_prod_to_ndarray 605/607`）。
