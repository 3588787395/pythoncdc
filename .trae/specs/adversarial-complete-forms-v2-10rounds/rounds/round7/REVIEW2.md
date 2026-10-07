# Round 7 复核批 · Task 7.3 交付（REVIEW2）
## Round 7 修复批（384ad07c）独立复核：B117/B118/B119/B120 四守卫封闭确认 + 变体攻击

- 规范：`adversarial-complete-forms-v2-10rounds`（spec.md / tasks.md / checklist.md）
- 复核角色：评审工程师子代理（独立于修复工程师；零 core 修改 / 零 git 写操作）
- 复核对象：修复批提交 `384ad07c`（相对评审基线 `49e5301b`），唯一 core 改动 = `core/cfg/region_ast_generator.py`（+516/-6）
- 复核探针前缀：`r7v7r_*`（`test_repros/round7/`，5 个新文件 35 单元，零覆盖既有文件）
- 判据工具：`scripts/pyc_verify.py`（唯一判据，未动）

---

## §0 终判结论

| 项 | 判定 |
|----|------|
| **复核终判** | **通过**（四破口 B117/B118/B119/B120 封闭确认，无打回项） |
| 打回项 | **0** |
| 新破口 | **1 项：B121**（复核批变体攻击发现，**存量缺口、非本修复批回归**——49e5301b 基线同型同败；详见 §4.2） |
| 观察（非违反） | O1 docstring 措辞严于代码（行为等价）；O2 落地锚点 :22025 实际 :22028（3 行漂移）；S regen 副作用 10 文件 M（未还原，登记待主代理） |

一句话理由：四守卫的判据全部落在 I.4 白名单（块末 opcode / 前驱后继集合 / 循环结构字段同一性 / 区域成员关系）上，逐 hunk 无窄门控、无个案补丁、无深度/偏移/名字条件，落地锚点 20/20 grep 实证在树；7 复现、攻击面 122/122、站桩 6 面 WORSE=0、34 集 1505/1568 全部由本复核独立复跑复现；四守卫边界外变体 23/24 通过，唯一失败经基线对照确证为与四守卫无关的存量缺口（B121），且同一对照显示修复在 while 宿主家族上由基线 FAIL 转 MATCH（守卫正向生效的直接证据）。

---

## §1 逐 hunk 合规审查表（diff `49e5301b..384ad07c -- core/cfg/region_ast_generator.py`，19 个代码 hunk 全查）

判据口径 = spec I.4：白名单只允许同层块对象结构事实（块末指令 opcode、后继/前驱集合、异常边、区域成员关系）；黑名单（出现即打回）= 文件名/函数名白名单、start_offset 魔法阈值、跨层 `X.entry in Y.blocks` 反查、新增 self 跨方法状态、以少发射换全绿、硬编码深度/计数上限。

