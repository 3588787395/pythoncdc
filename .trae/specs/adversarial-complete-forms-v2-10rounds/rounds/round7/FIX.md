# Round 7 修复批 · Task 7.2 交付
## B117–B120 守卫缺口型破口封闭（续作完成）

- 规范：`adversarial-complete-forms-v2-10rounds`（spec.md / tasks.md / checklist.md）
- 修复角色：修复工程师子代理（7.2 修复批 **续作**——前一任因配额中断，四守卫实现与门禁 2/3 第一面已在工作树；本续作核实实现、收紧过火判据、补齐全部门禁与交付）
- 基准：REVIEW.md（Task 7.1 评审）登记破口 **B117/B118/B119/B120**；HEAD = `76765985`（round6 终态），工作树唯一 core 改动 = `core/cfg/region_ast_generator.py`
- 结论一句话：**四破口全部封闭**（7 个最小复现全 MATCH）；攻击面 122/122 + neg 18/18（NEWFAIL=0，读数高于评审基线 114/122）；站桩 6 面 **WORSE=0**（round2face 235/251、probe42 176/196、round1face 417/423、residual 418/446、oldface 664/692、quotation 152/153，与 Round 6 终态逐位对齐 + 2 面改善）；34 集 1505/1568 与基线逐文件持平（NEWFAIL=0）；IV.2 合规自检全过。

---

## §0 续作过程说明（如实登记）

1. **前人遗留状态核实**：工作树含 `region_ast_generator.py` 四守卫实现（+454/-6，17 hunk）与 r7v7fix_attack.py / r7v7fix_probe_*（140/140 全过）/ r7v7fix_regress_round2face.json。续作逐 hunk 走读确认四守卫机制正确（§1–§4「续作确认」），但站桩 round2face 首跑 **231/251（基线 234/251，WORSE=4）** ——前人守卫存在 3 处过火（见 §5）。
2. **回退归因**（临时 env 门控插桩 `PYCDC_R7FIX_DEBUG`，交付前已全清）：`n7_01_simple_ternary`/`r10_15_global_hosts`/`cgroup_utils` = [B119] merge 兄弟发射守卫误触发（merge 块为普通汇合块/BoolOp 操作数块/try 体延续块，提前发射与既有发射面重排冲突）；`r10_21_fin_loopctrl` = [B119-deep] 回边释放对**纯回边块**（无用户语句）卸载了 continue 终结边登记职责。
3. **收紧**（仍全部 I.4 白名单判据，§5）：b119m 增设条件⑥（吞没风险事实）、B119-deep 增设「用户语句载体」判据。收紧后 4 个 WORSE 全部消除（cgroup 输出与 HEAD 字节一致、`set_cgroup_config` 为基线既有失败），7 复现保持 MATCH。
4. 全部自测门禁在**收紧后代码**上重跑；插桩清除后再次抽查（r7v7_b4a03 / r7v7_b2b04 / r10_21）读数不变。

---

## §1 B117 —— 体内 if 的 else 臂=纯 continue 回边块的降级重排缺「宿主尾区域」守卫

**破口回顾**（REVIEW.md §5 B117 行）：else-continue 降级重排（删 else=[Continue]、假边落空由回边隐式再生）仅当 if 区域=循环体尾区域时保语义；深度 ≥2 时假边误落宿主后继（continue 语义丢失）。违反 **C2（深浅不一致）+ C3**。最小复现：`r7v7_x_b2b04_d2.py`（深度 2 onset）、`r7v7_b2b04.py::b2b04_deep`（深度 3）。

**根因分析**：`_if_generate_normal` 的 else-continue 删除分支（原判据仅 `else_stmts==[Continue] and _current_loop is not None`）与 R100/RC3 continue 冗余抑制、嵌套区域全集认领三处共享「回边由循环结构再生」的隐式约定，均未验证「if 区域是否覆盖整个循环体」。当循环体尚有本区域之外的块（宿主 if 条件块、顺序后继），假边落空改落宿主语句；同时回边块被分析器并入 then_blocks 吸收后，其在嵌套区域认领循环中被全集标记吞没。

