# DIAG/FIX B141 — 循环「终块落点」发射责任：判据过捕，本票证伪并回退

票号 **B141**（接替在每日用量上限中断死的 B136b；B136b 只建好镜像 `D:/Temp/r136b/wt`＝仓库字节，未产出补丁，
其 `DIAG_B136_LOOP_EXIT_LANDING.md` §1–§5 全是 TO FILL）。宿主事实取自我自己的落地记录
（commit `82aa801a`）：`handlers :: TWHThreadController._target` 的 `@404`
＝ `LoopRegion(entry=90, WHILE, header=104, cond=90, back_edge=390, else_blocks=[408])` 的**普通成员**，
既不在 `body_blocks` 也不在 `else_blocks`，零后继，唯一前驱是回边块 `@390`，内容 `LOAD_CONST None; RETURN_VALUE`
两条从未发出（orig 199 指令 / 产物 197）。

**镜像**：`D:/Temp/r141/wt`（`core bytecode parsers utils scripts pycdc.py` 共 98 个 `.py` 逐文件 sha256 对齐仓库，
`files=98 bad=0`）。仓库 `core/` 全程未动（结束时复核：`region_ast_generator.py = e9a8f65f6451bcc8`、
`region_analyzer.py = e926a54f17753b33`）。判据尺 `scripts/pyc_verify.py single`。

## 1. 施工点（读代码得到，非猜）

`core/cfg/region_ast_generator.py:5361-5374`（`_generate_region` 的 loop 分支，紧接
`result = self._loop_generate_for/_loop_generate_while(...)` 之后）把循环区域的**剩余成员块**
一律 `self.generated_blocks.add(block)` —— **只登记，不发射**。这正是原则 2 禁止的形态
（成员关系即发射责任）。同一分支上方已有先例装配序 `[_result] + _post_yf_stmts`（`_post_yf_stmts`
见 `:5175/:5240/:5252/:5315`），所以「在 While/For 节点之后追加兄弟语句」是本方法既有契约，不是新通道。

## 2. 判据（已写入镜像，字节 `2aa23a5a453b94cc`）

`[r11-b141-loopterm]`：块 ∈ `region.blocks` ∧ ∉ `body_blocks ∪ else_blocks ∪ break_blocks ∪ init_blocks`
∧ ∉ {header, condition, back_edge, entry, merge, exit, for_iter_setup, for_iter_exit} ∧ 未被登记 generated
∧ **零正常后继且零异常后继** ∧ **全部前驱都在本循环块集内** ⇒ 用 `_generate_block_statements` 发射，
并以 `[result] + 落点语句` 返回；判据不成立即走原 `return result`（C3 守卫封闭）。

## 3. 实测读数（同镜像同字节 A/B）

| 文件 | HEAD | B141 | 结论 |
|---|---|---|---|
| `IQCommon/logger/handlers.pyc` | 29/30（红 `_target`） | **28/30**（红 `_target` **未翻正** ＋ 新红 `TWHThreadRotatingFileHandler._target`） | 目标单元零收益，另有一处过捕 |

即：**该判据没有命中 @404 所需的通道，却把兄弟单元打红**。两条候选解释（都待下一票读回，本票不再追）：

1. `@404` 走到发射时命中 `BlockRole.LOOP_EXIT → 返回 []`（发射器 `region_ast_generator.py:9240`、
   `:52760` 两处 `if block_role == BlockRole.LOOP_EXIT`，文档 `:51228` 明写「循环退出填充块不产生语句」），
   所以我调用 `_generate_block_statements` 得到空列表 ⇒ 登记照旧、语句照旧不发。
2. 新红来自另一条本应「不发」的终块被发了出去（重复发射）。

## 4. 裁决与后续

本票**证伪并回退**：镜像 `region_ast_generator.py` 已复原为仓库字节（`e9a8f65f6451bcc8`），
补丁字节留在 `D:/Temp/r141/b141_falsified_generator.py`（`2aa23a5a453b94cc`）。
下一票的正确顺序是**先读回 `@404` 的 `BlockRole` 与 `_generate_block_statements` 的返回值**，
再决定是修「LOOP_EXIT 抑制」还是修「收尾扫只登记不发射」——
两者是不同通道，把收尾扫当成唯一通道是我这次的前置误判（`git log` 记录的角色普查没有覆盖 role 表）。
读 role 表必须用**无副作用**探针（见 `DIAG_B139C_*.md` §3：在分析器内读 `successors`/`get_block_by_offset`
本身会改产物），只读 `block_roles` 字典与已绑定局部量。

同时登记：本轮（round 11）`realtime_event_source.clock_worker` 的同族但**不同通道**事实——
`@7972`（`if persist_flag is not False:` 头，110 指令体）与 `@8170` 在真实流水线的
`_generate_block_statements` 普查里**从未被 dispatch**（84 个被 dispatch 的块入口里无这两个偏移），
而它俩是外层 `LoopRegion(entry=5598)` 的 `body_blocks` 成员、是 `IfRegion(entry=7972)` 的 entry、
其前驱含内层 `LoopRegion(entry=7706)` 的 `FOR_ITER` 出口边 ⇒ 属「父区域在子循环之后未继续线性发射」，
与本票的「循环自身终块成员」不是同一判据，不得混在一张票里顺手改。