| # | 锚点（file:line） | 守卫/内容 | 判据来源 | 白名单符合 | 窄门控/个案补丁 | docstring/注释 C 条款 | 判定 |
|---|------------------|-----------|----------|-----------|----------------|---------------------|------|
| H1 | :3375-3397 | [B119-deep] 循环回边块显式释放（`_b68_is_tryfin_tail_releasable` 内） | 块末 opcode ∈ BACKWARD_JUMP_OPS + `argval` 目标 `is` 某 LoopRegion.header_block + 块内含用户语句载体（剥噪非跳转指令存在） | ✓（opcode+结构字段同一性+块内 opcode） | 无（纯回边块不释放＝维持原认领，非少发射） | ✓ 机制+[B119-deep 收紧] C3 条款 | 合规 |
| H2 | :3434-3455 | [B119] 非空 finally 帧宿主尾随块释放（同谓词） | 帧尾边界 = finally_blocks 全部指令最大偏移（**运行时派生**，非魔法常数）+ start_offset 比较 | ✓（区域跨度结构事实；无字面阈值） | 无 | ✓ 副本身份封闭论证 + C3 | 合规 |
| H3 | :6495-6517 | [B120] 祖先汇合块守卫（`_loop_generate_for`） | region.parent 链逐级 `merge_block is _bb`（块对象同一性） | ✓（区域父子关系） | 无（无祖先命中逐位保持） | ✓ 识别条件+归约方式+C3 | 合规 |
| H4 | :21362-21388 | [B117] then 臂吸收守卫（`_if_generate_normal`） | back_edge_block ∈ then_blocks（不在 else_blocks）+ 前驱集合 ⊆ then∪else∪blocks∪merge 判定区域外前驱 | ✓（前驱集合+区域成员关系） | 无（f2 共享尾不触发） | ✓ 机制+C3 | 合规 |
| H5 | :21537-21558 | [B118] else-break 出口边显式认领 | ①无 else_blocks/elif；②merge_block ∈ `_current_loop.break_blocks`；③then 各块后继集不含 merge | ✓（循环结构字段+后继集合） | 无（③ 不成立逐位保持） | ✓ ①②③+归约方式+C3；`{'type': 'Break'}` 与既有发射约定一致（:8660 等） | 合规 |
| H6 | :21565-21581 | [B117] else-continue 删除分支加尾区域前置守卫 | 谓词 `_if_region_is_loop_body_tail`（H9） | ✓ | 无（非尾区域保留显式 continue＝通用发射路径） | ✓ 识别条件+C3 | 合规 |
| H7 | :21639-21743 | [B119] merge 后继兄弟发射（识别①-⑥+假边同侧守卫） | merge/then/else 成员关系、∉ generated_blocks、剥噪非空、前驱集合 ⊆ 两臂∪condition_block∪entry、非循环回边（back_edge 同一性+末指令目标 header 同一性）、⑥ 位于**已完成生成** TryExceptRegion.blocks（读既有 `_generated_regions`，Set[int]，:376） | ✓（全部区域成员关系+前后驱集合+生成状态登记；非黑名单 `X.entry in Y.blocks` 区域合法性反查——本处为块级归属判定） | 无（④/⑤/⑥ 任一不成立交既有发射面） | ✓ ①-⑥+归约方式+C3；`_explicit_return` 标记由**既有** W14-B 剥离豁免逻辑消费（:21750，pre-existing） | 合规 |
| H8 | :22028-22035 | [B119] merge 兄弟语句装配（If 节点后缀兄弟） | —（消费 H7 的 pending 列表） | ✓ | 无 | ✓ 指回 H7 | 合规 |
| H9 | :23631-23654 | 新谓词 `_if_region_is_loop_body_tail` | body_blocks（除 header）⊆ blocks∪then∪else | ✓（区域成员关系） | 无 | ✓ **六项模板①-⑥齐备 + [C1][C2][C3] 独立条款**，与代码行为一致 | 合规 |
| H10 | :25279-25294 | [B117] 悬置回边块不随嵌套区域认领（认领循环 1） | back_edge_block(s) 成员 + 不在嵌套区域两臂 | ✓ | 无（回边仍属臂时照旧认领） | ✓ C3 | 合规 |
| H11 | :25328-25337 | [B119] 子区域认领释放判据（`_b68_is_tryfin_tail_releasable` 调用点） | 复用 H1/H2 谓词 | ✓ | 无 | ✓ 机制注释 | 合规 |
| H12 | :25751-25768 | [B117] R100 冗余抑制收紧（两分支） | 追加 `_if_region_is_loop_body_tail(region)` | ✓ | 无 | ✓ 机制注释 | 合规 |
| H13 | :25819-25832 / :25844-25852 | [B117] RC3 抑制收紧（两分支） | 追加 `_if_region_is_loop_body_tail(_rc3_enclosing)`（对 enclosing IfRegion 判定，语义正确） | ✓ | 无 | ✓ C3 | 合规 |
| H14 | :25991-26005 | [B117] 悬置回边认领跳过（认领循环 2） | 同 H10 | ✓ | 无 | ✓ C3 | 合规 |
| H15 | :26019-26033 | [B117] 悬置回边认领跳过（认领循环 3） | 同 H10 | ✓ | 无 | ✓ C3 | 合规 |
| H16 | :27987-28000 | `_generate_try_body` docstring [B119] 条款增补 | — | — | — | ✓ 六项模板+C 条款保持（:27957-28033 全文核验 ①-⑥+_missing=NONE），增补条款与 H17 行为一致 | 合规 |
| H17 | :28346-28383 | [B119] 空/不可抛 try 体镜像守卫 | ①has_finally/无 handler/finally_blocks 非空/无 finally_copy_blocks；②体块末前向跳转；③finally 首块 RERAISE 终结+含 PUSH_EXC_INFO；④剥噪 opcode 序列逐指令镜像 | ✓（块内 opcode 形态事实） | 无（④ 不匹配逐位保持） | ✓ ①-④+归约方式+C3 | 合规（观察 O1：docstring 称 PUSH_EXC_INFO「开头」，代码为 `any(...)` 存在性判定——真实 3.11 帧布局 PUSH_EXC_INFO 恒为首指令，行为等价，非违反） |
| H18 | :29893-29910 | `_generate_try` docstring [B119] 条款增补 | — | — | — | ✓ 六项模板+C 条款保持（:29776-29912 全文核验），与 H19 一致 | 合规 |
| H19 | :30204-30265 | [B119] post-try 宿主尾随块收集（B55-c 同层外推） | ∈ region.blocks、起点 ≥ try_offset_end（既有 `_b55c_tail_off`）且 > 帧尾边界（派生）、无 RERAISE、非祖先 merge（parent 链）、非循环回边、归属权威 `block_to_region`、未生成；且仅在 B55-c 集合为空时运行 | ✓（区域成员关系+父子关系+opcode+运行时派生偏移） | 无 | ✓ 识别条件+归约方式+C3 | 合规 |

