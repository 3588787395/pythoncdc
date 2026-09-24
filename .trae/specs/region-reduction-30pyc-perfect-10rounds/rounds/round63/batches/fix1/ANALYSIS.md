# Round 63 fix1 — 值语境链式比较前缀剥离（R63-B3 chainstore）

本文件由集中验证方（主代理）撰写：fix1 子代理在 04:29 停止工作，未留下 ANALYSIS.md。
以下每条数字都来自本工作区自产的记录文件（`fix1/dump/`）或集中重测（`r63gate/dump/`），
未做任何推测性补写。

## 交付物

`specs/cand_r63b3_chainstore.json` —— `core/cfg/region_ast_generator.py`，5 个 edit，
纯 LF 归一文本，落地后随合并 spec 一起进入工作树（合并 spec 共 9 edit / +474 行）。

| edit | 内容 |
|---|---|
| 1 | `_split_block_condition_prefix` 新增可选形参 `terminator_ops`（默认 `None`） |
| 2 | 新 helper `_r63b3_is_chain_cleanup_arm`（region_ast_generator.py:34216） |
| 3 | 新 helper `_r63b3_reduce_value_ctx_chain_store`（:34253） |
| 4 | `_generate_ternary` 调用点 A（:34602） |
| 5 | `_generate_ternary` 调用点 B（:34623） |

两个调用点都紧跟在 `_build_chained_compare_from_region_data(region)` 成功之后，
即只在「区域数据已经归约出完整链式比较」这一既有事实成立时才尝试语句级归约。

## 靶形态

`site-packages/IQEngine/plugins/plugin_system_matcher/matcher.pyc :: DefaultMatcher.match`
（L689 的 `if not (a <= b <= c):` 一类值语境链，链的前导段含语句，前缀划界原先无终止符放宽）。

## 见证（fix1 自测，arm 命名见 `fix1/dump/`）

```
landed.jsonl  matcher  16/17  ["match", 713, 689, 9, 524]
g1.jsonl      matcher  16/17  ["match", 715, 715, 10, 517]
```

orig 713 → 715（两条被吞指令复原），decomp 689 → 715（长度完全对齐），
真指令差 524 → 517。官方计数不变 16/17：残余是 `#182` 处的**顺序**缺陷
（`<JUMP>/JUMP` 对 `self/LOAD_FAST`），不是缺失——已由集中严格尺对 HEAD 的
defect-set diff 独立证实（`prevok/difftot.json`：matcher 的 `seq_len` 缺陷消失，
代之以一条 `seq_diff`）。

## 全量影响面（fix1 自测，402 支）

`dump/wl.jsonl`（402 条，arm=landed）与 `dump/wg.jsonl`（402 条，arm=g1）。
集中复核 `wl.jsonl` 与 `dump/p402_final.jsonl`（合并臂）**402/402 逐支 (matched, sha) 相同**，
两支合计 matched 函数 5677、完全匹配文件 382 —— 即本工作区的 landed 记录与集中
落地态记录互为印证。

`h62.py ab --a=fix1/dump/wl.jsonl --b=fix1/dump/wg.jsonl`：

```
REGRESSION history_data_source.pyc  18/18 -> 16/18
MOVED      trade_live_broker.pyc    fund_transfer [123,123,0,6] -> [123,88,1,57]
TALLY SAME=400 IMPROVED=0 REGRESSION=1 MOVED=1 ERR=0
```

**此对照不成立，已判定为基线错配，不作为回退依据。** 理由（字节级证据，非叙述）：

```
LANDING WORKTREE  sha 7ec41fa2f9cdd5d62c1a  size 3086600  getattr(region,=176  r63b3=3
fix1/mirr_g1      sha 082fa9910150acc9f2a7  size 3069504  getattr(region,=175  r63b3=3
central/mirr_f1   sha 082fa9910150acc9f2a7  size 3069504   ← 与 mirr_g1 逐字节相同
```

`mirr_g1` 于 04:08 构建，其基线是**落地前**的工作树（`getattr(region,` 计数 175 = 缺
R63-B4 Fix1 三元让位判据），而 `wl.jsonl` 的 `landed` 臂于 04:23 读取的是**落地后**
工作树（含 tern_slot + boolop_exit + fstail + chainstore）。两支相差的不是 chainstore，
而是整组合的其余四件。history_data_source 16/18 与 fund_transfer 123/88 正是那两件
各自负责的形状。正确口径见集中记录：以落地前 R62 基线 402 为 A、合并臂为 B，
REGRESSION=0。

`specs/cand_r63b3_revert.json` + `mirr_nog1`（04:27，sha 8654498ffdc74e5926d0，r63b3=0）
是「去掉 chainstore」的比较臂，其 note 自述 “comparator only, never landed”。
对应 `dump/wn.jsonl` 仅 185 条即中断，未跑完，故不采信其任何结论。

## 落地判据

chainstore 只是合并集的三分之一，落地判据用的是**合并臂**（tern_slot + fstail + chainstore
九 edit + analyzer boolop_exit）对轮初真基线的对照，不是本工作区那对错配臂。集中重跑
`h62.py ab --a=r62gate/dump/f4_402.jsonl --b=r63gate/dump/p402_final.jsonl`
（A=轮初 HEAD 96a5f310 落地态 402 支，B=`mirr_final` 402 支；`closeout63.py landproof mirr_final`
证得镜像 33/33 core 文件与工作树逐字节相同）：

```
TALLY SAME=398 IMPROVED=1 REGRESSION=0 MOVED=3 ERR=0   影响面 4/402
IMPROVED history_data_source   16/18 -> 18/18
MOVED    matcher               match [713,689,9,524] -> [715,715,10,517]
MOVED    trade_live_broker     fund_transfer [123,88,1,57] -> [123,123,0,6]
MOVED    flyAccount            _do_request [436,429,2,379] -> [436,443,2,384]
files fully matched: a=381 b=382
```

matcher 的这条 MOVED 即本工作区 g1 的贡献（指令数对齐，残余转为顺序）。
电池 `round63_b3/r63b3_chained_value_ctx_prefix.pyc` 在落地字节上 2/2 bad=0（见
`logs_g6_battery_landed.txt`）。据此落地。
