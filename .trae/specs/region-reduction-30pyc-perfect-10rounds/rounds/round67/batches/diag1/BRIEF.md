# Round 67 · diag1 · BRIEF（只读诊断代理）

工作目录 `D:/Temp/opencode/r67gate/diag1`。**仓库零改动**：不得写 `F:/Downloads/pythoncdc-main` 下任何文件
（包括 `core/`、`*OK.py`、`pyc_index.json`、`.trae/`、`test_repros/`）；所有产物写到本目录。
唯一允许的“写仓库”动作是读取（`h62.py build` 自带镜像==工作树断言，任何污染都会立刻失败）。
**不要跑 402 全量扫描** —— 那是集中验证方的职责（上一轮三支代理死在 150 轮上限，402 是主要开销）。

## 名下靶支（landed = 当前工作树 = R66 落地字节，中心已实测；逐函数读数见本目录 `targets.md`）
# diag1 targets (1 files, official gap 12, strict defects 18)

## IQEngine/plugins/plugin_system_trade/trade_live_broker.pyc
   pyc: F:/Downloads/pythoncdc-main/site-packages/IQEngine/plugins/plugin_system_trade/trade_live_broker.pyc
   official 107/119 (gap 12)   strict 105/123 (defects 18, missing 0, extra 0)
   OFF    _process_cancel_order                        orig=293   decomp=292   hunks=16 first_diff=43
   OFF    _process_order                               orig=454   decomp=396   hunks=9  first_diff=349
   OFF    _sync_worker                                 orig=349   decomp=347   hunks=0  first_diff=296
   OFF    _trade_status_handle                         orig=114   decomp=112   hunks=0  first_diff=107
   OFF    after_trading_cancel_order                   orig=155   decomp=155   hunks=3  first_diff=122
   OFF    etf_basket_order                             orig=693   decomp=693   hunks=11 first_diff=216
   OFF    etf_purchase_redemption                      orig=377   decomp=369   hunks=1  first_diff=37
   OFF    get_all_orders                               orig=79    decomp=78    hunks=2  first_diff=24
   OFF    get_max_amount                               orig=201   decomp=213   hunks=2  first_diff=18
   OFF    ipo_stocks_order                             orig=1075  decomp=1076  hunks=10 first_diff=437
   OFF    on_order_response                            orig=445   decomp=444   hunks=6  first_diff=57
   OFF    on_trade_response                            orig=392   decomp=391   hunks=6  first_diff=57
   STRICT _process_cancel_order                        [seq_len] orig=295 decomp=296
   STRICT _process_order                               [seq_len] orig=454 decomp=399
   STRICT _process_tick_order                          [target_diff] #27 JUMP 终点 orig=("'len'", 'LOAD_GLOBAL') decomp=("'self'", 'LOAD_FAST')
   STRICT _sync_worker                                 [seq_len] orig=350 decomp=347
   STRICT _trade_status_handle                         [seq_len] orig=114 decomp=112
   STRICT after_trading_cancel_order                   [seq_len] orig=156 decomp=159
   STRICT etf_basket_order                             [seq_diff] #254 orig=("'strategy_log'", 'LOAD_GLOBAL') decomp=("'entrust_price'", 'LOAD_FAST')
   STRICT etf_purchase_redemption                      [seq_len] orig=379 decomp=369
   STRICT get_all_orders                               [seq_len] orig=80 decomp=83
   STRICT get_ipo_stocks                               [target_diff] #189 POP_JUMP_IF_TRUE 终点 orig=("'str'", 'LOAD_GLOBAL') decomp=(None, 'FOR_ITER')
   STRICT get_max_amount                               [seq_len] orig=201 decomp=213
   STRICT ipo_stocks_order                             [seq_len] orig=1075 decomp=1076
   STRICT on_order_response                            [seq_len] orig=449 decomp=448
   STRICT on_order_response_list_handle                [target_diff] #23 POP_JUMP_IF_NONE 终点 orig=("'entrust_no'", 'LOAD_FAST') decomp=(None, 'FOR_ITER')
   STRICT on_pre_before_trading_start                  [target_diff] #4 POP_JUMP_IF_FALSE 终点 orig=("'self'", 'LOAD_FAST') decomp=("'datetime'", 'LOAD_GLOBAL')
   STRICT on_trade_response                            [seq_len] orig=396 decomp=395
   STRICT on_trade_response_list_handle                [target_diff] #23 POP_JUMP_IF_NONE 终点 orig=("'entrust_no'", 'LOAD_FAST') decomp=(None, 'FOR_ITER')
   STRICT rzrq_credit_order                            [target_diff] #406 JUMP 终点 orig=("'Order'", 'LOAD_GLOBAL') decomp=("'EntrustDirection'", 'LOAD_GLOBAL')

