# ADJUDICATION — R20-3 merge-landing family: CLOSED-FALSIFIED (no install), orchestrator re-measured

Engineer `r20m`（镜像 `D:/Temp/r20m`，票面只拥有 `core/cfg/region_ast_generator.py`）。
裁定时间：2026-10-10 02:34（其 DELIVER 写于 02:30，FIX 文档定稿 02:32，173 行）。

## 0. 交付面核验（不采信叙述，只信字节）

| 断言 | 我实测 |
|---|---|
| 交付文件不可安装（等于落地态） | `cmp -s core/cfg/region_ast_generator.py DELIVER/region_ast_generator.py` → **IDENTICAL_TO_LANDED_BASE**（sha16 两侧同为 `dff6e81a5f2ff9f6`；`diff` 改动行数 0；`py_compile` OK） |
| 只碰 generator | 镜像 `ast_generator_v2.py` = `beeaf14435e22922`、`region_analyzer.py` = `640d33a77dcb71c2`，与仓库一致 |
| 实时仓库未被污染 | `git status --porcelain -- core/` 空；三文件哈希 `dff6e81a5f2ff9f6 / beeaf14435e22922 / 640d33a77dcb71c2` |

结论：**本票 0 落地**，与它自己的声明一致（"install nothing"）。它先在 02:14→02:27 期间两次改动镜像字节
（`5d3ff1d071981e84` → `5c2acfa8b4bd5aac`），最后把镜像还原到落地态再交付，所以交付面是"还原后的基线"，
不是补丁丢失——这一点由它文档 §Stage 4 的 md5 论证与 `cmp` 同时成立。

## 1. 它对我票面前提的纠正（我逐条复核为真）

我派发的判据"arm/chain 尾巴要跳到 region 声明的 merge"在 generator 里**没有执行通道**：

- `:39406 merge_offset = region.merge_block.start_offset` 所在函数是
  `def _try_build_and_inner_or_pattern`（`def` 实测在 **:39338**）——不是尾巴跳跃的发射点。
  我用逐行扫描确认了归属（文件共 59535 行）。
- `merge_offset` 全文只出现 **6 次**，且都是"不满足就 `return None`"的模式否决；
  我按 `'jump'/'target'/'argval' = merge_offset` 形状 grep：**0 命中**。
  即没有任何一处把声明 merge 写进被发射的跳转目标。
- 机制性原因（我认可）：generator 产出的是 AST，`ast.BoolOp` / `ast.If` 不带跳转操作数，
  落地地址 100 % 由嵌套结构涌现。#37（`bar`/`strategy_universe`/`load_daily`）之所以能落地，
  是因为那里的声明 merge 恰好与一条既有语句边界重合，追加 `{'type':'Continue'}` 就等价于改落地。

⇒ 任何"从声明 merge 发射尾巴"的 generator 判据都属于 **fires-without-flips**，不值得再占门时间。

## 2. 三个残留为什么互相独立、且都不在 generator

| 单元 | 实测（工程师 `unit_diff.py`，与我此前读数一致） | 需要的归属改变 |
|---|---|---|
| strategy `Strategy.tick_worker_thread` 26/27，`hunks=0 landings=4` | 源是扁平 `elif A or B or C:`（C=链式比较 @536），产物 `elif not (A or B): if C:` | 要把 `@536` 从 `IfRegion entry=536` 的属主手里取出 |
| api_base `get_history_df` 27/28，`hunks=0 landings=2` | `if (not include) and (X or Y)` 被展成三层嵌套，短路出口被强制落到外层 skip 1254 | `region@992` 应拥有 `else=[1098]`，而 analyzer 把它给了 `IfRegion entry=1008` |
| broker 三件（`_process_tick_order`/`rzrq_credit_order`/`get_ipo_stocks`）各 1 个 landing | 分别早落 3/5/10 条指令，都在循环体内 | 同上，无落地常量可改；且三件全修好也只能 118/128→121/128，过不了 stage 3 的门 |

关键新事实（值得复用，勿再推导）：
- `region.inline_boolop_chains[id(cond_block)]` 在这两个条件块上实测 **`ibc_op=None ibc_blocks=[]`**，
  所以 `:20989 _main_ibc` 折叠与 `:21141 _disc_chain` 兜底（后者只构造 `op='and'`）**永远不会看到可折叠的链**。
- `_if_generate_elif_chain` 在整个 strategy 模块只进入 **1 次**（`L19D entry=210 ecs=[822]`）；
  512/982 处的 elif 残留来自 `_if_generate_normal` + orelse-elif 升级机制。
  ⇒ **任何只改 `_if_generate_elif_chain`（含 `:19454 elif_jump_target`）的判据对这一族是瞎的**，
  这条否证了我自己在 `d7e32be8` 里点名的候选分支。
- `_cond_block_branch_targets`（`:20098-:20128`）确认是"条件块 (jump, fallthrough) 提取器"，
  不是 arm 尾巴落地点——与我 `b43a7eba` 的自我纠正一致。

## 3. 它的基线与电池证据（Stage 1 PASS，我此前也独立测过其中数件）

镜像未打补丁时逐字复现封版读数：strategy 26/27、api_base 27/28、trade_live_broker 118/128、
real_quote 43/45、quotation 153/153、matcher 17/17、order_api 37/37；
六电池 `repro 9R / arm 0G3R / ccneg 3G1R / retbreak 2G2R(DRIFT=0) / orderapi 5G / tail 13G`。
探针惰性等步长已按其 `cmp` 记录采信（并保留了它自己抓到的一次 **非惰性**：
占位替换把 `D:/Temp/` 写成 `D:/Bemp/`，`open()` 抛错被宽 `except` 吞掉，产物少了 2444 字节的
`tick_worker_thread`——`cmp` 把它拦下，这正是本战役要求 `cmp` 证明探针的理由）。

## 4. 后续票的正确切法（本票不再重发）

残留 4 个单元族（strategy 1 + api_base 1 + broker 3 个 landing + get_tick_direction）的**共同根在 analyzer**：
`inline_boolop_chains` 缺条目 + `else=[1098]` 的属主错位，而这两者受
`rounds/round20/NOTE_T20_ORDERING_WALL.md` 记录的**区域生成顺序墙**约束
（`_identify_conditional_regions` 沿 `get_blocks_in_order()` 升序，父先于子）。
⇒ 下一票必须是 analyzer 侧（拥有 `core/cfg/region_analyzer.py`，generator 禁改），
且判据要能在**识别期**声明"该条件块的短路成员及其出口"，而不是事后修补；
否则按 §1 的结论它必然零翻正。

同时登记为**已否证轴**：
- "generator 里把 arm/chain 尾巴改成落向声明 merge"（无执行通道）；
- "`_if_generate_elif_chain` / `:19454` 是这一族的发射点"（每模块仅 1 次进入，残留不走它）。
