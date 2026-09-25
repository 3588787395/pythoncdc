# Round 67 · diag3 · BRIEF（只读诊断代理）

工作目录 `D:/Temp/opencode/r67gate/diag3`。**仓库零改动**：不得写 `F:/Downloads/pythoncdc-main` 下任何文件
（包括 `core/`、`*OK.py`、`pyc_index.json`、`.trae/`、`test_repros/`）；所有产物写到本目录。
唯一允许的“写仓库”动作是读取（`h62.py build` 自带镜像==工作树断言，任何污染都会立刻失败）。
**不要跑 402 全量扫描** —— 那是集中验证方的职责（上一轮三支代理死在 150 轮上限，402 是主要开销）。

## 名下靶支（landed = 当前工作树 = R66 落地字节，中心已实测；逐函数读数见本目录 `targets.md`）
# diag3 targets (3 files, official gap 6, strict defects 10)

## IQCommon/api/klinedata.pyc
   pyc: F:/Downloads/pythoncdc-main/site-packages/IQCommon/api/klinedata.pyc
   official 42/45 (gap 3)   strict 56/63 (defects 7, missing 0, extra 0)
   OFF    get_all_real_daily_kline                     orig=188   decomp=187   hunks=3  first_diff=26
   OFF    get_multiminute_his_data                     orig=479   decomp=478   hunks=3  first_diff=16
   OFF    kline_datetime_list                          orig=389   decomp=389   hunks=9  first_diff=228
   STRICT get_all_real_daily_kline                     [seq_len] orig=188 decomp=187
   STRICT get_all_real_minute_kline                    [target_diff] #54 POP_JUMP_IF_FALSE 终点 orig=("'system_log'", 'LOAD_GLOBAL') decomp=("'fq'", 'LOAD_FAST')
   STRICT get_history_common                           [target_diff] #41 POP_JUMP_IF_NONE 终点 orig=("'is_dict'", 'LOAD_FAST') decomp=("'fields'", 'LOAD_FAST')
   STRICT get_kline_by_count_new                       [target_diff] #161 POP_JUMP_IF_NONE 终点 orig=('0', 'LOAD_CONST') decomp=("'symbols'", 'LOAD_FAST')
   STRICT get_multiminute_his_data                     [seq_len] orig=481 decomp=482
   STRICT get_price_common                             [target_diff] #114 POP_JUMP_IF_NONE 终点 orig=("'frequency'", 'LOAD_FAST') decomp=("'is_dict'", 'LOAD_FAST')
   STRICT kline_datetime_list                          [seq_diff] #151 orig=('<JUMP>', 'POP_JUMP_IF_TRUE') decomp=('<JUMP>', 'POP_JUMP_IF_FALSE')

## fly/simtradding/flyAccount.pyc
   pyc: F:/Downloads/pythoncdc-main/site-packages/fly/simtradding/flyAccount.pyc
   official 21/23 (gap 2)   strict 21/23 (defects 2, missing 0, extra 0)
   OFF    _do_request                                  orig=436   decomp=443   hunks=2  first_diff=384
   OFF    init_connection                              orig=42    decomp=41    hunks=0  first_diff=25
   STRICT _do_request                                  [seq_len] orig=436 decomp=445
   STRICT init_connection                              [seq_len] orig=42 decomp=41

## IQData/api/api_base.pyc
   pyc: F:/Downloads/pythoncdc-main/site-packages/IQData/api/api_base.pyc
   official 24/25 (gap 1)   strict 26/27 (defects 1, missing 0, extra 0)
   OFF    get_history_df                               orig=1742  decomp=1719  hunks=14 first_diff=1277
   STRICT get_history_df                               [seq_len] orig=1742 decomp=1719

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
- `klinedata`：R63 记的 `_boolop_resolve_merge` 在 `get_kline_by_count` 给出 merge=374（真出口应为 172）
  **至今未动**，是本轮头号线索之一；同一函数严格尺 857/859。另一条 `get_price` 553/555 是 +2 过冲。
  注意 chain.pop 类判据对 klinedata 的历史负代价（[[project-r64-boolop-chainpop-cost]]）。
- `flyAccount::_do_request` [436,443,2,384]：R64 指名的 `_loop_build_if_with_exit_branches`（L10470）
  **已被 R65 的运行时计数器证伪**（该函数对 `_do_request` 调用 0 次）。真实机制是 **7 个
  `merge_context is None` 的 TernaryRegion 被降级为裸 `Expr`**，修复通道
  `_apply_r62... _apply_r23n6_return_promotion`（R65 时 L47636，现已下移）卡在自身 POP_TOP 测试上。
  ⇒ 从降级 + 提升守卫两处起手，不要重跑 loop helper。
- 该过冲是 R63-B4 成对引入的（b4c_402 与 p402_final 同行 `[436,443,2,384]`），单臂中性 ⇒
  任何候选必须在**成对**与**单臂**两种配置下都读数（[[project-analyzer-generator-pair-inertness]]）。
- `api_base::get_history_df` 上一轮归因完成但「候选：NONE」（round66 OUTCOME §6），要换判据入口才允许重开。

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
