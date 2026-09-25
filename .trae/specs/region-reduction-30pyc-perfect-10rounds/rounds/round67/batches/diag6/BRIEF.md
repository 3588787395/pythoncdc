# Round 67 · diag6 · BRIEF（只读诊断代理）

工作目录 `D:/Temp/opencode/r67gate/diag6`。**仓库零改动**：不得写 `F:/Downloads/pythoncdc-main` 下任何文件
（包括 `core/`、`*OK.py`、`pyc_index.json`、`.trae/`、`test_repros/`）；所有产物写到本目录。
唯一允许的“写仓库”动作是读取（`h62.py build` 自带镜像==工作树断言，任何污染都会立刻失败）。
**不要跑 402 全量扫描** —— 那是集中验证方的职责（上一轮三支代理死在 150 轮上限，402 是主要开销）。

## 名下靶支（landed = 当前工作树 = R66 落地字节，中心已实测；逐函数读数见本目录 `targets.md`）
# diag6 targets (3 files, official gap 5, strict defects 9)

## IQCommon/strategy/wizard_quant_api.pyc
   pyc: F:/Downloads/pythoncdc-main/site-packages/IQCommon/strategy/wizard_quant_api.pyc
   official 51/53 (gap 2)   strict 52/56 (defects 4, missing 0, extra 0)
   OFF    calculate_di                                 orig=75    decomp=73    hunks=0  first_diff=45
   OFF    params_analysis                              orig=133   decomp=126   hunks=1  first_diff=117
   STRICT filter_desicion                              [seq_len] orig=179 decomp=181
   STRICT calculate_di                                 [seq_len] orig=81 decomp=79
   STRICT init_stock_pool_filter                       [target_diff] #33 JUMP 终点 orig=("'security_pool_info'", 'LOAD_FAST') decomp=("'final_stocks'", 'LOAD_FAST')
   STRICT params_analysis                              [seq_len] orig=134 decomp=128

## IQEngine/plugins/plugin_system_risk_calculation/__init__.pyc
   pyc: F:/Downloads/pythoncdc-main/site-packages/IQEngine/plugins/plugin_system_risk_calculation/__init__.pyc
   official 33/35 (gap 2)   strict 34/37 (defects 3, missing 0, extra 0)
   OFF    _on_publish_after_trading_end                orig=486   decomp=481   hunks=3  first_diff=33
   OFF    _save_testds_to_csv                          orig=71    decomp=68    hunks=7  first_diff=19
   STRICT _on_publish_after_trading_end                [seq_len] orig=488 decomp=481
   STRICT _on_set_positions                            [seq_len] orig=297 decomp=298
   STRICT _save_testds_to_csv                          [seq_len] orig=75 decomp=68

## fly/logger.pyc
   pyc: F:/Downloads/pythoncdc-main/site-packages/fly/logger.pyc
   official 29/30 (gap 1)   strict 62/64 (defects 2, missing 0, extra 0)
   OFF    write_logging_thread                         orig=113   decomp=113   hunks=1  first_diff=40
   STRICT write_logging_thread                         [seq_diff] #71 orig=("'msgs'", 'LOAD_FAST') decomp=('<JUMP>', 'JUMP')
   STRICT check_baseFilename                           [target_diff] #14 POP_JUMP_IF_TRUE 终点 orig=('1', 'LOAD_CONST') decomp=('0', 'LOAD_CONST')

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
- `wizard_quant_api::params_analysis` [133,126,1,117] 属 **try-body JUMP_FORWARD 家族**
  （与 `fileio_utils::write` 同一机制，见 diag4），counts 基本相等 ⇒ 查发射顺序而不是缺失。
- `risk_calculation`：上一轮 **D1**（generator 现 L44564
  `[R66-diag4 D1 augsub-continue-role]`）已把 `get_TradeMode_trades` 清空、33/35。残余 2 支是别的形状，
  新判据必须先与该处划清层次。
- `fly/logger`：R62 的 `plugin_system_log/__init__.pyc` 靶已 10/10 双尺全清（[[project-round-commit-scope]] 无关，
  线索在 rounds/round62/OUTCOME.md）；R64 的 `cand_fixa` 曾对该文件测得 28/30 且逐函数零变化 ⇒ INERT，
  不要沿同一判据入口重开。
- 本批三支缺口都小（1–2 指令）：优先做**严格尺**能对齐的那支，把它推到双尺 100% 就是本轮的「修到完全 OK」候选。

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