**守卫设计**（续作确认 + 核实证据）：
- **then 臂吸收守卫**（:21365）：`_current_loop.back_edge_block ∈ region.then_blocks` 且该回边块存在**区域外前驱**（前驱 ∉ then∪else∪blocks∪merge）时，从 then_blocks 摘除、不标记 generated，交还循环尾装配面。I.4 依据：块对象前驱集合 + 区域成员集合（同层结构事实）。恢复 C3（无区域外前驱时逐位保持）。
- **尾区域谓词 `_if_region_is_loop_body_tail`**（:23631，带独立六项+C 条款 docstring）：循环 `body_blocks`（除 header）全部 ⊆ 本区域 blocks∪then_blocks∪else_blocks ⇒ 尾区域。I.4 依据：区域成员关系（body_blocks/then_blocks/else_blocks 集合事实），无深度/偏移条件。
- **else-continue 删除加尾区域前置守卫**（:21565）：非尾区域时保留显式 `else: continue`（通用发射路径）。恢复 C2（深浅一致：深度 ≥2 不再降级重排）与 C3。
- **R100/RC3 冗余抑制加同一谓词**（:25754/:25822）：「merge 即 header ⇒ 回边再生」的抑制只在尾区域成立。恢复 C2。
- **悬置回边块不随嵌套区域认领**（:25279/:25994/:26022）：回边块 ∈ 当前循环 back_edge_block(s) 且不在嵌套区域两臂内时跳过全集标记，交 LOOP_BACK_EDGE 分派发射。I.4 依据：循环结构字段 back_edge_block/back_edge_blocks + 区域成员关系。恢复 C1（块唯一归属，acc+=1 块不再蒸发）。
- **核实其正确性的证据**：复现 r7v7_x_b2b04_d2 / r7v7_b2b04 转 MATCH（§6 门禁 1）；边界外形态 b2b01（if c: break）/b2b02（return）/b2b03（无 else 重组）维持 MATCH = 守卫不误触发（r7v7fix_probe_detail.json）。

**触及方法与 docstring**：守卫体位于 `_if_generate_normal`（:20845，非 `_generate_*` 命名，守卫点均有结构化注释块）与 `_process_if_blocks`（:24887）；`_generate_if`（:14487）docstring 六项+C 条款（round6 建置）未被本批行为改动破坏，续作核对一致。

**自测读数**：r7v7_x_b2b04_d2 = 2/2 MATCH、r7v7_b2b04 = 3/3 MATCH；b2 族其余 11 探针 + 负对照全过。

## §2 B118 —— `if c: continue else: break` 的 else-break 出口边被丢弃

**破口回顾**（REVIEW.md §5 B118 行）：else→break 边与 FOR_ITER 自然出口共享出口块，if 生成只发 then=[Continue]，else 臂（break 边）因目标=循环出口块被丢弃 → break 变「继续迭代」。违反 **C3**（跨区域非局部引用无显式认领）。最小复现：`r7v7_x_b2c03_pure.py`、`r7v7_b2c03.py::b2c03_shallow`。

**根因分析**：`_if_generate_normal` else 臂发射路径对「else_blocks 为空 + merge=循环 break 落点」的形态只发射 then 臂，假边的 break 语义无任何发射面认领；Break 发射守卫只覆盖 then 路径。

**守卫设计**（续作确认）：else-break 出口边显式认领守卫（:21537）——识别条件：① 无 else_blocks 且 else 生成结果为空、无 elif 链；② 处于循环上下文且 `merge_block ∈ _current_loop.break_blocks`（分析器对 break 落点的权威登记，I.4 依据：循环结构字段 + 区域成员关系）；③ then 臂各块后继集均不含 merge（then 以跳转终结，假边是 merge 唯一来源，I.4 依据：后继集合）。满足时 `orelse = [Break]`（break 语句重编译自然再生出口 POP_TOP）。恢复 **C3**（出口边显式认领）+ 间接恢复 C1（merge 块不重复发射）。③ 不成立（`if c: S; break` 共享汇合形态）时维持既有路径逐位不变（C3）。

**核实其正确性的证据**：复现 r7v7_x_b2c03_pure = 2/2、r7v7_b2c03 = 3/3 全 MATCH（break 语义恢复，字节码出口块 POP_TOP 再生）；深度 3 变体（b2c03_deep，break 块非循环出口）本就通过且保持 MATCH = 守卫窄触发不误吞。

**触及方法与 docstring**：同 §1（守卫体在 `_if_generate_normal`，注释含识别条件①②③与归约方式）。

