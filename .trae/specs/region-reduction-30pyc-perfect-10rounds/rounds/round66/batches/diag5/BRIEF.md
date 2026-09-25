# Round 66 · diag5 · BRIEF（只读诊断代理）

工作目录 `D:/Temp/opencode/r66gate/diag5`。**仓库零改动**：不得写 `F:/Downloads/pythoncdc-main` 下任何文件（包括
`core/`、`*OK.py`、`pyc_index.json`、`.trae/`）；所有产物写到本目录。唯一允许的“写仓库”动作是
读取（`h62.py build` 自带镜像==工作树断言，任何污染都会立刻失败）。

## 名下靶支（landed = 当前工作树 = R65 落地字节，已实测）
- `IQCommon/util/trade_info_utils.pyc` **38/40**  matched=[["get_trade_list", 339, 323, 14, 148], ["trade_operation", 304, 302, 2, 40]]
- `IQCommon/util/fileio_utils.pyc` **12/14**  matched=[["acquire", 96, 93, 3, 52], ["write", 637, 637, 4, 519]]
- `IQEngine/utils/scheduler.pyc` **43/45**  matched=[["get_checked_time", 106, 106, 0, 43], ["run_daily", 77, 71, 0, 56]]
- `IQCommon/strategy/wizard_quant_api.pyc` **51/53**  matched=[["calculate_di", 75, 73, 0, 45], ["params_analysis", 133, 126, 1, 117]]
（全路径见本目录 `targets.txt`。）

## 目标与交付（按此优先级，务必边测边写进 `FACTS.md`）
0. **先**把本目录 `dump/landed.jsonl`、`dump/battery_landed.jsonl`、`dump/canary_landed.jsonl` 用
   `--arm=landed` 各跑一遍（每条 <120 秒），确认与下面基线逐支相同；不一致就停下并写进 FACTS.md。
1. 对每个残余函数：先跑**归一化 hunk 表**（`nhunks.py <pyc> build_landed/<product> <fn> --ctx=3`；
   跳转目标归一为 `J`、嵌套 code object 常量归一为 `CODEOBJ`），据此判定「缺语句 / 多语句 / 纯换位」，
   并把 orig 与 decomp 的偏移区间写进 FACTS.md。
2. 归因到 `core/cfg/region_ast_generator.py` 或 `core/cfg/region_analyzer.py` 上**当前落地字节**的
   具体函数与行号（用 `grep -n` 实测，不要引用上一轮的旧行号），并给出该区域的同层次字段证据
   （`regdump.py`、只读探针、`sys.settrace` 计数器均可）。
3. 写一个 **≤15 行的合成复现**（`synth/xxx.py` → 编译成 `.pyc`，加进本目录一个新 `txt` 名单），
   证明它在 landed 上复现同一形状。**没有复现就不许提交 spec。**
4. 交 **一份** spec（`specs/cand_r66_<名>.json`，单文件单锚点，anchor 在 LF 归一文本里 `count==1`），
   判据必须是**同层次结构身份**（识别条件 / 归约方式 / AST 映射三要素写进补丁注释），
   禁止：按函数名/文件名/偏移/阈值匹配、`region.entry in r.blocks` 型跨区域跨层次包含、
   把 `self` 当帧内临时变量的新增状态、以及任何「不发射/直接抑制」式取巧。
5. 实测三组并写进 FACTS.md：`--arm=<cand>` 的 targets / battery / canary，再用
   `h62.py ab --a=dump/landed.jsonl --b=dump/<cand>.jsonl`（battery、canary 同）给出
   SAME/IMPROVED/REGRESSION/MOVED/ERR。**canary 4 支 sha 必须逐支不变；battery 24 支必须不比下面基线差。**
6. 若 1-5 全过，再跑 402 全量分片（`D:/Temp/opencode/r65gate/all402.txt`，`--nshard=4 --shard=0..3`，
   每片 <200 秒）并给出 A/B。跑不完也要在 FACTS.md 写清「未测」二字，禁止把未测说成无回归。

