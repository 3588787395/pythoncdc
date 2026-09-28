# R75 · diag1（只读诊断）BRIEF —— 71 单元子机理归属 + 9 inside-try 逐行根因

## 0. 使命与工作区

工作区：`D:/Temp/opencode/r75gate/diag1`；基线 HEAD = **`982cd398`**。
**只读批**：不写任何 spec、不改 repo、不手改 `*OK.py`。产出 `FACTS.md` + `dump/` 探针读数，
为 fix1/fix2/fix3 的判据归属提供中心可复核的证据。

## 1. 输入

- `filecat.json`（34 文件 / 71 单元，逐单元 `failures` 列表）
- `../center/fam75.json`（真实 ruler verdict 聚类：F-ABSORB 61 / F-PAD 8 / F-POLARITY 1 / F-OTHER 1）
- `../center/dump/{firstdiv75,exctable_diff75,tryverdict75,crosstab75}.txt`
- 基线 G3v：`rounds/round74/logs/gate/G3v_pycverify_r74.json`

## 2. 必答问题

1. **61 个 F-ABSORB 单元子机理归属**（逐单元给证据行，四选一 + 其他）：
   a. 共享尾/共享 else 被吸收进上层 region；
   b. 孤儿子块未发射（orphan child，R74 修了一类，是否还有未覆盖形态）；
   c. 跳转 target 落在不同 instr（region 边界/布尔短路归约差）；
   d. 纯位移（target 同、offset 平移 → Σ|Δ| 应不升）。
   产出 `dump/submech75.txt`（file/unit/family/verdict/lenA/lenB/firstA/firstB/class）。
2. **9 个 inside-try 单元逐行根因**：原 pyc 该函数的 try 结构（几层、handler 几个、共享尾在哪）
   vs 产品 AST（`ast.Try` 层级、handler 落点），给出**行级对照**（利用 fam75 的 lineA/lineB 与
   `exctable_diff75` 的条目差）。产出 `dump/inside75.md`。
3. **`real_quote.get_tick_direction` 解剖**（R74 拒收点）：absj3/absj9 各改了哪几处 hunk、
   第 3 个 hunk 的字节级内容、为什么 absj 能过而 +try7_9/+try7_10d 过不了。
   产出 `dump/tick_direction75.md`（供 fix1 定规避）。
4. **对照组口径**：`et>0` 但首分歧在区外的单元（`klinedata.get_kline_by_count_new`、
   `trade_info_utils.kill_trade_process`/`get_trade_status`、`quote.check_frequency`/
   `run_individual_transform`、`ptradeAccount.order_response_order_update`）——
   给出「try 是载体还是根因」的判据读数。
5. **与 R74 已知残留的对应**：trade_live_broker 13 / quote 11 / trade_info_utils 5 三个头部文件
   是否存在共同子机理（跨文件同构模式）？给聚类结论。

## 3. 硬规则

- 全程只读 repo；不落地；每条命令 <300s；探针**局部 import** 避免 try 内 NameError。
- 探针产物一律写 `D:/Temp/opencode/r75gate/diag1/dump/`；`FACTS.md` 放工作区根。
- 读数必须原始可复核（附命令与文件路径），不得只给结论。

## 4. 交付

`FACTS.md`（读数表 + 与 fix1/fix2/fix3 重叠面 + 原始文件索引）、`dump/submech75.txt`、
`dump/inside75.md`、`dump/tick_direction75.md`、其余探针输出。