**自测读数**：c03 单元 5/5（bracket + deep）；b2c02（then/else 双 continue）3/3 不受扰。

## §3 B119 —— 空/不可抛 try 体 + 非空 finally 体重复发射（两深度皆破）

**破口回顾**（REVIEW.md §5 B119 行）：`try: pass finally: <体>` 的体正常路径副本内联进 try 体块（3.11 异常表无保护区 ⇒ 块不切分），try 体走查重复发射 → 重编译出两份体。违反 **原则 2 每块唯一归属（C1 发射侧表现）**。最小复现：`r7v7_x_b4a03_pure.py`、`r7v7_b4a03.py`（两深度皆破）。

**根因分析**：CPython 3.11 零成本异常布局下，不可抛 try 体的 finally 正常副本与 try 体同块内联，异常副本（PUSH_EXC_INFO 帧 + RERAISE）另存 finally_blocks；识别侧 R09（region_analyzer.py:1460）已识别孤儿 finally 帧，但发射侧 `_generate_try_body` 走查与 `_generate_try` 收尾毯式标记无对应守卫——体块既进 try 体又被 finalbody 重建；跨度收集拉进 region.blocks 的宿主尾随块（如 `return flag`）被毯式标记吞没（宿主顺序代码蒸发）。

**守卫设计**（续作确认 + 两处收紧）：
- **空/不可抛 try 体镜像守卫**（`_generate_try_body` :28349；docstring 增补 :27990）：① has_finally、无 except handler、finally_blocks 非空且无 finally_copy_blocks；② try 体块末指令为前向跳转；③ finally 首块 PUSH_EXC_INFO 开头 RERAISE 终结；④ try 体块与 finally 首块剥噪后 opcode 序列逐指令**镜像**（I.4 依据：块内 opcode 形态事实，与 `_identify_empty_body_finally_regions` 副本对齐同构）。命中 → 整块登记 generated 不发射，Try.body 空（回填 Pass），体唯一归属 finalbody。恢复 **C1**。④ 不匹配（体含用户语句混合块）逐位保持（C3）。
- **B119-deep 循环回边/条件块释放**（`_b68_is_tryfin_tail_releasable` :3375）+ **续作收紧**（:3385）：块末指令 ∈ BACKWARD_JUMP_OPS 且跳转目标 is 某 LoopRegion header_block，且**块内含用户语句载体**（剥噪后存在非跳转指令——纯回边块如 r10_21 fin_continue_stmt 的 continue 终结块无可移交的发射内容，维持原认领路径）时显式释放，交包围循环装配面发射。I.4 依据：块末 opcode + 循环 header 同一性 + 块内 opcode。恢复 C1/C2（deep 变体 `n -= 1` 循环尾块不再被吞）。目标非任何循环 header 的 backward 块维持原拒绝路径（C3）。
- **非空 finally 帧宿主尾随块释放**（同谓词 :3437）：副本身份封闭 = 块起点 **> finally_blocks 全部指令最大偏移**（帧尾边界；一切正常/异常副本块 ≤ 该边界，W21 保护面不受影响）且通过判据 2/3 时释放。I.4 依据：区域跨度/结构字段 + 指令偏移（非魔法常数）。
- **宿主 if 的 merge 后继兄弟发射**（`_if_generate_normal` :21642，装配 :22028）+ **续作收紧⑥**：merge 语句作为 If 节点**后继兄弟**发射并登记 generated。识别条件①-⑤（续作确认）+ 新增 **⑥ 吞没风险事实**：merge 必须位于某个**已完成生成**的 TryExceptRegion（≠本区域）的 blocks 中——即子 try 收尾认领循环已运行并按释放判据跳过它，本 if 是其剩余唯一发射面；不在任何已生成 try 块集内的普通汇合块由既有兄弟发射面处理（提前发射会同其重排冲突——cgroup/neg_simple_and_or/g_in_try_except 实测归因）。I.4 依据：区域成员关系 + 区域生成状态（`_generated_regions` 为生成器既有登记，非新增 self 状态）。恢复 **C1**（`return flag` 唯一归属发射）+ C2。
- **非空 finally 帧 post-try 尾随块收集**（`_generate_try` :30207；docstring 增补 :29896）：B55-c 判据同层外推，候选块须起点 ≥ try_offset_end 且 > 帧尾边界、无 RERAISE、非祖先 IfRegion merge（parent 链 merge_block 同一性）、非循环回边块、归属权威为本区域。I.4 依据：区域成员关系/父子关系/块末 opcode/归属权威。恢复 C1。