## 中心已实测基线（直接复放校验，禁止当成自己的发现）
- `--arm=landed` 跑 `targets.txt` 必须与 `targets.md` 逐支相同；不一致就**停下**并写进 `FACTS.md`。
- 电池 31 项（`battery.txt`，含 7 支 R66 新复现）：合计 matched **115/127**、缺陷函数 12 支
```
  round63_b1/r63_ft.pyc                      2/2 []
  round63_b1/r63_ft2.pyc                     2/2 []
  round63_b1/r63_ft4.pyc                     2/2 []
  round63_b2/probe_r63b2_cases.pyc           7/9 [["c6_elif_try_then_more", 50, 50, 1, 15], ["c8_elif_chain_only", 31, 33, 1, 15]]
  round63_b2/probe_r63b2_cases2.pyc          7/9 [["d2_elif_notry", 44, 45, 1, 28], ["d8_elif_try_chain_or_plain", 51, 50, 1, 6]]
  round63_b2/repro_r63b2_tail_cmp_return.pyc 2/2 []
  round63_b3/r63b3_chained_value_ctx_prefix.pyc 2/2 []
  round63_b4/r63b4_tern_in_elif_chain.pyc    3/3 []
  round63_b5/r63b5_w1.pyc                    1/2 [["init_connection", 42, 41, 0, 25]]
  round63_fix1/r63b3_chainstore_prefix.pyc   2/2 []
  round63_fix2/r63b4_cond_boolop_stmt_steal.pyc 13/13 []
  round64_diag1/r64d1b_closed_exit_prefix.pyc 2/2 []
  round64_diag1/r64d1b_sibdispatch_attempt.pyc 4/4 []
  round64_diag2/r64d2_chain_yield_sibling_entry.pyc 2/2 []
  round64_diag2/r64d2_valuectx_consumer.pyc  2/2 []
  round64_diag3/r64d3_postif_join.pyc        2/2 []
  round64_diag4/r64d4_boolop_poptop_merge.pyc 3/3 []
  round64_diag4/r64d4_deferred_prefix.pyc    3/3 []
  round64_diag5/r64d5_contsink.pyc           1/2 [["probe", 122, 122, 1, 9]]
  round65_diag1/r65_trytail.pyc              8/9 [["p5", 33, 30, 2, 20]]
  round65_diag1/r65_trytail_w.pyc            8/8 []
  round65_diag2/fs2.pyc                      6/10 [["v1", 13, 11, 0, 3], ["v6", 15, 11, 0, 5], ["v7", 24, 24, 0, 1], ["v8", 33, 27, 0, 14]]
  round65_diag2/fsrepro.pyc                  7/7 []
  round65_diag5/r65d5_probe.pyc              2/2 []
  round66_diag1/r66_empty_then_join.pyc      3/3 []
  round66_diag3/r66d3_pred.pyc               2/3 [["v6", 36, 34, 2, 16]]
  round66_diag3/r66d3_shared_store.pyc       3/3 []
  round66_diag3/r66d3_var.pyc                6/6 []
  round66_diag4/r66d4_augsub.pyc             2/2 []
  round66_diag5/r66_else.pyc                 3/3 []
  round66_diag6/r66_delrepro.pyc             3/3 []
```
- 金丝雀 4 支 sha **必须逐支不变**：
```
  quotation.pyc          143/143 sha=4d41187e356544e0
  market_time.pyc         10/10  sha=af77224b34b203c4
  datetime_func.pyc       26/26  sha=e711b8ea86d49a15
  datetime_func.pyc       25/25  sha=9d09af09249da177
```

## 交付（按此优先级；轮次上限 150，边测边写 `FACTS.md`）
0. 复放基线（targets / battery / canary 各一遍 `--arm=landed`，每条 <120 秒），读数抄进 `FACTS.md`。
1. 对每个残余函数先跑**归一化 hunk 表**：`python -X utf8 nhunks.py <pyc> build_landed/<product> <fn> --ctx=3`
   （跳转目标归一为 `J`、嵌套 code object 常量归一为 `CODEOBJ`），据此判定「缺语句 / 多语句 / 纯换位」，
   把 orig 与 decomp 的偏移区间写进 `FACTS.md`。**counts 已相等却仍失败的函数，先查发射顺序，不要再找归属判据。**
2. 归因到 `core/cfg/region_ast_generator.py` 或 `core/cfg/region_analyzer.py` 上**当前落地字节**的具体
   函数与行号（`grep -n` 实测，上一轮的旧行号一律不可信），并给出该区域**同层次字段**证据
   （`regdump.py`、只读探针、`sys.settrace` 计数器均可）。
