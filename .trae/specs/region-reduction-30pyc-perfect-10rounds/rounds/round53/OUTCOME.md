# Round 53 — 布尔链「同运算段出口一致性」(R53-A)

## 靶与根因（逐行取证）

靶族：`A or (B and C)` / `A and (B or C)` 被反编译成 `(A or B) and C` —— 运算重新结合，
语义改变。真实命中（G0 15 靶内）：

| pyc | 函数 | 落地前缺陷 |
| --- | --- | --- |
| `IQCommon/api/klinedata.pyc` | `_all_bars_of_cache` | `target_diff #24` |
| 同上 | `get_kline_by_date_new` | `target_diff #36` |
| 同上 | `get_multiminute_his_data_by_date` | `target_diff #272` |
| `IQCommon/util/replace_utils.pyc` | `log_request` | `target_diff #11` |
| `IQEngine/plugins/plugin_fly_data/strategy/strategy.pyc` | `tick_publish_thread` | `target_diff #44` |
| `IQEngine/utils/scheduler.pyc` | `run_weekly` | `target_diff #14` |
| `IQCommon/strategy/jq_trans_module.pyc` | 2 支（官方已 35/35，strict 内容缺陷） | — |

根因站点：`core/cfg/region_analyzer.py :: _detect_boolop_conditional_chain` 的运算元出口一致性
检验（`25147-25151` 取 `first_jump_target=chain[0]` 的短路目标、`prev_op=chain[-2][1]`，
`25231-25233` 命中即 `chain.pop(); break`）。带打印镜像核 `mirr_diag53` 在合成复现体
`wit53b/r53_13_or_and_return` 上实测：

```
[R53 append] cur=0  term=POP_JUMP_FORWARD_IF_TRUE ->38  op=or   chain=[(0,'or')]
[R53 append] cur=14 term=POP_JUMP_FORWARD_IF_FALSE->42  op=and  chain=[(0,'or'),(14,'and')]
[R53 append] cur=26 term=POP_JUMP_FORWARD_IF_FALSE->42  op=and  chain=[(0,'or'),(14,'and'),(26,'and')]
[R53 POP]    op=and prev=and firstJT=38 curJT=42 eq=False sbt=False normOR=False notOR=False
```

⇒ 第三运算元 `26` 被弹出。判据把 **不同运算段** 的出口拿来比：`A or (B and C)` 里 `A` 的短路
目标是 body(38)，而 `B`/`C` 同段的短路目标都是 exit(42) —— 跨段比较必然不等。弹出后
`chain=[(0,'or'),(14,'and')]` 又被 `25316-25441` 的 pure-or 判别改写为 `[(0,'or'),(14,'or')]`
（`25441 chain[-1]=(..., 'or')`），父 `IfRegion` 遂把 `26` 当作自己的第二个条件块 ⇒
`(A or B) and C`。

## 判据 R53-A（同层次、纯结构）

弹出前补一条「同运算段出口一致」豁免：从 `chain[-2]` 起沿**同标签**回溯得到末段头块，
若末段头的短路目标 `is` 当前运算元的短路目标，则该运算元是本段真成员，链必须保留；
否则仍按原逻辑弹出（嵌套 if 条件块交还父 `IfRegion`）。只读区域标签与块的后继关系，
不读名字/常量/偏移/指令数；未命中逐字节不变。落盘 `core/cfg/region_analyzer.py`
`25231-25262`（注释 `25231-25244` + 判据 `25245-25262`；原 `chain.pop()/break` 退到
`25263-25264`。单 hunk +32/−1，净 +31 行）。

## 门禁数字（候选臂 c53a 与落地核双跑，严格串行）

* **G0**（15 靶逐函数 strict + `wit53b` 电池）：靶面 strict 合计 `747/841 → 751/841`
  （`klinedata 53/63 → 56/63`、`scheduler 46/52 → 47/52`，其余 13 靶逐字不变）；
  电池 `MISMATCH=6 MATCH=4 → MISMATCH=4 MATCH=6`（`r53_13`、`r53_21` 转正）。
  另一电池 `wit53/`（链嵌 boolop 族，语料 0 命中，见 Round 53 移交）两臂 `7/12` 不变。
* **G1** 17 支低缺陷文件：`SAME=16 IMPROVED=0 REGRESSION=0 MOVED=1`（MOVED 支
  `replace_utils` strict `7/9 → 8/9` FIXED `log_request`）。
* **G2′** 143 支：`SAME=142 IMPROVED=0 REGRESSION=0 MOVED=1`，fully matched 112 → 112。
* **G3** 109 支：`SAME=108 IMPROVED=0 REGRESSION=0 MOVED=1`，fully matched 80 → 80。
* **G4** 全量 544 路径：`TALLY SAME=538 IMPROVED=0 REGRESSION=0 MOVED=6 ERR=0`，
  `files fully matched 485 → 485`。