**触及方法与 docstring**：`_generate_try_body`（:27956）docstring 六项+C 条款（round6 建置）**增补 [B119] 镜像守卫条款**（:27990）；`_generate_try`（:29775）docstring 六项+C 条款**增补 [B119] 尾随块收集条款**（:29896）；`_b68_is_tryfin_tail_releasable`（:3308）docstring 及判据注释同步收紧说明。

**自测读数**：r7v7_x_b4a03_pure = 2/2、r7v7_b4a03 = 3/3 全 MATCH；b4b01（合法嵌套不误释放）3/3、b4a06（try 体仅表达式）3/3 不受扰。

## §4 B120 —— for-else×嵌套 if/else(break)×循环后共享 return 深度 3 误归属

**破口回顾**（REVIEW.md §5 B120 行）：循环出口与宿主 if 假边的共享后继 `return acc`（非孤儿、有顶级祖先）被误归属进宿主 if 臂体 → 函数级 return 消失、假路径变隐式 return None。违反 **C2 + 原则 3（嵌套即抽象节点）**。最小复现：`r7v7_b4c03.py::b4c03_deep`。

**根因分析**：`_loop_generate_for` 的 break 落点发射面（孤儿块释放 :1717-1800 一带）对「break 落点同时是祖先区域 merge_block」的共享汇合无守卫，把宿主层汇合块的语句发射进本循环的 `_sequential_after_loop`（= 宿主臂体内），吞并父级后继语句。

**守卫设计**（续作确认）：祖先汇合块守卫（:6498）——break 落点 `_bb` 沿 `region.parent` 链存在祖先区域其 `merge_block is _bb` 时，跳过本循环对该落点的发射与 generated 认领（不 discard/add），落点保持其权威归属区域（顶级 BASIC 区域）的发射责任，由宿主层按既有次序输出。I.4 依据：区域父子关系（parent 链）+ merge_block 块对象同一性。恢复 **C2**（深度 3 不再误归属）+ 原则 3/原则 4（块归拥有其全部到达边的层级）。无祖先命中（break 落点专属本循环，如 fin_break 形态）时既有发射逐位保持（C3）。

**核实其正确性的证据**：复现 r7v7_b4c03 = 3/3 MATCH（`return acc` 回到函数级、flag=false 路径语义恢复）；边界负对照 x_b4c03_d2（深度 2）= 2/2 保持 MATCH；r10_21 fin_break（break 落点专属循环）4/4 不受扰。

**触及方法与 docstring**：守卫体位于 `_loop_generate_for`（:5607，非 `_generate_*` 命名，守卫点有结构化注释块含识别条件与归约方式）。

**自测读数**：b4c03 = 3/3；b4c01/b4c02（B4×B3、B4×B2 组合）3/3 不受扰。

---

## §5 过火收紧记录（站桩回退 → 判据收紧，门禁 6 执行记录）

| # | 回退文件（round2face） | 症状 | 归因（插桩实测） | 收紧（判据仍全 I.4 白名单） | 收紧后 |
|---|----------------------|------|-----------------|---------------------------|--------|
| 1 | `n7_01_simple_ternary::neg_simple_and_or` | 幻影裸表达式 `a` | b119m 对 `return a or b` 的 BoolOp 操作数块（merge@14，fall-through 续接块）触发 | b119m 条件⑥（吞没风险事实）：无 try 块集包含 merge → 不触发 | 5/5 MATCH |
| 2 | `r10_15_global_hosts::g_in_try_except` | `return CACHE[key]` → `CACHE[key]`（return 丢失） | b119m 对 try 体内 if 的延续块（merge@48，块末 BINARY_SUBSCR fall-through）提前发射 | 同⑥：外层 try 尚未完成生成 → 不触发 | 6/6 MATCH |
| 3 | `IQCommon/util/cgroup_utils::add_process_to_cgroup` | 汇合调用被重排进 `else:` 臂 + 幻影 continue（语义改变） | b119m 对函数级 try 包裹的 13 个普通汇合 merge 提前发射（其余 12 处被既有发射面正确处理，重排冲突） | 同⑥：外层 try 未完成生成 → 全部不触发；输出与 HEAD 字节一致 | 7/8（=基线，`set_cgroup_config` 为基线既有失败） |
| 4 | `r10_21_fin_loopctrl::fin_continue_stmt` | 函数尾 `return out` 蒸发 | B119-deep 回边释放对**纯 JUMP_BACKWARD** continue 终结块（无用户语句）卸载登记职责，级联破坏宿主装配 | 增设「用户语句载体」判据：剥噪后仅剩跳转的纯回边块不释放 | 4/4 MATCH |