3. 写一个 **≤15 行合成复现**（`synth/xxx.py` → 编成 `.pyc`，另建一个本目录内的 `txt` 名单），
   证明它在 landed 上复现同一形状。**没有复现就不许提交 spec。**
4. 交 **一份** spec（`specs/cand_r67_<名>.json`，单文件、`edits` 列表里每个 anchor 在 LF 归一文本中
   `count==1`）。判据必须是**同层次结构身份**，注释含**三要素：识别条件 / 归约方式 / AST 映射**。
   禁止：按函数名/文件名/偏移/阈值匹配、`region.entry in r.blocks` 型跨区域跨层次包含、
   把 `self` 当帧内临时变量的新增状态、以及任何「不发射 / 直接抑制」式取巧。
5. 实测三组并写进 `FACTS.md`：`--arm=<cand>` 的 targets / battery / canary，然后
   `python -X utf8 h62.py ab --a=dump/landed.jsonl --b=dump/<cand>.jsonl`（battery、canary 同理），
   给出 SAME/IMPROVED/REGRESSION/MOVED/ERR。要求：**金丝雀 4 支 sha 逐字节不变、电池不得比基线差、
   名下靶支必须朝好的方向动**。
6. 若判定本批某支「无可落地判据」，在 `FACTS.md` 明确写 **候选：NONE** 并附排除读数；
   不要为交差而交 spec。**FACTS.md 即使只做到第 2 步也必须是完整可复放的记录**（这是最低交付）。

## 本批已知情报（R64–R66 归档 + 集中验证，先读再动手）
- 上一轮 diag1 交的 **E1**（generator 现 L16876 `[R66-diag1 E1 单测试空臂不得吞并 if/else 之后的汇合块]`）
  已落地，且把本支从 106/119 推到 **107/119**（`_sync_worker` 等）。E1 的 variant-1（去掉
  `chained_compare_blocks` 条款）在 402 上把 `strategy.pyc` 24/24→23/24 **已被否决**，不要重提该变体。
- 残余 12 支缺陷函数里，`_process_order`（orig 454 / decomp 396，缺 ~58 条）与
  `ipo_stocks_order`（1075/1076 但 jumpdiff=10、truediff=437）是两类不同形状：前者像语句丢失，
  后者 counts 基本相等 ⇒ 先按**位移/顺序**家族处理（见 [[project-r64-matcher-displacement-lead]] 的方法：
  计数已对齐时先查发射顺序，不要再找归属判据）。
- f-string 家族（R65 遗留、R66 的 P1/P3/P4 三支已落）在本支表现为 `on_order_response` /
  `get_etf_stock_info` 这类 1 指令差 + 大 truediff；现行规则在 generator L41633 `[R66-d2 P1]`、
  L36319 `[R66-d2 P3]`、L17055 `[R66-d2 P4]`，新判据必须证明与这三处不同层或互补。
- **禁止按函数名/文件名/偏移匹配**（`_process_order` 这类名字不能作为判据输入）。

## 工具与纪律
- 一律 `python -X utf8`；**禁止设置 PYTHONIOENCODING**；每条命令必须 <300 秒（长任务自己分片）。
- `h62.py`：`build --spec=specs/x.json --dst=x`、`run --arm=landed|x --list=targets.txt --out=dump/x.jsonl`、
  `ab --a=… --b=…`。产物名 = `site-packages/`（或 `test_repros/`）之后的路径 `/`→`__`、`:`→`_`、`.pyc`→`OK.py`。
- 严格尺：`python -X utf8 cstrict.py build_<arm> <list.txt> dump/<arm>_strict.json`
  （第一个参数是**本目录内的 build 目录名**，第二个是 pyc 名单；它给每支 `strict ok/functions` +
  每条缺陷 `[name, kind, message]` + missing/extra 嵌套 code object）。
- 落地代码里的 R66 标记（行号是本轮落地字节实测值，动笔前再 grep 一次）：generator
  L2842/L2855/L21991/L44623/L44755/L44823/L44833 `[R66 fix]`、L7219 `[R66-diag6-A for-iter-delete-terminator]`、
  L16876 `[R66-diag1 E1 …]`、L17055 `[R66-d2 P4]`、L26644 `[R66-diag5-B try-tail-unprotected-else]`、
  L36319 `[R66-d2 P3]`、L41633 `[R66-d2 P1]`、L44564 `[R66-diag4 D1 augsub-continue-role]`；
  analyzer L20949 `[R66-diag3 value-context chained-compare gate]`。
- 上一轮全记录：`F:/Downloads/pythoncdc-main/.trae/specs/region-reduction-30pyc-perfect-10rounds/rounds/round66/`
  （`OUTCOME.md` §5 六批判定 / §6 未采纳 / §7 下一轮线索，`logs/EVIDENCE.md` A–F，`batches/` 全部代理自产记录）。
