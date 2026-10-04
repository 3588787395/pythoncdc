# REVIEW3 — 批次 C（12d7ddb9）只读对抗审计

- 审计对象：`git show 12d7ddb9 -- core/cfg/region_ast_generator.py`（[B71] 边类型封闭 + `_generate_try` docstring 六要素；另含 `site-packages/fly/common/op_stationOK.py` 再生成 1 行恢复 `cls.lock.release()`）
- 基线（修复前）对照对象：父提交 `616437c3`（批次 B 在位、批次 C 未在位），经 `git worktree add --detach` 隔离运行，core/ 零触碰，审计结束后 worktree 已删除
- 环境：Python 3.11.7；工具链 `pycdc.py -o <v>OK.py <v>.pyc` → `scripts/pyc_verify.py single <v>.pyc`
- 锚点：修复后 HEAD `site-packages/fly/common/op_station.pyc` single = **21/21，100.00%**（本审计独立复跑）

## §1 清单逐项结论

### 1. 判据合法性（I.4）— PASS

修复后守卫仅使用以下判据（region_ast_generator.py:30137-30148）：

| 判据 | 来源 | 白名单归属 |
|---|---|---|
| `getattr(_p, 'predecessors', None)` | basic_block.py:65 | 后继/前驱集合 |
| `getattr(_p, 'exception_successors', None)` | basic_block.py:67，cfg_builder.py:297 填充 | 异常边（明列白名单） |
| `getattr(_p, 'loop_header', False)` | dominator_analyzer.py:343-362（`_classify_loop_headers`：块内含 FOR_ITER/GET_ANEXT 指令 + 回边目标集合） | 块级结构事实：由「块内 opcode」+「后继集合/回边」两个白名单源派生，非跨层反查（REVIEW2 对 B2-B4 的既有先例同口径） |
| `region_analyzer.get_region_for_block(_b71_lh)` + region_type 含 'LOOP' | region_analyzer | 区域成员关系 |

黑名单逐项核查：无名字白名单；无 start_offset 魔法阈值（新 hunks 中 offset 仅出现于集合成员比较）；无跨层 `X.entry in Y.blocks` 反查（新增行未引入）；无新增 self 跨方法状态（`setattr(_b71_host_loop, 'else_blocks', ...)` 为批次 B 既有移交通道）；方向为恢复发射而非「以少发射换绿」；无硬编码深度/计数上限。**PASS**。

### 2. 边类型封闭正确性 — PASS

- `exception_successors` 唯一填充点：`cfg_builder._connect_exception_edges`（cfg_builder.py:276-298），按 3.11 异常表 entry（start/end/target）对覆盖区间内每个 try_block 执行 `add_successor(handler_block)` **且** `exception_successors.add(handler_block)`。即「exception_successors = 异常表边（target = handler 入口）」与修复表述一致。
- 「finally 异常副本入口（PUSH_EXC_INFO 块）经异常边持有 try 体内循环头作前驱」事实成立：try/finally 的异常表覆盖整个 try 体，体内任意块（含 while/FOR_ITER 循环头）的 exception_successors 均含副本入口；副本入口前驱含循环头但**全部经异常边**。修复后 gate 要求 `fb ∉ pred.exception_successors`，副本入口被正确排除、留在 finally_blocks 作 finalbody 语句源（变体 v4 实证：修复前 `finally: pass` 蒸发 → 修复后语句保留）。
- 真正的循环出口块（FOR_ITER 出口边/循环头正常边后继）仍被认领：循环头的 exception_successors 只含异常表 target（副本入口），不含正常出口块，故 `fb ∉ pred.exception_successors` 对真出口块成立（v1/v3 实证认领后 MATCH）。
- 残余理论边界（登记，非缺陷）：若某块同时是真循环出口又是异常表 target（两角色合一），修复后守卫将拒绝认领。实际字节码中两角色 offset/职能分离，未观测到实例。

### 3. 守卫对称性 — PASS

- any() 门：`any(A ∧ B)`，A=`p.loop_header`，B=`fb ∉ p.exception_successors`；内层扫描跳过条件：`¬A ∨ ¬B → continue`，处理条件恰为 `A ∧ B`。两处互为精确逻辑补，无「门放行而内层全跳过」或反向裂缝；门通过时内层必在 predecessor 集合中找到同一合格前驱并选宿主（`break`）。
- `or ()` 防御：`BasicBlock.__init__`（basic_block.py:67）恒初始化 `exception_successors = set()`，真实块不会缺属性；属性缺失/None → `()` → `fb not in ()` = True（按正常边计，等同修复前对该块的行为）；空集 falsy → `()`，成员语义不变。对真实块零行为改变。

### 4. docstring 六要素真实性 — PASS（附 1 条措辞 nit）