收紧对修复面无损伤：7 复现保持 MATCH（§6 门禁 1）、攻击面 122/122（§6 门禁 2）。

---

## §6 自测门禁证据（全过）

| # | 门禁 | 读数 | 基线 | 判定 | 证据 |
|---|------|------|------|------|------|
| 1 | 7 个最小复现转 MATCH | x_b2b04_d2 2/2、b2b04 3/3、x_b2c03_pure 2/2、b2c03 3/3、x_b4a03_pure 2/2、b4a03 3/3、b4c03 3/3（逐个 `pycdc regen` + `pyc_verify.py single`） | 评审 1/2、2/3、1/2、2/3、1/2、1/3、2/3 | **全 MATCH** | 本节执行记录 + r7v7fix_probe_detail.json |
| 2 | 攻击面重放（r7v7fix_attack.py，47 探针 compile→regen→batch+single） | **attack 122/122、neg 18/18、47/47 文件 success、NEWFAIL=0** | attack 114/122、neg 18/18 | **过（+8 单元，零新失败）** | r7v7fix_probe_index.json / r7v7fix_probe_results.json / r7v7fix_probe_detail.json |
| 3 | 站桩 6 面（r7v7fix_station.py，RV2 先 regen 再 verify） | round2face **235/251**、probe42 **176/196**、round1face **417/423**、residual **418/446**、oldface **664/692**、quotation **152/153** | Round 6 终态 234/251、176/196、417/423、417/446、664/692、152/153 | **逐面 WORSE=0**（round2face/residual 各 +1 改善；quotation 唯一失败 change_his_to_forward 与基线一致） | r7v7fix_regress_round2face.json、r7v7fix_regress_probe42.json、r7v7fix_full_round1face.json、r7v7fix_full_residual_a/b.json、r7v7fix_full_oldface_a/b.json、r7v7fix_quotation.json、r7v7fix_station_regress_compare.json（r7v7fix_compare_regress.py） |
| 4 | 34 集（harden-completed-forms-10rounds/baseline/failing_index.json，RV2 分 4 片 batch） | **1505/1568**，逐文件与基线持平 | 1505/1568 | **NEWFAIL=0** | r7v7fix_34set_report.json + shard0-3 JSON（.trae/specs/harden-completed-forms-10rounds/round7fix/） |
| 5 | IV.2 合规自检 | 见 §7 | — | **全过** | 本节执行记录 |

## §7 IV.2 合规自检明细

