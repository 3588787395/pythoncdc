# Round 47 — OUTCOME

落地：R47-A（单条同层判据，纯插入 34 行）。发货字节 `core/cfg/region_ast_generator.py`
`b8bfc794dc6c852e7d9c → 2a3d522b0ec9e8fe66e4`（len 3 000 351 → 3 003 323，CRLF 48 620 → 48 654，
裸 LF 0，UTF-8 BOM 保留）；`core/cfg/region_analyzer.py` 逐字节未动 `55a9f61b9b0703063d44`。

开工时核对的落地字节（Round 46 发货态，HEAD `7a17aeca`）：
generator `b8bfc794dc6c852e7d9c / 3 000 351 / CRLF 48 620 / 裸 LF 0`，
analyzer `55a9f61b9b0703063d44 / 1 681 035`。

## 1. 靶与根因（R47-A，线 A 代理交付、编排方独立复测）

`site-packages/IQEngine/plugins/plugin_system_log/__init__.pyc :: <module>.DefaultLogger.trade_logs_control`
官方行 `[189, 190, 1, 144]`：产物比原始**多恰好一条指令**，strict `seq_len orig=193 decomp=194`；
编辑脚本证明唯一非平移改动是 `INSERT …('JUMP', 420)`，其余 144 个 `true_diffs` 全是它的位移影子。

原始字节码：

```
B12  term=POP_JUMP_FORWARD_IF_FALSE 294   succ=[B232(落入), B294(跳转)]
B232 term=STORE_FAST norm_log_size        succ=[B294]        <-- 纯落入，无跳转
B294 term=POP_JUMP_FORWARD_IF_FALSE 418   succ=[B356, B418]
```

源文本是 `if exists(norm): …` 之后**顺序**跟着 `if exists(sys): …`（真 else/elif 需要一条跨过第二个
测试的 `JUMP_FORWARD`，字节码里没有）。`_loop_handle_no_exit_successors`
（`core/cfg/region_ast_generator.py:9955`）只按极性配对取 `_then_succ`/`_else_succ`，
把 `_else_succ` 当 else 臂整段生成，于是 `If(body, orelse=[If(...)])` 渲染成 `if/elif`——
违反原则 1（`B232` 的唯一终结符是落入，被当作无条件跳转），并提前把 `B294` 记为已发射。

判据（六条合取，全读结构事实）：① `not _then_is_continue`；② `_else_succ is not block`；
③ `_else_succ ∈ _then_succ.successors`；④ `_then_succ` 的终结符 opname ∉ `FORWARD_JUMP_OPS ∪ BACKWARD_JUMP_OPS`
（⇒ ③ 的可达性只能是落入）；⑤ `_then_succ` 不是任何子区域的入口块（臂尾即自身）；
⑥ `_else_succ ∈ self._current_loop.blocks ∧ _else_succ ∉ self.generated_blocks`（发射责任仍欠着）。
命中 ⇒ 发 `If(test, body)`（**无 orelse**）、只登记 `_then_succ`，并 `return` 而不认领 `_else_succ`，
让循环体的顺序归约按入口引用它（原则 2 + 原则 4）。
反证：真 else 臂的 then 臂末块必以无条件前向跳转跳过 else 臂（④ 假），或其后继集不含 `_else_succ`（③ 假）。

## 2. 门禁（编排方独立复跑，全部串行）

| 门 | 结果 |
|---|---|
| G0 合成见证（`g047.py`，9 个 code object，`w47_witness.py`） | 落地前 `defective=3/9` → 候选 `1/9`；逐 code object 签名 `identical=7 differs=2`（两条 DIFFERS 即见证本身） |
| G1 靶池 27 支（`g1pool46.txt`，a 侧 `round46/g1_r46bB.jsonl`） | `SUM files=27 same=26 gained=1 lost=0`，`UP __init__.pyc 8/10 → 9/10`（`g1_r47aA.jsonl`） |
| G2′ test_repros 电池 143 支（a 侧 `bat45.jsonl`） | `SUM files=143 same=143 gained=0 lost=0`（`g2_r47aA.jsonl`） |
| G3 锚点 109 支（a 侧 `anch45.jsonl`） | `SUM files=109 same=109 gained=0 lost=0`（`g3_r47aA.jsonl`） |
| G4 全量 A/B 544 路径（唯一发货判据，a 侧 `round46/g4bB_all.jsonl`） | `SUM files=544 same=543 gained=1 lost=0`；sha 变化面 = **1 支产物**（`changed47a.txt`） |
| G4′ strict 尺对变更产物（落地**前**） | `affected=1 fixed=1 broken=0 changed=0`：`FIXED trade_logs_control [seq_len orig=193 decomp=194]`；同文件其余 8 个 code object 签名与原始相等，`setup` 未被扰动 |
| G5 single + 电池复跑（落地后字节） | `__init__.pyc matched_functions: 9`，mism 只剩 `setup [320, 253, 1, 293]`；产物唯一改动 `elif os.path.exists(sys_log_path)` → `if …`。五支电池 `zg0_landed.json`：`1/9, 3/15, 0/5, 0/4, 0/8` |
| G6 `batch --index pyc_index.json --all --round 47` | 402 verified / 0 failed；索引差异 = 402 条轮次戳 + 1 条 `matched_functions 8→9`（同条 `bytecode_match_rate 0.8→0.9`） |
| G7 `stats` | `375 ok / 27 partial / 0 failed`，`matched_functions 5662`，`cumulative_match_rate 98.54%` |