**专项核查（全过）**：
- I.5 七前缀方法：diff 新增 `def (_fix_/_merge_/_patch_/_fallback_/_hack_/_workaround_/_temp_)*` = **0**。
- 硬编码深度/计数上限：diff 新增行 grep depth/上限 = **0**（四守卫判据无任何深度条件）。
- start_offset 魔法阈值：diff 新增行无字面常数比较（:3448/:30237 等均为运行时派生边界）。
- 新增 self 跨方法状态：**0**（仅读既有 `_generated_regions`/`_generated_blocks`/`_generated_offsets`）。
- 插桩残留：diff 中 `R7FIXDBG`/`PYCDC_R7FIX_DEBUG`/environ = **0**（续作临时插桩确认全清）。
- touched `_generate_*` 方法 docstring 六项核验：`_generate_if`(:14488-14546)、`_generate_try_body`(:27957-28033)、`_generate_try`(:29776-29912) ①-⑥+[C1][C2][C3] **missing=NONE**；守卫体宿主 `_if_generate_normal`/`_loop_generate_for`/`_process_if_blocks`（非 `_generate_*` 命名）守卫点均有结构化注释块（识别条件/归约方式/C3），与 FIX.md §1-§4 声明一致。
- BOM：`region_ast_generator.py` head3 = `efbbbf`，全文件 BOM count = **1**（单头保持）。

---

## §2 落地核验表（I.6：FIX.md §9 落地锚点逐条 grep，file:line 逐行取文核对特征片段）

| FIX.md §9 锚点 | 核对结果 |
|---------------|---------|
| :21365（B117 then 臂吸收守卫） | ✓ 实文 `# [B117] 循环回边块的 then 臂吸收守卫（区域归约算法原则 2 每块` |
| :21537（B118 else-break 认领） | ✓ 实文 `# [B118] else-break 出口边显式认领守卫（原则 4 入口引用语义 +` |
| :21565（else-continue 删除尾区域守卫） | ✓ 实文 `# [B117] else-continue 隐式再生守卫（原则 2 每块唯一归属）` |
| :23631（`_if_region_is_loop_body_tail`） | ✓ 实文 `def _if_region_is_loop_body_tail(self, region) -> bool:` |
| :25279 / :25994 / :26022（悬置回边认领跳过 ×3） | ✓ 三处实文均命中 |
| :25754 / :25822（R100/RC3 抑制尾区域守卫 ×2） | ✓ 两处实文均命中 `[B117] 尾区域守卫` |
| :27990（`_generate_try_body` docstring [B119] 条款） | ✓ |
| :28349（try 体镜像守卫） | ✓ |
| :29896（`_generate_try` docstring [B119] 条款） | ✓ |
| :30207（post-try 尾随块收集） | ✓ |
| :3375 / :3385（B119-deep 回边释放+收紧） | ✓ 两处实文均命中 |
| :3437（非空 finally 帧尾随块释放） | ✓ |
| :21642（merge 后继兄弟发射识别①-⑥） | ✓ |
| :22025（兄弟语句装配） | ✓ 实文在 **:22028**（3 行漂移，锚点特征唯一命中——观察 O2，非虚报） |
| :25331 / :25337（子区域认领释放判据调用点） | ✓ |
| :6498（B120 祖先汇合块守卫） | ✓ |
| 宿主方法 :3308/:5607/:14487/:20845/:24887/:27956/:29775/:23631 | ✓ 全部 def 行核对一致 |

