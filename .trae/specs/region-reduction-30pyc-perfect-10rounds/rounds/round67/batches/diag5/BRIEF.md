# Round 67 · diag5 · BRIEF（只读诊断代理）

工作目录 `D:/Temp/opencode/r67gate/diag5`。**仓库零改动**：不得写 `F:/Downloads/pythoncdc-main` 下任何文件
（包括 `core/`、`*OK.py`、`pyc_index.json`、`.trae/`、`test_repros/`）；所有产物写到本目录。
唯一允许的“写仓库”动作是读取（`h62.py build` 自带镜像==工作树断言，任何污染都会立刻失败）。
**不要跑 402 全量扫描** —— 那是集中验证方的职责（上一轮三支代理死在 150 轮上限，402 是主要开销）。

## 名下靶支（landed = 当前工作树 = R66 落地字节，中心已实测；逐函数读数见本目录 `targets.md`）
# diag5 targets (3 files, official gap 7, strict defects 9)

## IQData/plugins/plugin_system_realquote/real_quote.pyc
   pyc: F:/Downloads/pythoncdc-main/site-packages/IQData/plugins/plugin_system_realquote/real_quote.pyc
   official 40/44 (gap 4)   strict 41/45 (defects 4, missing 0, extra 0)
   OFF    get_cache_l2_data_by_one                     orig=321   decomp=322   hunks=2  first_diff=197
   OFF    get_real_minute_kline                        orig=253   decomp=254   hunks=3  first_diff=197
   OFF    get_tick_direction                           orig=259   decomp=258   hunks=3  first_diff=102
   OFF    one_prod_to_ndarray                          orig=605   decomp=607   hunks=5  first_diff=424
   STRICT get_cache_l2_data_by_one                     [seq_len] orig=321 decomp=322
   STRICT get_real_minute_kline                        [seq_len] orig=253 decomp=256
   STRICT get_tick_direction                           [seq_len] orig=259 decomp=260
   STRICT one_prod_to_ndarray                          [seq_len] orig=606 decomp=608

## IQEngine/plugins/plugin_fly_data/fly_api/order_api.pyc
   pyc: F:/Downloads/pythoncdc-main/site-packages/IQEngine/plugins/plugin_fly_data/fly_api/order_api.pyc
   official 32/34 (gap 2)   strict 33/36 (defects 3, missing 0, extra 0)
   OFF    future_order                                 orig=101   decomp=92    hunks=2  first_diff=36
   OFF    option_order                                 orig=83    decomp=73    hunks=3  first_diff=39
   STRICT base_order                                   [target_diff] #136 POP_JUMP_IF_TRUE 终点 orig=("'order_obj'", 'LOAD_FAST') decomp=("'生成订单，订单号:{order_id}，可转债代码：{symbol}，数量：{side}{share}'", 'LOAD_CONST')
   STRICT future_order                                 [seq_len] orig=101 decomp=93
   STRICT option_order                                 [seq_len] orig=83 decomp=74

## IQEngine/utils/scheduler.pyc
   pyc: F:/Downloads/pythoncdc-main/site-packages/IQEngine/utils/scheduler.pyc
   official 44/45 (gap 1)   strict 50/52 (defects 2, missing 0, extra 0)
   OFF    run_daily                                    orig=77    decomp=71    hunks=0  first_diff=56
   STRICT run_daily                                    [seq_len] orig=84 decomp=75
   STRICT func_wrapper                                 [seq_len] orig=219 decomp=215

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
- `real_quote`：上一轮 diag3 的 analyzer 判据已落地（analyzer 现 L20949
  `[R66-diag3 value-context chained-compare gate]`），40/44，`get_cache_l2_data` 双尺全对齐。
  残余 4 支里，`get_real_minute_kline` / `get_tick_direction` / `get_all_real_daily_kline` /
  `kline_datetime_list` 上一轮全部判「候选：NONE」并给排除证据：前两支**纯位移**（删除区间与插入区间同尺寸同
  跳转目标），`kline_datetime_list` 纯次序颠倒（区域图正确），`get_all_real_daily_kline` 是编译器重入块的产物复制
  （源码无对应构造）。⇒ 位移族请从**生成器重排/线性化通道**统一处理，别按文件分头做（[[project-r64-matcher-displacement-lead]]）。
- **`r66d3_pred::v6` 是本批的现成复现**：判据 (d) 为不退化「头块带前导已完结语句」而保留落地读数
  （synth 电池里现在仍是 2/3，`['v6', 36, 34, 2, 16]`）。要做成，必须让撤销动作对「头块内的前导语句」做
  **同层拆分**而不是整体拒绝 —— 这是 analyzer L20949 那条判据的直接后续，属于本批名下。
- `order_api`：R50 起就钉死的 `_try_build_ternary_kwarg_call` kwarg 槽位 bail + 只向前走链；
  上一轮复核「提升分支在 L47665/L47668 提前 bail、POP_TOP 测试 0 命中」，行号现已漂移，必须 grep 重取。
  见 [[project-r50-ternary-kwarg-bail]]。
- `scheduler`：`run_daily` [77,71,0,56] 已被 R65 判为 **cellvar 降级、在区域层之外**，
  **禁止**再花批次攻它（[[project-r65-diag5-leads]] 第 3 条）。

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