产物改动面：`site-packages/` 下唯一变化 `IQEngine/plugins/plugin_system_log/__init__OK.py`（1 行）。

## 3. 否证与移交

* **R47-B（编排方一手候选）在 G0 即回归，本轮不落地。** 靶
  `site-packages/fly/data/quote_handler.pyc :: <module>.get_Ashares_local`（官方 `75/77`，`j=0`，`t=24`）：
  try 体保护段把 `LOAD_FAST returnlist | RETURN_VALUE` 切进两块，`_generate_try_body:23536`
  因此发 `Expr(returnlist)` + `return None`（多出 `POP_TOP / LOAD_CONST None`），
  见证电池 `r47_tryret_witness.py` 在落地字节上 `defective=3/15`。
  折叠臂 `mirr_r47b`（generator `3fa23dc13fd7f2bc5d48`）把它变成 `defective=7/15`：
  `r47_01/04/05` 的 `try` 语句**整条消失**（strict `orig=50 decomp=5`、嵌套 `<listcomp>` MISSING），
  并破坏对照 `r47_07_try_tail_return_attr`（`44/6`）。stderr 无
  `Region-based decompilation exception` ⇒ 是下游结构守卫静默丢弃了 `body_stmts[-1]` 为带值 `Return`
  的 Try 节点，折叠点须换到该守卫可接受的表示。三支旧电池（5/4/8 个 code object）在此臂下
  签名零变化 ⇒ 折叠对无关形状确为惰性，但它不足以发货。靶移交 Round 48。
* **`setup`（320/253，缺 65 条）不是区域归约洞**（线 A）。三条语句前缀 48 + 9 + 9 = 66 删、
  1 插（`BUILD_TUPLE`）＝净 65；涉及的块全部**已发射**，只是前缀被三元区域边界的待定操作数队列吞掉：
  `IF_ELIF_CHAIN@B112` 的 `merge_block=B646` 是后代 `TernaryRegion(entry=B176)` 的**内部块**
  （`B646 ∉ chain.blocks`），且 R46-B 的判据 ③（`owner.entry` 即该块）在此为假。
  区分事实是「块的指令流停在表达式中段」，属操作数栈层，非层内判据。
  合成电池 `g0tern.py` 在落地字节上复现同一 `(cond, cond)` 伪影：
  `t47_10 69/37`，两条阴性对照 `17/17`、`24/24`。移交 Round 48（候选方向：
  `ExpressionReconstructor` 的跨块操作数队列，或 analyzer 不让链取后代内部块作 merge）。
* **否证同簇假设**：`write_logging_thread 113/113 j1`（R46-C1，等长 MOVE）与
  `flyAccount :: init_connection 42/41`（线 D）在 R47-A 下逐字节不变（`fly/logger.pyc` 仍 28/30、
  `flyAccount.pyc` 仍 21/23）⇒ 三者机制不同，线索各自保留。
* 线 B（`fly/data/quote.pyc` 四函数族）、线 C（七支 deficit-1）本轮交付时窗口已用尽，
  其 scratch 目录 `D:/Temp/r47diagB`、`D:/Temp/r47diagC` 与臂留在原地，结论并入 Round 48 开工复测。

## 4. 残余靶（本轮未动，官方行原样）

`matcher::match`、`clock_worker`、`decrypt_database_url`、`events 510/508`、`_init_config 86/84`、
`OverNightOrder.__init__`、`api_base::get_history_df −24`、等长换位的 10 行、`params_analysis 133/126`、
`quote_handler :: get_kline_local 760/682 j=12`、`get_index_stocks_local` 残余 1 条、`setup`、
`trade_logs_control` 之外本文件无残余。