**落地核验 = 20/20 通过（19 处行号精确命中，1 处 3 行漂移且特征唯一）。FIX.md §10「代码已落地」声明属实，无未落地声明项、无虚报。**

---

## §3 读数独立复跑表（关键项亲跑；「修复声称」= FIX.md §6）

### §3a 七个最小复现（亲跑：`python pycdc.py <pyc> -o <OK>` + `pyc_verify.py single`）

| 探针 | 评审基线读数 | 修复声称 | 本复核亲跑 | 判定 |
|------|-------------|---------|-----------|------|
| r7v7_x_b2b04_d2 | 1/2 | 2/2 MATCH | **success 2/2** | ✓ |
| r7v7_b2b04 | 2/3 | 3/3 | **success 3/3** | ✓ |
| r7v7_x_b2c03_pure | 1/2 | 2/2 | **success 2/2** | ✓ |
| r7v7_b2c03 | 2/3 | 3/3 | **success 3/3** | ✓ |
| r7v7_x_b4a03_pure | 1/2 | 2/2 | **success 2/2** | ✓ |
| r7v7_b4a03 | 1/3 | 3/3 | **success 3/3** | ✓ |
| r7v7_b4c03 | 2/3 | 3/3 | **success 3/3** | ✓ |

**7/7 全 MATCH，与声称逐项一致。**

### §3b 攻击面（亲跑全量 `r7v7fix_attack.py`，compile→regen→batch+single）

| 项 | 评审基线 | 修复声称 | 本复核亲跑 | 判定 |
|----|---------|---------|-----------|------|
| attack units | 114/122 | 122/122 | **122/122**（41 文件，detail JSON 逐行 0 失败行） | ✓ |
| neg units | 18/18 | 18/18 | **18/18**（6 文件全 MATCH） | ✓ |
| NEWFAIL | — | 0 | **0**（47/47 文件 success） | ✓ |

重跑产物与提交证据自洽：`r7v7fix_probe_results.json` 重跑 diff 仅 `elapsed_sec`/`generated_at` 时间戳（其余字节一致）；`r7v7fix_probe_index.json`/`r7v7fix_probe_detail.json` 重跑后逐字节一致。

### §3c 站桩 6 面