| 项 | 结果 |
|----|------|
| core 模块 IMPORT_OK | core / core.cfg / region_ast_generator / region_analyzer / cfg_builder / basic_block / ast_converter / ast_generator_v2 / code_generator 全部 IMPORT_OK |
| 全量 py_compile | core/*.py + core/cfg/*.py + parsers/*.py + scripts/*.py + pycdc.py 全部 OK |
| BOM | `region_ast_generator.py` head3 = `efbbbf`，全文件 BOM count = 1（单头保持） |
| 插桩残留 | 续作临时插桩（PYCDC_R7FIX_DEBUG / R7FIXDBG 标记）grep = 0 全清；存量 env 门控插桩为评审已登记存量（未新增） |
| G0（触及方法 docstring 六项+C 条款与代码一致） | `_generate_try_body`（:27956，六项+C 条款+[B119] 增补条款 :27990）、`_generate_try`（:29775，六项+C 条款+[B119] 增补条款 :29896）、`_generate_if`（:14487，round6 建置核对一致）、新增 `_if_region_is_loop_body_tail`（:23631，六项+C 条款齐备）；守卫点注释与代码逐条对应 |
| G3（零新增七前缀方法） | diff 新增行 grep `_fix_/_merge_/_patch_/_fallback_/_hack_/_workaround_/_temp_` 方法定义 = 0 |
| G4（零新增硬编码深度/计数上限） | diff 新增行 grep depth/计数上限 = 0；深度不出现在任何判据 |
| I.4 黑名单（判据面） | 无文件名/函数名白名单、无 start_offset 魔法阈值（帧尾边界 = finally_blocks 指令偏移运行时派生）、无跨层 `X.entry in Y.blocks` 反查（新增代码用 region.parent 链与区域字段）、无新增 self 跨方法状态（仅读既有 `_generated_regions`）、无「以少发射换全绿」窄门控（收紧⑥/用户语句载体两判据均为结构事实守卫，评审 §5 已确认原实现非窄门控） |

## §8 交付物清单

| 类别 | 路径 |
|------|------|
| 本报告 | `rounds/round7/FIX.md` |
| 修复实现 | `core/cfg/region_ast_generator.py`（工作树 M，落地锚点见 §9） |
| 攻击面证据 | `rounds/round7/r7v7fix_attack.py`（r7v7_attack.py 续作副本，输出前缀 r7v7fix_）、`r7v7fix_probe_index.json`、`r7v7fix_probe_results.json`、`r7v7fix_probe_detail.json` |
| 站桩证据 | `rounds/round7/r7v7fix_station.py`（r7v7_station.py 续作副本，输出前缀 r7v7fix_）、`r7v7fix_regress_round2face.json`、`r7v7fix_regress_probe42.json`、`r7v7fix_full_round1face.json`、`r7v7fix_full_residual_a/b.json`、`r7v7fix_full_oldface_a/b.json`、`r7v7fix_quotation.json` |
| 站桩对照 | `rounds/round7/r7v7fix_compare_regress.py`（r7v7_compare_regress.py 续作副本）→ `r7v7fix_station_regress_compare.json` |
| 34 集证据 | `.trae/specs/harden-completed-forms-10rounds/round7fix/r7v7fix_34set_report.json` + `r7v7fix_34set_shard0..3.json` + `idx_shard0..3.json` |
| regen 副产物 | `*OK.py` M 态（test_repros/round7、round10、round8、site-packages 及 r7v7fix 站桩/攻击重放 regen 所必需，未手改） |

## §9 落地锚点清单（file:line，供 grep 核验；行号 = 交付时工作树）

`core/cfg/region_ast_generator.py`：

| 破口 | 锚点 |
|------|------|
| B117 | :21365（then 臂吸收守卫）、:21565（else-continue 删除尾区域守卫）、:23631（`_if_region_is_loop_body_tail` 谓词）、:25279/:25994/:26022（悬置回边块认领跳过）、:25754/:25822（R100/RC3 抑制尾区域守卫） |
| B118 | :21537（else-break 出口边显式认领守卫） |
| B119 | :27990（`_generate_try_body` docstring [B119] 条款）、:28349（try 体镜像守卫）、:29896（`_generate_try` docstring [B119] 条款）、:30207（post-try 尾随块收集）、:3375/:3385（B119-deep 回边释放+收紧）、:3437（非空 finally 帧尾随块释放）、:21642（merge 后继兄弟发射识别①-⑥）、:22028（兄弟语句装配）、:25331/:25337（子区域认领释放判据，`_b68_is_tryfin_tail_releasable` 调用点） |
| B120 | :6498（祖先汇合块守卫） |
| 宿主方法 | :3308（`_b68_is_tryfin_tail_releasable`）、:5607（`_loop_generate_for`）、:14487（`_generate_if`）、:20845（`_if_generate_normal`）、:24887（`_process_if_blocks`）、:27956（`_generate_try_body`）、:29775（`_generate_try`）、:23631（`_if_region_is_loop_body_tail`） |

---

## §10 「代码已落地」声明（I.6）

**本修复批（Round 7 · Task 7.2）四破口 B117/B118/B119/B120 的守卫代码已全部落地于工作树 `core/cfg/region_ast_generator.py`（未提交，零 git 操作），自测门禁 1–5 全部通过（7 复现全 MATCH、攻击面 NEWFAIL=0 且读数提升、站桩 6 面 WORSE=0、34 集 NEWFAIL=0、IV.2 合规全过），交付证据齐备。无未落地的声明项，无虚报。**
