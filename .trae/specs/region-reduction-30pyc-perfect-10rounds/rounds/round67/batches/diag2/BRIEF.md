# Round 67 · diag2 · BRIEF（只读诊断代理）

工作目录 `D:/Temp/opencode/r67gate/diag2`。**仓库零改动**：不得写 `F:/Downloads/pythoncdc-main` 下任何文件
（包括 `core/`、`*OK.py`、`pyc_index.json`、`.trae/`、`test_repros/`）；所有产物写到本目录。
唯一允许的“写仓库”动作是读取（`h62.py build` 自带镜像==工作树断言，任何污染都会立刻失败）。
**不要跑 402 全量扫描** —— 那是集中验证方的职责（上一轮三支代理死在 150 轮上限，402 是主要开销）。

## 名下靶支（landed = 当前工作树 = R66 落地字节，中心已实测；逐函数读数见本目录 `targets.md`）
# diag2 targets (3 files, official gap 13, strict defects 17)

## fly/data/quote.pyc
   pyc: F:/Downloads/pythoncdc-main/site-packages/fly/data/quote.pyc
   official 70/81 (gap 11)   strict 74/89 (defects 15, missing 0, extra 0)
   OFF    build_current_period_df                      orig=115   decomp=108   hunks=5  first_diff=12
   OFF    check_frequency                              orig=121   decomp=120   hunks=1  first_diff=21
   OFF    check_limit                                  orig=330   decomp=311   hunks=2  first_diff=248
   OFF    get_individual_data                          orig=312   decomp=311   hunks=1  first_diff=156
   OFF    get_price                                    orig=230   decomp=232   hunks=0  first_diff=172
   OFF    get_real_from_zeromq                         orig=703   decomp=678   hunks=0  first_diff=660
   OFF    initImagedata                                orig=243   decomp=225   hunks=0  first_diff=190
   OFF    load_bars_from_hundsun                       orig=477   decomp=483   hunks=0  first_diff=410
   OFF    load_get_price                               orig=171   decomp=171   hunks=0  first_diff=1
   OFF    run_individual_transform                     orig=362   decomp=321   hunks=2  first_diff=263
   OFF    run_tick_socket                              orig=306   decomp=307   hunks=2  first_diff=228
   STRICT build_current_period_df                      [seq_len] orig=118 decomp=109
   STRICT change_his_to_backward                       [target_diff] #213 POP_JUMP_IF_TRUE 终点 orig=("'data'", 'LOAD_FAST') decomp=('None', 'POP_TOP')
   STRICT change_his_to_forward                        [target_diff] #241 POP_JUMP_IF_FALSE 终点 orig=("'preindex'", 'LOAD_FAST') decomp=(None, 'FOR_ITER')
   STRICT check_frequency                              [seq_len] orig=123 decomp=124
   STRICT check_industry_code                          [seq_diff] #159 orig=('0', 'CONTAINS_OP') decomp=('1', 'CONTAINS_OP')
   STRICT check_limit                                  [seq_len] orig=331 decomp=311
   STRICT get_individual_data                          [seq_len] orig=314 decomp=313
   STRICT get_price                                    [seq_len] orig=230 decomp=232
   STRICT get_real_from_zeromq                         [seq_len] orig=703 decomp=678
   STRICT initImagedata                                [seq_len] orig=245 decomp=225
   STRICT load_bars_from_hundsun                       [seq_len] orig=477 decomp=483
   STRICT load_get_price                               [seq_diff] #53 orig=('<JUMP>', 'POP_JUMP_IF_FALSE') decomp=('None', 'POP_TOP')
   STRICT run_individual_transform                     [seq_len] orig=364 decomp=321
   STRICT run_tick_socket                              [seq_len] orig=309 decomp=310
   STRICT run_tick_transform                           [target_diff] #135 POP_JUMP_IF_FALSE 终点 orig=("'self'", 'LOAD_FAST') decomp=("'len'", 'LOAD_GLOBAL')

## IQData/utils/common_func.pyc
   pyc: F:/Downloads/pythoncdc-main/site-packages/IQData/utils/common_func.pyc
   official 23/24 (gap 1)   strict 26/27 (defects 1, missing 0, extra 0)
   OFF    handle_exrights                              orig=276   decomp=268   hunks=1  first_diff=263
   STRICT handle_exrights                              [seq_len] orig=276 decomp=268

## IQEngine/plugins/plugin_system_matcher/matcher.pyc
   pyc: F:/Downloads/pythoncdc-main/site-packages/IQEngine/plugins/plugin_system_matcher/matcher.pyc
   official 16/17 (gap 1)   strict 16/17 (defects 1, missing 0, extra 0)
   OFF    match                                        orig=715   decomp=715   hunks=10 first_diff=517
   STRICT match                                        [seq_diff] #182 orig=('<JUMP>', 'JUMP') decomp=("'self'", 'LOAD_FAST')

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
- `quote.pyc` 的 `load_bars_from_hundsun` 上一轮由 P4 修到 hunk 3 段→0 段（`[477,524,3,507]`→
  `[477,479,0,471]`，orig=477）；本轮残余是 **过冲 +2** 与 R66 §7.3 记的
  `os.path.exists(DumploadDailyFile)` 裸表达式。`get_price`(230/232)、`initImagedata`(243/225)、
  `get_real_from_zeromq`(703/678)、`run_individual_transform`(362/321) 仍是大缺口。
- 严格尺在本支多出的 4 支 `target_diff`/`seq_diff`（`change_his_to_backward`、`change_his_to_forward`、
  `check_industry_code`、`load_get_price`、`run_tick_transform`）是**跳转终点/常量槽**问题，
  官方尺看不见（[[project-official-vs-strict-gate-blindness]]）；`change_his_to_forward #241` 是
  R25 起就登记在册的金丝雀级残余，不要顺手改坏它。
- `matcher::match` 的位移线索**已在册**：orig 指标 180..462（282 条、源码 219-232 行）被发到产物尾部
  （decomp 428..713），而 `if self._volume_limit:` 占了前槽；R63 的 chain-store 修复与该处无关
  （probe_align hunk 表逐字节相同）。⇒ 只能从**生成器的重排/线性化通道**下手，别再找归属判据。
- `IQData/utils/common_func::handle_exrights`（276/268，1 hunk，first_diff=263，尾部缺 8 条）
  上一轮已归因但判「无可落地判据」，并给了实测读数（round66 OUTCOME §6）；其孪生
  `IQCommon/util/common_func` 已由 R65-D5 双编辑推到 21/21，两尺都要读（[[project-duplicate-source-pycs]]、
  [[project-analyzer-generator-pair-inertness]]）。
- **BoolOp chain.pop 的历史代价**：analyzer 侧 `chain.pop` 曾同时买到 quote_handler 57/57 + crypto 严格 9/9，
  却把 klinedata 严格 −2（[[project-r64-boolop-chainpop-cost]]）。任何碰 BoolOp 链弹出的判据必须同时跑
  这两支见证。

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