| 面 | Round 6 终态 | 修复声称 | 本复核读数来源 | 读数 | 判定 |
|----|-------------|---------|---------------|------|------|
| quotation | 152/153 | 152/153 | **亲跑** `r7v7fix_station.py quotation` | **152/153**，唯一失败 `change_his_to_forward: Different control flow` 与基线一致 | ✓ |
| round2face | 234/251 | 235/251（+1 改善） | `r7v7fix_regress_round2face.json` 逐行求和 = 45 行 235/251；compare JSON same=44/improved=1/**WORSENED=0** | 235/251 | ✓ |
| probe42 | 176/196 | 176/196 | `r7v7fix_regress_probe42.json` 42 行 176/196；compare base=154/189 为**旧快照**（round7 评审已登记之 improved 名单现象），new=176/196 与 Round 6 终态逐位一致，WORSENED=0 | 176/196 | ✓ |
| round1face | 417/423 | 417/423 | `r7v7fix_full_round1face.json` 24 行 417/423；same=24/WORSENED=0 | 417/423 | ✓ |
| residual | 417/446 | 418/446（+1 改善） | `r7v7fix_full_residual_a/b.json` 72 行 418/446；compare base=404/446 旧快照，WORSENED=0（+1 本轮改善与 claimed 一致） | 418/446 | ✓ |
| oldface | 664/692 | 664/692 | `r7v7fix_full_oldface_a/b.json` 59 行 664/692；WORSENED=0 | 664/692 | ✓ |

**6 面 WORSE=0 独立确认；证据链（face JSON ↔ compare JSON ↔ FIX.md 声称）三方自洽。**

### §3d 34 集

| 项 | 修复声称 | 本复核核验 | 判定 |
|----|---------|-----------|------|
| 合并读数 | 1505/1568，NEWFAIL=0 | `r7v7fix_34set_report.json`（34 行 1505/1568）== shard0-3 合并（9+9+8+8=34 行，逐文件 units 一致）；对 `baseline/failing_index.json` 逐文件比对：**WORSE=0、NEWFAIL=0**（3 文件 +9 units 改善相对更旧基线快照，与 Round 6 终态 1505/1568 持平口径一致） | ✓ |
| 抽 6 文件亲跑（regen+single） | — | quote **84/92**、jq_trans_module **65/65**、email_utils **3/4**、trade_live_broker **118/128**、cgroup_utils **7/8**（=FIX.md §5 基线口径，`set_cgroup_config` 基线既有失败）、quotation **152/153** —— 6/6 与 report 行逐项一致 | ✓ |

---

## §4 变体攻击表（复核独立攻击义务；探针 = `test_repros/round7/r7v7r_*` 5 文件 35 单元，py_compile→regen→single 三件套）

### §4.1 四守卫边界外变体（「不误伤」方向为主）

| 守卫 | 探针 | 变体形态（评审批未覆盖） | 读数 | 判定 |
|------|------|------------------------|------|------|
| B117 | r7v7r_b117_f2tail（7 单元） | f2 共享尾（宿主 if 包裹 for，回边块无区域外前驱，浅+深）；尾区域 else-continue 深度 2（宿主 else 臂并存，谓词应放行降级重排）；while 宿主 + 宿主顺序后继（B117 修复形态 while 变体，浅+深） | **6/7**：前 6 单元全 MATCH；`b117r_while_host_deep` 失败 → **B121**（见 §4.2，非守卫误伤——基线同败） | ✓ 不误伤（且浅层 `b117r_while_host` 由基线 FAIL 转 MATCH = B117 守卫在 while 宿主家族正向生效的直接证据） |
| B118 | r7v7r_b118_merge（7 单元） | ③ 拦住形态：两臂均 break 共享出口块（then 可达 merge，② 成立 ③ 不成立——不得二次注入 orelse=[Break]，浅+深）；② 拦住形态：then 尾跳共享汇合 + 体尾随语句（无 else，merge ∉ break_blocks，浅+深）；正向适用形态：while 宿主 else-break（浅+深，守卫应认领） | **7/7 全 MATCH** | ✓ 不误伤不漏接 |
| B120 | r7v7r_b120_break（7 单元） | break 落点专属本循环（函数级尾随块，无祖先 merge，浅+深）；fin_break（try/finally 内 break，r10_21 家族）；for-else + 独占 break 落点 + 尾随语句；宿主 if 假边与 break 边共享循环后汇合（守卫正向：祖先 merge 命中交宿主发射，浅+深） | **7/7 全 MATCH** | ✓ 不误伤（fin_break 等专属形态不触发确认） |
| B119 | r7v7r_b119_try（9 单元） | 收紧⑥ 拦住形态：merge ∈ **未完成生成** TryExceptRegion（try 体内 if + 尾随语句，浅+深）；merge 无任何 try 归属（BoolOp 汇合，neg_simple_and_or 家族，浅+深）；try 体内 if 真臂 return（g_in_try_except 家族，浅+深）；镜像守卫不触发：真实可抛 try 体 try/finally（块切分/finally_copy_blocks 非空，浅+深） | **9/9 全 MATCH** | ✓ 收紧⑥ 与镜像守卫边界正确 |
| （对照） | r7v7r_b121_whilehdr（5 单元） | B121 最小复现（见 §4.2） | 3/5（2 失败单元均为 B121） | —（破口探针） |

**变体攻击小结：四守卫「不误伤」方向 23/24 单元 MATCH；唯一失败经基线对照确证与四守卫无关（§4.2）。四守卫「漏接」方向未发现新破口（新破口 B121 属 while 头形成/识别侧，非 B117-B120 守卫面）。**

### §4.2 新破口登记：B121（编号自 B120 续接；**存量缺口，非本修复批回归**）

| 项 | 内容 |
|----|------|
| 锚点 | 识别侧 while 头形成/旋转 while 条件提升面（`core/cfg/region_analyzer.py` `_identify_loop_regions` :3782 一带 / R23-B LoopRegion.condition_block 旋转 while 家族，spec III.1）；**形态级定位**，行级锚点未逐行确证（如实声明） |
| 机制 | `if gate: while rest: BODY; if flag: continue`（while 为 if 体唯一语句）。3.11 rotate-while 布局：入口 guard 块（`POP_JUMP_FORWARD_IF_FALSE`→出口）、体尾底测条件（`POP_JUMP_BACKWARD_IF_TRUE`→体首）、体内 continue 的 `JUMP_BACKWARD` 落**入口 guard 块**；宿主 if 假边与 guard 同落出口块 ⇒ 入口 guard 块获得 back edge，被识别为**嵌套循环 header**，宿主 if 条件被提升为外层 while 条件 → 重建为 `while gate: while rest:`（字节码证据：gate@34 与 rest@38 双跳 90、continue@84 JUMP_BACKWARD→36）。gate 语义由「进入前测一次」变「每迭代重测」，宿主 if 区域消失，出口拓扑改变 → Different control flow |
| 违反条款 | 原则 2 每块唯一归属（宿主 if 条件块被 while 头吸收，IfRegion 消失）+ 原则 3 嵌套即抽象节点（if→while 复合误归约为嵌套 while）；对照无 continue 同构形态（b121r_minimal）3/3 MATCH ⇒ 纯形态破（非深度 onset） |
| 最小复现 | `test_repros/round7/r7v7r_b121_whilehdr.py::b121r_min_continue`（浅层即破）、`::b121r_min_continue_deep`；复核批原始发现 `r7v7r_b117_f2tail.py::b117r_while_host_deep` |
| 存量性证明 | 同探针在修复前基线 `49e5301b`（临时副本树外运行，零工作树改动）同样失败：r7v7r_b121_whilehdr **3/5 = 3/5**、r7v7r_b117_f2tail 基线 **5/7**（while_host 浅+深双败）vs 修复 **6/7**（浅层转 MATCH）——B117–B120 四守卫与本破口无关，且修复在该家族净改善 1 单元 |
| 当前 verify 读数 | r7v7r_b121_whilehdr = 3/5；r7v7r_b117_f2tail = 6/7 |
| 状态 | 已定位（形态级）；**移交下一修复批**（Round 7 修复批范围 = B117-B120，不含此项，不影响本批复核判定） |

---

## §5 II.7 十三条误解自查（复核结论宣告前逐条自检）

| # | 误解 | 本复核是否触犯 | 说明 |
|---|------|--------------|------|
| 1 | 循环论证分母 | 否 | 变体分母 = 探针源码单元，判据 = pyc_verify（外部 ruler），非实现枚举 |
| 2 | 有过就算 | 否 | 失败项逐一对照基线定位（B121），不略过；未把 MATCH 缺口当通过 |
| 3 | 语料证据口径 | 否 | 变体探针按守卫判据边界定向构造，非语料抽样 |
| 4 | 无限分母 | 否 | 变体集封闭（5 文件 35 单元），不随深度膨胀计分 |
| 5 | 节点词汇当完备 | 否 | 结论以 verify 字节等价 + 基线对照表达 |
| 6 | 浅层测试当无感证明 | 否 | 每变体文件含浅+深孪生；B121 浅层 onset 如实登记为纯形态，未以深层通过辩护 |
| 7 | 门禁读数当完备性 | 否 | 站桩/34 集读数仅作回归旁证；「通过」= 修复批封闭确认，非完备性宣告 |
| 8 | 顶层构造粗清单 | 否 | 攻击到判据面（19 hunk 逐块 + B121 字节码逐指令 diff） |
| 9 | 识别率当完备性 | 否 | 结论以 C1/C2/C3 与原则条款归属表达 |
| 10 | 维度互替 | 否 | 读数复跑（§3）/ 守卫边界（§4）/ 合规（§1）三维独立呈报 |
| 11 | 改工具不改方法 | 否 | 零 core/零工具改动；基线对照用树外临时副本（`git show` 只读提取），工作树零改动 |
| 12 | 错误检测标准 | 否 | 未涉 except*；PUSH_EXC_INFO/RERAISE 为 3.11 finally 帧口径，无 3.12 opcode 混用 |
| 13 | 语料上限当能力上限 | 否 | B121 登记未以「语料未见」作封闭依据；通过判定限定于本修复批范围 |

**自查结论：未触犯 II.7 任一条。**

---

## §6 结论与残余项

### 终判：**通过**

- 四破口 B117/B118/B119/B120 守卫封闭成立：7 复现全 MATCH（亲跑）、攻击面 122/122 + neg 18/18（亲跑全量重放，NEWFAIL=0）、站桩 6 面 WORSE=0（quotation 亲跑 + 5 面证据链核验）、34 集 1505/1568 NEWFAIL=0（合并自洽 + 6 文件亲跑一致）。
- 合规：19 个代码 hunk 判据全部落在 I.4 白名单；七前缀/深度/魔法偏移/新 self 状态/插桩新增均为 0；docstring 六项+C 条款齐备且与代码一致（1 项措辞观察 O1）；BOM 单头保持。
- 落地：FIX.md §9 锚点 20/20 实证在树（1 处 3 行漂移 O2）；§10「代码已落地」声明属实。

### 残余项移交

| # | 项 | 处置建议 |
|---|----|---------|
| 1 | **B121**（while 头形成/旋转 while 条件提升吸收宿主 if，存量缺口） | 移交下一轮修复批；识别侧 `_identify_loop_regions` 旋转 while 家族按 I.3 封闭（判据建议方向：入口 guard 块的 back edge 来源是否为该 while 自身 continue 语义边 + 宿主 if 假边与 guard 出口共享的区分，均属白名单结构事实） |
| 2 | regen 副作用（本复核重跑产生，依纪律未还原） | 10 个 M 态文件待主代理处理：`test_repros/round7/` 8 个 `r7v7_*OK.py`（b2b04/b2c02/b2c03/b4a03/b4c03/x_b2b04_d2/x_b2c03_pure/x_b4a03_pure）、`site-packages/IQEngine/plugins/plugin_system_trade/trade_live_brokerOK.py`、`.trae/.../rounds/round7/r7v7fix_probe_results.json`（仅时间戳字段 diff）。均为 regen 重跑副作用，非手改；regen 输出存在多MATCH渲染非确定性（如 x_b2b04_d2 重跑产出与源码结构逐字一致的正确渲染），verify 读数不受影响 |
| 3 | 新增复核探针（未跟踪，零覆盖既有文件） | `test_repros/round7/r7v7r_b117_f2tail.py/.pyc/*OK.py`、`r7v7r_b118_merge.py/...`、`r7v7r_b119_try.py/...`、`r7v7r_b120_break.py/...`、`r7v7r_b121_whilehdr.py/...`（B121 最小复现三件套，供修复批直接使用） |
| 4 | 观察 O1（镜像守卫 docstring「PUSH_EXC_INFO 开头」vs 代码存在性判定，行为等价）、O2（锚点 :22025→:22028 漂移） | 不构成打回；建议修复批顺手把 docstring 措辞对齐代码（「含 PUSH_EXC_INFO」） |

**本报告唯一新交付**：`rounds/round7/REVIEW2.md` + `r7v7r_*` 探针三件套；零 core 修改、零 git 写操作、未触碰 rounds/round1..6 证据与既有 r7v7_*/n7v7_* 探针文件本体。