- ① 异常表界定/双副本：与 cfg_builder 异常表模型及 W11-A 注释（28799-28812）一致。✓
- ② 归约顺序：与代码序一致（28888 [B75] 前置归约 → handler 快照 → try 体循环 → handler 臂 → else/cleanup → finalbody，30097/30100 两分支）。✓
- ③ 唯一归属判定：`block_to_region` 权威守卫实存于 post-try 各收集循环（29060-29062、29226-29228），「post-try 收集拒绝非本域块」属实；[B71]「三重释放移交」= else_blocks 追加（30154）+ finally_blocks.remove（30157）+ region.blocks.remove（30161），逐行核实；「异常副本入口不构成出口证据、必须留在 finally_blocks」与 30137-30139 gate 语义一致。✓
- ④ 嵌套即抽象节点：与 30178-30199 派发路径一致。✓
- ⑤ 入口引用语义逐句核实：entry 块引用派发（30182-30188，`entry is fb` 回溯）；`handler_entry_blocks` 实存并多处使用（3165、26916、27344 等）；W11-A 正常副本锚点 = `_find_finally_normal_copy_blocks`（定义 28415，调用 28995）；孤儿 finally 帧 `_identify_empty_body_finally_regions`（region_analyzer.py:9568，调用 1462）。无虚报。✓
- ⑥ 流程与 C 条款：C1 判据枚举属实；C2 批次 C 未新增任何 self 状态（diff 仅 docstring + 守卫两处）；C3「守卫不命中时既有发射逐位不变」由构造保证（仅追加合取/析取条件）并被负对照与 v2 逐字节同态实证。✓
- nit（不构成打回）：⑥ 中 C1 枚举未显式列出 `loop_header`；其为白名单源（块内 opcode + 回边后继/支配结构）的派生块元数据，语义包含于「块末 opcode/前驱后继集合」，建议下批次顺手补一词。

### 5. BOM/插桩/禁用前缀 — PASS

- BOM：`core/cfg/region_ast_generator.py` 首 3 字节 = `efbbbf`，单头。✓
- 插桩：`git show 12d7ddb9` 全 diff 无 print/logging/pdb/breakpoint（唯一命中为 FIX_C.md 文档行自述该 grep 模式）。✓
- 禁用前缀：diff 无任何新增方法/函数定义 → 无禁用前缀问题（FIX_C.md「无新增方法」声明属实）。✓

### 6. 附带发现（登记，不计入批次 C）

- **在途未提交修改**：工作区 `site-packages/fly/simtradding/ptradeAccountOK.py` 有未提交 diff（两处 `finally: pass` → `write_lock.release()`）。经与 HEAD 现场重生成产物 `git diff --no-index` 比对**逐字节一致**——属批次 C 验证后残留的过期 OK.py 再生成（非手改、非代码变更）。建议下一批次提交或还原，避免 IV.2 门禁「在途变更」歧义。本审计未触碰该文件。

## §2 对抗变体读数表

探针：`rounds/round1/probes_rvC/`（rvC_v1-v4.py/.pyc/*OK.py；基线产物归档于 `baseline_616437c3/`；机器可读读数 `rvC_results.json`）。单变量对照：worktree @616437c3 仅 region_ast_generator.py 版本不同。

| 变体 | 形态 | 修复前 616437c3 | 修复后 12d7ddb9 | 产物对比 | 结论 |
|---|---|---|---|---|---|
| rvC_v1 | try 体含 for、finally 含语句 | **FAIL 1/2**：`finally: pass`，sink.append 蒸发 | **MATCH 2/2**：finally 语句保留 | DIFFERS | 修复生效（正常出口边认领） |
| rvC_v2 | try 体含 while + **循环内 raise**、finally 含语句 | **FAIL 1/2**：循环体镜像泄漏进 finalbody | **FAIL 1/2**：形态与基线**逐字节同态**（SHA256 IDENTICAL） | IDENTICAL | **存量破口**（非批次 C 引入/加剧）；触发条件经 v4 锁定为「循环内 raise」 |
| rvC_v3 | try/finally 外层套 with + if（宿主混合） | **FAIL 5/6**：`finally: pass` 且 res.touch() 泄漏到 try 外 | **MATCH 6/6** | DIFFERS | 修复生效，严格优于修复前 |
| rvC_v4（诊断） | 与 v2 同形、循环内无 raise | **FAIL 1/2**：`finally: pass`（与 op_station 蒸发同型，直接复现批次 B 失效机理） | **MATCH 2/2** | DIFFERS | 修复生效，机理验证成立 |

变体2 暴露的存量破口建议登记为 **B77 候选**（III.5）：形态 = `try/finally + while 循环 + 循环内 raise + finally 含非空语句`；现象 = 循环体镜像块泄漏进 Try.finalbody（`v=q.pop(); if v>limit: pass; raise ValueError(v); out.append(v); q`）；归属 = 区域归类/W11-A 层（守卫两侧同态，与 [B71] 边类型无关），移交后续轮次封闭。

## §3 终判：**放行**

- 判据全落 I.4 白名单（loop_header 经来源核查属块级结构事实），无黑名单项；
- 边类型封闭与块构建代码事实一致，异常副本入口不再误移交、真出口块照常认领，op_station 21/21 独立复跑通过；
- 门/内层判据逻辑互补无裂缝，`or ()` 防御对真实块零行为改变；
- docstring 六要素逐句核实无虚报（仅 C1 枚举建议补 `loop_header` 一词，nit）；
- 对抗实测：修复面 v1/v3/v4 由 FAIL 转 MATCH（含 op_station 蒸发同型的 v4 直接机理复现），v2 存量破口与修复前逐字节同态、无回退；无「以少发射换绿」（三例均为恢复发射）；
- BOM/插桩/禁用前缀三项门禁全过。

打回条件均不成立。随判放行移交两项登记：① B77 候选（v2 形态存量破口）；② ptradeAccountOK.py 在途重生成残留（提交或还原）。
