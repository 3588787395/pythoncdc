# DIAG R15-16（T20 候选票）klinedata `get_kline_by_count_new`：全函数只差 **1 条指令**，差在 if 臂尾落点

## 1. 读数（landed 字节，2026-10-09 13:48）

`unit_diff.py site-packages/IQCommon/api/klinedata.pyc get_kline_by_count_new --all`

```
len orig=642 prod=642  delta=0            ← 内容与长度完全相同，纯落点残差
== replace orig[567..568 @2926] prod[567..568] del=1 ins=1
   - @2926  JUMP_BACKWARD                  （orig 该槽：目标 = 绝对偏移 1268）
   + @2924  JUMP_FORWARD                   （prod 该槽：目标 = 绝对偏移 3074）
hunks=1
```

`win_dis.py`（另行取 orig/prod 对齐窗口，只读就地产物）给出两侧同槽上下文与目标值：

```
orig[567] -> JUMP_BACKWARD 1268    ;   prod[567] -> JUMP_FORWARD 3074
prod  @2892 POP_JUMP_FORWARD_IF_FALSE 2926   （`if symbol_four not in dividends_stock`）
prod  @2894..@2920  LOAD_FAST fields / POP_JUMP_FORWARD_IF_NOT_NONE 2902 /
                    BINARY_SUBSCR / LOAD_FAST history_data_dict / symbol / STORE_SUBSCR   ← 真臂体（line 301）
prod  @2924 JUMP_FORWARD 3074        ← 就是这个槽；orig 此处是 JUMP_BACKWARD 1268
prod  @2926 LOAD_FAST dividends_all  ← else 臂体（line 303-306）
```

⇒ **该文件的唯一失败单元只差这一条跳转的方向与落点**；`klinedata` 63/64 → 64/64 即整文件翻绿。

## 2. 产物源码形状（就地 `klinedataOK.py` line 292-307）

```
292  if len(bars_ndarr) == 0:
293      history_data_dict[symbol] = EMPTY…
294      continue                       ← 前两个臂的 continue 发射正确（非差异槽）
295  elif need_exrights == 0 or …:
296      history_data_dict[symbol] = bars_ndarr…
297      continue                       ← 同样正确
298  elif fq is not None and … :
299      symbol_four = symbol.replace(…)
300      if symbol_four not in dividends_stock:
301          history_data_dict[symbol] = bars_ndarr if fields is None else bars_ndarr[fields]
302      else:
303          dividends = dividends_all[symbol_four]
304          dividend_dict = {…}
305          exrights_bars_ndarr = get_exrights_data(…)
306          history_data_dict[symbol] = …
307      continue
```

真臂（line 301）**没有**自己的 `continue`：产物让它的臂尾 `JUMP_FORWARD` 到 if/else 之后的共用 `continue`（@3074）；
原字节码里该臂尾是 `JUMP_BACKWARD 1268`，即**直接回到所在循环的头部**，不经过 @3074 的汇合槽。
⇒ 缺陷不是「丢语句」而是**该臂的出口身份**：原函数里这条臂是与 `continue` 等价的**硬退出臂**（异常终止迭代），
产物把它当成了会落入 if/else 汇合块的普通臂。

## 3. 判据方向（识别端，勿在生成端事后重排）

区域归约语义：IfRegion 若有一条臂的后继**不进入**声明的 merge，而是回到**包围它的循环头部**
（`for` 的迭代/条件头块），则该臂为硬退出臂，其 merge 身份应为循环头部——
这正是生成端 `[R3-Continue]`（`region_ast_generator.py:21378-21398`）要求
`region.merge_block is self._current_loop.header_block` 才发 `continue` 的前提；
本形里该 nested IfRegion 的 `merge_block` 被算成 if/else 之后的顺序汇合块（@3074 一侧），
于是走「臂尾正向跳到汇合 + 汇合处统一 continue」的形状。

开票前必须先做的两个测量（本票未完成的部分，禁止直接动 core）：
1. 只读 `RegionAnalyzer(cfg).analyze()` 独立进程普查：该 nested IfRegion 的
   `merge_block / then_blocks / else_blocks / condition_block` 身份，以及真臂块的**后继集合**
   （是否只有循环头、是否含 @3074 顺序块）。注意 [[in-analyzer-probes-perturb-cfg]]：
   判据读数只能在独立进程建 CFG，不得在 analyzer 内部打印。
2. 消融定位发射支：`_if_generate_elif_chain` 的臂 continue 支（`:19483-19573`）与
   `[R3-Continue]`（`:21378-21398`）各自单独旁路，确认哪一支产出 @2924 这条正向跳
   （依 [[ablate-builders-to-locate-emission-site]]：桩替换 + 产物字节差，不用行号 print）。

## 4. 共要件与冲突提示

- 判据落在**识别端 merge 身份**⇒ 涉改文件是 `core/cfg/region_analyzer.py`，与本轮 r19t2
  镜像工程师（api_base / strategy 的臂成员与 merge 身份）**同一文件**。
  必须等 r19t2 的 DELIVER 落地或明确否决后再施工，否则两份整文件交付互相覆盖。
- 前两个臂（line 294/297）的 `continue` 当前已正确 ⇒ 任何放宽都必须只作用于
  「臂的后继回到循环头且与声明 merge 不同」这一条，`repro_tail` 13 例
  与 `repro` 9 例（RED=9/9 是基线）为常驻护栏：判据若把它们改红即回退。
- 验收：`klinedata` 63/64 → **64/64**（整文件），`unit_diff … get_kline_by_count_new` 的
  `hunks=1 → hunks=0`，面板 17 文件零下降，门链 label vs 上一轮。