## 基线（中心已实测，直接复放校验）
targets 见上；battery 24 项（含 5 支 R65 新见证）：
合计 matched=91/104
  r63_ft.pyc                                  2/2  []
  r63_ft2.pyc                                 2/2  []
  r63_ft4.pyc                                 2/2  []
  probe_r63b2_cases.pyc                       7/9  [["c6_elif_try_then_more", 50, 50, 1, 15], ["c8_elif_chain_only", 31, 33, 1, 15]]
  probe_r63b2_cases2.pyc                      7/9  [["d2_elif_notry", 44, 45, 1, 28], ["d8_elif_try_chain_or_plain", 51, 50, 1, 6]]
  repro_r63b2_tail_cmp_return.pyc             2/2  []
  r63b3_chained_value_ctx_prefix.pyc          2/2  []
  r63b4_tern_in_elif_chain.pyc                3/3  []
  r63b5_w1.pyc                                1/2  [["init_connection", 42, 41, 0, 25]]
  r63b3_chainstore_prefix.pyc                 2/2  []
  r63b4_cond_boolop_stmt_steal.pyc           13/13 []
  r64d1b_closed_exit_prefix.pyc               2/2  []
  r64d1b_sibdispatch_attempt.pyc              4/4  []
  r64d2_chain_yield_sibling_entry.pyc         2/2  []
  r64d2_valuectx_consumer.pyc                 2/2  []
  r64d3_postif_join.pyc                       2/2  []
  r64d4_boolop_poptop_merge.pyc               3/3  []
  r64d4_deferred_prefix.pyc                   3/3  []
  r64d5_contsink.pyc                          1/2  [["probe", 122, 122, 1, 9]]
  r65_trytail.pyc                             8/9  [["p5", 33, 30, 2, 20]]
  r65_trytail_w.pyc                           8/8  []
  fs2.pyc                                     5/10 [["v1", 13, 11, 0, 3], ["v3", 15, 11, 0, 14], ["v6", 15, 11, 0, 5], ["v7", 24, 24, 0, 1], ["v8", 33, 23, 0, 28]]
  fsrepro.pyc                                 6/7  [["m_b", 39, 35, 0, 34]]
  r65d5_probe.pyc                             2/2  []
canary 4 支：
  quotation.pyc            143/143 sha=4d41187e356544e0
  market_time.pyc           10/10  sha=af77224b34b203c4
  datetime_func.pyc         26/26  sha=e711b8ea86d49a15
  datetime_func.pyc         25/25  sha=9d09af09249da177

## 工具与纪律
- 一律 `python -X utf8`；**禁止设置 PYTHONIOENCODING**；每条命令必须 <300 秒（长任务自己分片）。
- `h62.py` 用法：`build --spec=specs/x.json --dst=x`、`run --arm=landed|x --list=targets.txt --out=dump/x.jsonl`、
  `ab --a=... --b=...`。产物名 = `site-packages/` 之后路径 `/`→`__`、`:`→`_`、`.pyc`→`OK.py`。
- 落地代码里的本轮相关标记（用 `grep -n` 在当前字节上取实际行号）：generator
  `[R65-diag1-A try-body-tail-return-none]`、`[R65-D5-A]`、`[R65-D5-B]`、`[R65-d3 C1a]/[C1b]/[C1c]`、
  `[R64-b2]`、`[R64-B2]`、`[R64-D4-B]`、`[R64-B1 sibling merge-entry dispatch]`、`[R64-D4-A]`；
  analyzer `[R65-diag4 n1 operand-rejoin exemption]`、`[R64-diag1 closed-shared-exit-prefix]`。
- **轮次上限 150 轮**：R65 有三支代理死在 150 轮且没留下任何报告。所以第 0 步起就持续写 FACTS.md，
  即使只做到第 2 步，FACTS.md 也必须是完整可复放的读数记录。
- 若判定本批某支「无可落地判据」，就在 FACTS.md 明确写 **候选：NONE** 并给出排除证据（实测读数），
  不要为交差而交 spec。

## 已知情报（来自 R65 归档与集中验证）
- **R65 diag5 交代的同族**：`scheduler::get_checked_time [106,106,0,43]`、`fileio_utils::write [637,637,4,519]`、`wizard_quant_api::params_analysis [133,126,1,117]` 三支同指一个形状 —— try 体内一个 `JUMP_FORWARD` 跳出 `try ∪ handlers`，该块必须被**调度进 try 体内部**而非其后（R65 已落地的 `[R65-diag1-A try-body-tail-return-none]` L26483 只处理了「体尾 return-none 终止块」这一子集）。这是本轮最值得做成**一条**判据的家族。
- `scheduler::run_daily [77,71,0,56]` R65 判为 cellvar（闭包变量跨区域读写）退化，区域层判据修不动 —— 只做一次复核，不要投第二份预算。
- `trade_info_utils::get_trade_list 339/323 jd14` 与 `wizard_quant_api::calculate_di 75/73 jd0` 未诊断过。

上一轮全记录：`F:/Downloads/pythoncdc-main/.trae/specs/region-reduction-30pyc-perfect-10rounds/rounds/round65/`
（`OUTCOME.md` §5 代价与 §6 移交线索、`logs/EVIDENCE.md`、`logs/partial17_after_r65.txt`）。
