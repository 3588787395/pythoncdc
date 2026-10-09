# T12-01 答案（纯测量票）：不存在能回答「这个入口是否已被发射」的现成台账

镜像 `D:/Temp/r141/wt`；基线 = 仓库当前字节（`region_ast_generator.py = 971df5e2c9cd7d0a`，
即 B133 落地 + r11-b159 纯注释；`region_analyzer.py = e926a54f17753b33`）。
仓库 `core/` 与 `site-packages/` 全程 0 项改动（每张脚本收尾 `shutil.copyfile(GEN, DST)` 复原镜像）。
探针惰性自证：每次装完探针先跑一遍，产物与封存产物**逐字节相同**（quotation `182759`、
realtime_event_source `20555`、handlers `9093` 三处均验证过）。

## 1. 三个问题，逐一用 A/B 读数回答

### Q1 兄弟臂子区域经循环体/其他路径发射时，有没有地方记下它的入口偏移？

**没有。** 实测（HEAD 字节 + `[R163]` 只打印 `_generate_if` 入口，惰性已自证）：
B158 候选在 quotation 里重派发并造成 16 单元回归的那批块，其入口偏移在 HEAD 的
`_generate_if` 记录中**根本不出现**，而它们所在的单元在 HEAD 是**绿的**：

| 块 | HEAD 是否经 `_generate_if` 发射 | HEAD 该单元状态 | B158 重派发后果 |
|---|---|---|---|
| `get_stock_exrights` @640 | 未出现（该 co_name 不在打印白名单，见 §3 的口径限制） | 绿 | 回归 |
| `one_prod_to_dataframe` @634 / @800 / @1202 / @1422 | **False**（不在 HEAD 的 entry 集合里） | 绿 | 回归 |
| `get_eps` @994 | **True** | 绿 | 回归（重复发射） |
| `get_eps` @358 | **False** | 绿 | 回归 |
| `clock_worker` @7972 | **False**（基线 R162 实测：无候选时全 run 无 `_generate_if entry@7972`） | 红（缺 110 指令体） | 被补发，产物 20555→20812，单元仍红 |

⇒ 结论：**这些绿单元的语句是被别的路径发射的**（不经 `_generate_if`，也不经
`_generate_region`，因为后者会在 `finally` 里把 id 记入 `self._generated_regions`，
而 B158 的入口偏移台账正是从 `_generated_regions` 反查出来的、仍然判成「未生成」）。
候选发射点包括 `_if_generate_elif_chain` / `_generate_boolop` / `_generate_ternary` /
`_loop_generate_*` 内的直连子区域渲染——具体哪一条要下一票逐单元读回，本票只证「现成台账答不了」。

### Q2 若无，记录点应在何处？

必须是**唯一漏斗**，不能是第二真相源：把「已渲染区域入口偏移」的登记放在
`_generate_region` 的 `finally`（已有 `_generated_regions.add(id)`）里**改成同时记入口偏移**，
并且把上面那些**绕开 `_generate_region` 的直连调用点**统一改为经 `_generate_region` 分派；
只加登记而不收口直连点，等于给同一判断留两套口径（违反 rules.md §1.5 C1/C3）。
这条收口不小：`grep -c "_generate_region("` 在 HEAD 上是 **108**（1 定义 + 107 调用）。

### Q3 evt 的 @7972 与 quotation 那批回归块，在「谁发射了它」上的可分事实是什么？

现有容器（`_generated_regions` id 集、`generated_blocks`、`generated_offsets`）**给不出**可分事实：
@994 在 HEAD 确被 `_generate_if` 发射，却仍被 B158 判为未生成并重发（说明该次发射没进任何台账）；
@7972 在 HEAD 完全没被发射，台账同样显示未生成 ⇒ 两者在台账上不可分。
可分的候选事实需要下一票读：@7972 的 `IfRegion` 的**父链**与其父区域 `body_blocks` 的认领关系
（`[R151]` 已给 owners：`IfRegion@7972(then=True)`、`LoopRegion@5598(×2)`、多个 IfRegion 的 then/else），
以及 @7972 的**前驱 @7706 是内层 FOR_ITER**（循环出口边）这一身份——quotation 的 @634/@800/@1202/@1422
是不是也挂在循环出口边上，必须逐块读回再判，不许凭同族类比。

## 4. 本票对既有记录的自我更正

上一份 `DIAG_B153_CLOCK_WORKER_REDISPATCH_FALSIFIED.md` §3 里「父链读数显示 quotation 命中是兄弟臂、
由循环体路径发射」这句在**方向**上得到本票证实，但依据要换成上表的 A/B 数（父链打印只覆盖了
`get_eps`/`one_prod_to_dataframe`/`clock_worker` 三个 co_name，`get_stock_exrights` 那行
`occurred=False` 是**打印白名单**造成的假阴性，不是事实）。
另记一次我差点犯的错：装候选后看到 `_generate_if entry@7972 occurred=True`，
若据此判「HEAD 本来就已发射 7972」就会把候选自己的派发当成基线事实——
必须用**无候选基线**（本票 R162/R163）单独跑一遍才算 A/B。
与 [[feedback-adjudicate-nondeterministic-reds]]、[[feedback-truncation-hides-diffs]] 同源。

## 5. 交给 T12-02 的唯一可行入口

按 Q2 收口需要动 107 个调用点，不是一轮之工。可行的窄道是先**只补台账**不改调用：
在 `_generate_region` 的 `finally` 里同时记 `entry.start_offset`（`_emitted_entry_offsets`），
并把候选条件从「id 不在 `_generated_regions`」换成「入口偏移不在 `_emitted_entry_offsets`」——
本票已证这仍不够（@994 走直连路径，不更新台账 ⇒ 依旧双发），所以 T12-02 若要落地，
必须**同时**把 clock_worker 那一形限定到「入口块的前驱是内层循环的 FOR_ITER/回边出口边」，
并把 quotation 的 @994 类同入口重复对象作为必测反例写进票面。
