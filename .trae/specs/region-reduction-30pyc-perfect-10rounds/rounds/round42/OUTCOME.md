# Round 42 结果 —— R42-A 在 G0/G4′ 被否证（官方 ＋1 是假 ok）⇒ 本轮 core/ 零改动、不发货

## 一、结论

候选 R42-A（线 A 交付，`core/cfg/region_analyzer.py` 的 W14-A 断链处放行「直落后继恰为链共同出口」的末操作数）
**否证，不落地**。本轮 `core/` 零改动，`pyc_index.json` 与全部提交产物未变。

否证理由（实测，不是风格判断）：它把缺陷从「少发指令」换成「短路接线的跳转终点错误」，
同时**在官方尺上 ＋1**。官方尺对跳转指令只比操作码、不比已解析的跳转终点
（`_r10_strict_check.py:10` 记录过这一失效模式：跳转终点差异被误判成 `target_diff`，制造假 ok），
故该候选正是「用假 ok 换计数」的形状。

## 二、两条决定性证据

**(1) 合成见证（G0）**：源 `if not dd or sym not in dd or len(dd[sym]) == 0:`

- 落地臂产物：`if dd and sym in dd:` ＋ 体内联 ＋ 尾随 `return` —— 丢掉第三个操作数、`not in` 取反，`seq_len orig=43 decomp=35`（少发 8 条）。
- 候选臂产物：`if dd and sym not in dd or len(dd[sym]) == 0:` ＋ `else:` 包体 —— 43 条全恢复（`Σ|Δ| 8 → 0`），
  但 `target_diff #2 POP_JUMP_IF_FALSE 终点 orig=('flds', LOAD_FAST) decomp=('len', LOAD_GLOBAL)`。
  首个操作数的 `not` 被吞成 `and` 链连接词：`dd` 为假时源应**直接 return**，产物却继续求值 `len(dd[sym])` ⇒ **KeyError 路径**，语义不等价。
  四支 or 链见证（`w1`/`w2`/`w3`/`r42w_1`）在候选臂上全部 `Σ|Δ| → 0` 却全部残留 `target_diff` ⇒ **无任何一支达到 strict-CLEAN**，G0 的「改后必须 CLEAN」不满足。

**(2) 语料真身（G4′）**：`IQData/utils/common_func.pyc :: handle_exrights`

- 落地：`seq_len orig=276 decomp=268`（官方 `23/24`）。
- 候选：`target_diff #2 POP_JUMP_IF_FALSE 终点 orig=('fields', LOAD_FAST) decomp=('len', LOAD_GLOBAL)`，而官方 `24/24`。
- 产物首行 `if tmp_dividends and symbol not in tmp_dividends or len(tmp_dividends[symbol]) == 0:`
  vs 源 `if not tmp_dividends or symbol not in tmp_dividends or len(…) == 0:` ⇒ 同一个取反吞噬，实证成立。

## 三、其余门禁（同一双臂，全部实测；均不构成发货许可）

| 门禁 | 实测 |
| --- | --- |
| 锚点唯一性 / 镜像完整性 | `build --spec=spec41a.json --dst=r42a`：1 edit、`core/cfg/region_analyzer.py`、BOM=False、CRLF、插入 9 行、head 镜像与工作区字节全等（落地-41 `11e2c67e2d7681735f9d`） |
| G1 deficit-1＋2 池 17 行 | `SAME=15 IMPROVED=1 REGRESSION=0 MOVED=1` |
| G2′ `reprobat61`（63 条目，含 Round 40/41 电池） | `SAME=63 IMPROVED=0 REGRESSION=0 MOVED=0 ERR=0`，`fully matched a=52 b=52` |
| G3 `anchors109`（109 条目） | `SAME=109 REGRESSION=0 MOVED=0 ERR=0`，`fully matched a=79 b=79` |
| **G4 全 402 双臂 A/B** | `SAME=400 IMPROVED=1 REGRESSION=0 MOVED=1 ERR=0`，`fully matched a=375 b=376` |
| G4 的 MOVED 行 | `IQData/api/api_base.pyc::get_history_df` 官方计数不变（23/25），`1718/1742 → 1739/1742`（少发 24 条 → 少发 3 条，长度更近，仍不匹配）⇒ 同族同一失效模式，不构成反驳 |
| G4′ 严格尺（2 个受影响产物） | `affected=2 fixed=0 broken=0` —— 目标函数未变干净，仅换缺陷类 ⇒ **否决发货的判据** |

注：G4 的 `IMPROVED=1 / REGRESSION=0` 单独看是「可发货」形状；本轮把 **G4′ 提到与 G4 同级**：
若 G4 的每一个 IMPROVED 行在 G4′ 上都不是 strict-CLEAN，则该 IMPROVED 视为假 ok ⇒ NO-GO。
（Round 41 的先例：G4 IMPROVED=2 且 G4′ `fixed=2 broken=0`，二者同向，才落地。）

## 四、真实缺陷的层位（移交下一轮）

候选没有修的那个东西才是靶：短路链在**条件语境**下被重建时，首操作数的隐式取反被并入连接词，
`not A or B or C` 被拼成 `A and B or C`。落地点在发射/条件重建侧（`region_analyzer.py::_detect_boolop_conditional_chain`
把链成员拼成 BoolOp 处，或 `region_ast_generator` 的条件表达式生成处），与「是否断链」不同层。
判据应当是：重建后的条件在**跳转终点意义下**与原 CFG 同构（每个 `POP_JUMP_IF_*` 的真/假出口分别落到链的下一操作数与共同出口），
而不是「指令多重集相同」。

新承重电池：`test_repros/round42_orchain_fallthrough/`（`r42w_corpus_shape` 两支、线 A 的 `w1/w2/w3` 与 `nc1..nc4`）。
其判据用法：任何触及该族的未来候选，必须让 `r42w_1_orchain_tail_fallthrough` 达到 **strict-CLEAN**；
只在官方尺上变绿不算修好。

## 五、结转台账（本轮未触碰）

Round 41 的全部残余原样结转：8 条布局等价行、`matcher::match 713/689`、`clock_worker +6`、
`decrypt_database_url 295/324`、`events 510/508`（不得从 else 归属边进攻）、`_init_config 86/84`、
`OverNightOrder.__init__ 172/148`、#61 ＋ `r29x_01 <module> 142/138`、`get_all_real_daily_kline 188/187`、
`quote.pyc` 余 12 处（含 `get_price 230/188`、`get_real_from_zeromq 703/669`）、`real_quote.pyc` 余 5 处
（含 `one_prod_to_ndarray 605/607`）。本轮新增：`handle_exrights`（假 ok 已否证，真缺陷在条件重建侧）、
`api_base::get_history_df`（少发 3 条，与上同族）。
G5 金丝雀基线仍需以 landed-41 重导（本轮无产物变化，旧基线对本轮无事，但 Round 41 的两支产物已移动）。