* **G4′**（6 支受影响文件逐 code object strict）：`fixed=6 broken=0 changed=1`；
  每支 strict ok：`klinedata 53→56`、`jq_trans_module 61→61`、`replace_utils 7→8`、
  `strategy 25→26`、`scheduler 46→47`、`market_time 9→9` ⇒ 合计 `201 → 207`。
  唯一 changed 即 `market_time :: is_open`（见下）。
* **G5**：落地核对后重跑 6 支受影响 pyc ⇒ 产物与门禁臂 `build_c53a` **6/6 逐字节相同**；
  金丝雀 `fly/data/quotation.pyc` 官方 `143/143`、strict `148/150` 且缺陷两支名字逐字未变；
  `test_repros/round16_sink` 电池 `15/15 MATCH`。
* **G6** `batch --index pyc_index.json --all --round 53`：`verified_pyc 402 / failed_pyc 0`；
  全量重跑后仅 **6** 支 `*OK.py` 内容变化（＝ G4 的 MOVED 集合，无手改产物）；
  `pyc_index.json` 值域零变化（`git diff -U0` 非 `last_tested_round` 行 = 0），
  仅 402 条轮次戳 `52 → 53`，仍纯 CRLF 4553 行 141 019 B。
* **G7** `stats` 逐字：`total_pyc 402 / verified_pyc 402 / ok_pyc 375 / partial_pyc 27 /
  failed_pyc 0 / total_functions 5746 / matched_functions 5667 / cumulative_match_rate 98.63%`
  —— 与 Round 52 相同：**本轮官方尺零位移**。

## 收益如实入账

官方尺（`bytecode_diff`，容忍 jump/NOP）看不见本轮收益：6 支修的全是
**等长但运算重新结合**的内容缺陷（`target_diff`），官方按索引对齐比较故不报。
真实度量是 strict 尺：受影响 6 文件 `201 → 207`（+6 函数字节码逐条一致），
`broken=0`。这与 Round 51 的 R52-A、Round 52 的部分收益同性质，
按 [[project-official-vs-strict-gate-blindness]] 的口径不入任何率值。

## 字节面

`core/cfg/region_analyzer.py` `66553c66939e9e9242f4 → b10ee76b55754f09e945`
（1 689 673 → 1 691 897 B，CRLF 27 148 → 27 179、裸 LF 0、无 BOM，单 hunk +32/−1）；
`core/cfg/region_ast_generator.py` 逐字节未动（`c36cf1fe7dad68377c80`，3 011 895 B）。
`git status --porcelain core/` 仅 1 支。落地由 `land53.py` 把关：先在内存应用 spec
（锚点 `count==1`）并与通过全部门禁的臂 `mirr_c53a` 逐字节相同后才写盘。


## 否证与移交

* **R53-B 否证**：加「链只允许 1 个运算段边界」可表性合取（`_r53_boundaries <= 1`）后
  `scheduler::run_weekly` 的真修复被撤回（FIXED→无），而 `market_time::is_open` 的 +2 伪造
  依旧 ⇒ 判别式不是段边界数；`mirr_c53b` 与 `mirr_c53a` 在 `market_time` 上产物逐字节相同。
* **`fly/common/market_time.pyc :: is_open` 交 Round 54**：dis 地面真值是
  `(A and B) or (C and D)`（`184 IF_FALSE->210`、`208 IF_TRUE->258`、`232 IF_FALSE->316`、
  `256 IF_FALSE->316`）。检测器**不是**从 `A` 进入的：`A` 被父 `IfRegion` 占为条件，
  子链从 `B` 起（`B or (C and D)` 二段形，R53-A 因此命中）。保留 `D` 后严格缺陷从
  `target_diff #27`（等长、错结合）变为 `seq_len orig=67 decomp=69`（结合正确但函数尾
  `return False` 被 sink 逻辑折成 `else:`），strict ok 9/10 不变、官方 10/10 不变。
  开证点在发射侧「链汇合块逃出所在臂」，与 [[project-chain-tail-drop-witness]]、
  [[project-r16-lead-sink-collapse]] 同邻域。
* 电池余支（同一 `A or (B and C)` 族的其它形状）：`r53_14_and_or_return`(+2)、
  `r53_16_or_and_while`(−2)、`r53_17_neg_or_and`(+2)、`r53_22_or_and_in_loop`(+1)。
* Round 50 三元链 kwarg 线（`order_api :: future_order 101/93`、`option_order 83/74`、
  `base_order [target_diff] #136`）本轮未动。
