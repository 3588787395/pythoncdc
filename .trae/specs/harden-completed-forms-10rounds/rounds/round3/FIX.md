# Round 3 批次一 · 修复工程师报告（B10 破口：loop-else×break 证据链失效族）

## 1. 任务范围

完成 B10 破口剩余 5 个 MISMATCH 单元的算法修复（REVIEW.md §2/§4 锚点）：

| # | 文件 | 单元 | 修复前 | 修复后 |
|---|------|------|--------|--------|
| 1 | r3_20_for_else_break_exit.pyc | while_else_break_exit | MISMATCH | MATCH |
| 2 | r3_20_for_else_break_exit.pyc | else_break_with_flag | MISMATCH | MATCH |
| 3 | r3_22_loop_else_return_continue.pyc | for_else_continue_outer | MISMATCH | MATCH |
| 4 | r3_25_triple_for_else.pyc | triple_for_mixed_break | MISMATCH | MATCH |
| 5 | r3_27_loop_try_with_match.pyc | loop_try_with_break | MISMATCH | MATCH |

（r3_20 的 inner_break_out 已由前序会话修复，本轮保持。）

## 2. 根因与机制

B10 族的双签名拆解为识别层（R3-A）与生成层（R3-B）两类：

- **R3-A（识别层）**：`_find_loop_else`（region_analyzer.py :5343-5361 docstring）的 break 证据链在两类合法形态下失效——
  (a) **no-break 路径**：for 循环无显式 break 时，for_iter_exit 的前驱中存在 ∉ body 的条件跳转落点（如 `else: break` 的 else 体经 JUMP_FORWARD 汇入），旧逻辑不将其计为 break 证据 → else 被误归约为循环后顺序代码；
  (b) **break_targets 路径**：else 体是**纯跳转桩**（单条 JUMP_BACKWARD(_NO_INTERRUPT) 回循环头）时，旧 `_else_only_pure_jump` 元组含 JUMP_BACKWARD，把「else: continue」形态误判为「else 体并入循环体」→ else 丢失。
- **R3-B（生成层）**：即使识别层已归约出 else/break 结构，生成层仍有三处证据链断裂——
  (c) **落点过度认领**：`if c: break` 的真臂是独立纯跳转桩块，其跳转落点（循环 break 落点）被 if-builder 吸收进臂集合；子区域臂渲染止于 Break 语句（:22749-22752 将后续块登记进 `_post_break_blocks` 搁置台账后跳过），落点内容**从未发射**，但渲染完成后的整区域台账登记已将其标记 generated → R102/R58 循环后发射路径因 generated 守卫跳过 → 落点语句（acc.append(t) 等）丢失；
  (d) **else 桩语义降级**：for-else 体为 `continue`（绑定外层循环）时，else 桩块是纯 JUMP_BACKWARD 回**本**循环头，旧生成路径丢弃该桩 → 外层 continue 丢失；
  (e) **break 落点子区域双归属**：break 落点块（如 `if i == 1: break` 的落点 196）同时是祖先循环的 break_blocks 成员与某 IfRegion 臂集合成员，IfRegion 子区域派发在**内层循环体内**发射了它 → 应由祖先循环 R102 在循环后发射的语义被提前/错位。

## 3. 修复方案（锚点均为实际行号）

### FIX-1 识别层 · no-break 路径 break 证据前驱扫描
- 位置：`core/cfg/region_analyzer.py` :5536-5570（实现）、:5343-5354（`_find_loop_else` docstring 增补）
- 机制：for_iter_exit 前驱扫描——存在 ∉ body_set、非异常边、末条为 JUMP_FORWARD/JUMP_ABSOLUTE 的前驱时，判为 break 证据 → `return None, natural_exit`（else 归约终止，落点交由循环后顺序发射）。
- 触发单元：r3_20 while_else_break_exit / else_break_with_flag。

### FIX-3 识别层 · `_else_only_pure_jump` 元组收窄
- 位置：`core/cfg/region_analyzer.py` :5480-5520（实现）、:5355（docstring）
- 机制：纯跳转 else 判定元组从含 JUMP_BACKWARD 收窄为 `('JUMP_FORWARD', 'JUMP_ABSOLUTE')`——JUMP_BACKWARD 桩是「else: continue」回边，不再判伪并入循环体。
- 触发单元：r3_22 for_else_continue_outer（与 FIX-5 配合）。

### FIX-2a 生成层 · R102 归零落点放行 + `_post_break_blocks` 收窄判据
- 位置：`core/cfg/region_ast_generator.py` :5361-5401（R102 elif）
- 机制：break 落点解析回本循环/生成中祖先（归零 None）且 ∉ 本循环 else_blocks、且 **∈ `_post_break_blocks` 搁置台账**（臂渲染止于终止语句时的搁置登记 = 内容未发射的同层结构证据）时，从 generated_blocks 台账摘除后按普通块发射进 `_sequential_after_loop`，发射后补登记。
- **收窄判据（本轮关键修正）**：初版仅判「归零 ∧ ∉ else_blocks」即放行，导致 quotation get_str_data（落点 838 ∈ IfRegion@762 else_blocks 且为条件跳转**直接目标**，臂渲染经 BREAK 角色分支 :22849 `_generate_block_statements` **真实消费**、产出 `[Assign, Break]` 完整进 If 节点 orelse）被二次发射 → 152/153 回归 151/153。收窄为「必须 ∈ 搁置台账」后：r3_20 落点 96（臂尾纯跳转桩落点、被搁置、从未消费）仍放行，838（已被消费、不入台账）维持原守卫逐位跳过。
- 触发单元：r3_20 while_else_break_exit（落点 96）。

### FIX-2b 生成层 · R58 归零落点放行（与 FIX-2a 对称）+ 臂集合守卫
- 位置：`core/cfg/region_ast_generator.py` :5477-5510（结构化子区域分支的 `_r3b10_child_emits` 臂集合守卫）、:5513-5532（归零 elif 收窄，与 FIX-2a 同判据）
- 机制：落点被已生成/生成中结构化子区域认领时，仅当其 ∉ 子区域任何臂集合（body/else/then/try/handler/finally）才放行发射（臂集合成员的内容已随子区域臂渲染消费，如 r3_20 else_break_with_flag 落点 98 ∈ 内层 else_blocks）；归零 elif 与 FIX-2a 同样以 `_post_break_blocks` 收窄。
- 触发单元：r3_27 loop_try_with_break（return acc 块 342）、r3_22（落点 136）。

### FIX-4 生成层 · BREAK 分支双 Break 补发守卫
- 位置：`core/cfg/region_ast_generator.py` :22838-22850（`_process_if_blocks` BREAK 分支）
- 机制：BREAK/PURE_BREAK 角色块经 `_generate_block_statements` 产出的语句列表末条已是 Break 时不再追加显式 Break，防止 `break` 后接终止语句的臂渲染产出双 Break。
- 触发单元：r3_27 loop_try_with_break（elif i==5 臂块 104）。

### FIX-5 生成层 · else 桩 JUMP_BACKWARD 归约为 Continue
- 位置：`core/cfg/region_ast_generator.py` :5135-5179（`_loop_generate_for` 内 R58-B Break 归约之后）
- 机制：for 循环 else_stmts 为空且 `_filtered_else_blocks` 每块去噪后恰一条 JUMP_BACKWARD(_NO_INTERRUPT)、且任一后继 ∈ 祖先链 LoopRegion.header_block 集合时，该桩是「continue 绑定外层循环」→ `else_stmts = [{'type': 'Continue'}]`，桩块标记 generated。
- 触发单元：r3_22 for_else_continue_outer、r3_25 triple_for_mixed_break。

### FIX-6 生成层 · 祖先循环 break 落点子区域抑制
- 位置：`core/cfg/region_ast_generator.py` :15865-15895（`_if_generate_then_branch` 子区域派发处）
- 机制：派发子区域前沿 region.parent 找最近包围 LoopRegion；子区域 entry ∈ 该循环 break_blocks（`_r3b10_post_loop_child`）时跳过本层生成，交由该循环 R102 后循环发射，消除 break 落点的双归属错位发射。
- 触发单元：r3_25 triple_for_mixed_break（@196）。

## 4. C1/C2/C3 条款声明（全部修复点）

- **C1（局部消费）**：只读同层结构事实——区域成员集合（then/else/body/break_blocks）、块末 opcode 与后继/前驱集合、BlockRole、生成器既有台账（generated_blocks/_post_break_blocks）。无文件名/函数名白名单、无 start_offset 魔法阈值、无跨区域/跨层次启发式、无新增 self 跨方法状态（`_post_break_blocks` 为既有台账 :289，本轮仅接上消费者）。
- **C2（黑箱组合）**：父区域经子区域入口引用（_generate_region / _sequential_after_loop / R58 递归），落点语句在循环节点后的顺序位置唯一发射一次（发射后立即补登记 generated）。
- **C3（守卫封闭）**：放行仅发生在「落点 ∈ 搁置台账（内容未发射）」时；落点 ∈ else_blocks、∉ 搁置台账（已被臂渲染消费）或归属结构化子区域臂集合时维持原守卫逐位不变。不命中修复判据的路径与旧实现逐位一致。

## 5. 自测读数全表（收窄判据终态）

### 5.1 目标单元（5/5 转 MATCH）
| 文件 | 修复前 | 修复后 |
|------|--------|--------|
| r3_20_for_else_break_exit | 2/4 | **4/4** |
| r3_22_loop_else_return_continue | 4/5 | **5/5** |
| r3_25_triple_for_else | 3/4 | **4/4** |
| r3_27_loop_try_with_match | 8/9 | **9/9** |

### 5.2 已修 10 单元保持（零回归）
| 文件 | 读数 |
|------|------|
| r3_21_for_else_empty | 5/5 ✓ |
| r3_23_if_break_continue_guard | 5/5 ✓ |
| r3_24_double_loop_break | 5/5 ✓ |
| r3_26_while_for_mixed | 4/4 ✓ |
| r3_30_for_unpack_async | 5/5 ✓ |
| r3_32_comp_loop_interleave | 11/11 ✓ |

### 5.3 基线守卫（不变差）
| 文件 | 本轮 | 基线 |
|------|------|------|
| r3_28_while_mixed_chain | 1/5 | 1/5 ✓ |
| r3_31_else_mixed_if | 3/5 | 3/5 ✓ |

### 5.4 负对照
| 文件 | 读数 |
|------|------|
| n3_01_simple_loops | 5/5 ✓ |
| n3_02_guard_and_else | 5/5 ✓ |

### 5.5 site-packages 防回归抽验（6 支）
| 文件 | 本轮读数 | 基线 | 结论 |
|------|----------|------|------|
| fly/data/quotation | 152/153（唯一失败 change_his_to_forward） | 152/153 | ✓（初版 FIX-2a 曾致 get_str_data 回归 151/153，收窄后恢复） |
| IQCommon/strategy/jq_trans_module | 65/65 | 65/65 | ✓ |
| IQEngine/plugins/plugin_system_trade/trade_live_broker | 118/128 | ≥118/128 | ✓ |
| fly/data/quote | 84/92 | ≥84/92 | ✓ |
| IQEngine/plugins/plugin_system_risk_calculation/risk_calculation | 29/29（100%） | 41/43（95.3%） | ✓（验证器单元口径不同，比例不低于基线） |
| IQEngine/plugins/plugin_system_event_source/realtime_event_source | 12/13 | 12/13 | ✓ |

### 5.6 round1/2 抽验
| 文件 | 读数 |
|------|------|
| round76/r76_b1a_jqcond | 5/5 ✓ |
| round2/r2_08_loop_tail_branches | 8/8 ✓ |
| round2/r2_08_handler_mixed_boolop | 3/3 ✓ |
| round2/r2_11_minimal_with_break | 3/3 ✓ |
| round2/r2_11_except_star_single | 2/2 ✓ |

## 6. R3DBG_GUARD 调试插桩清理确认

grep（R3DBG 模式）结果：`core/`、`scripts/`、`pycdc.py` 均 **No matches found**——树中零残留。临时探针（_probe_r3b/_probe_r3c/_probe_r3d/_probe_dis/_probe2_r3）与临时差分文件（_tmp_*）已全部删除。

## 7. 遗留与建议

- risk_calculation 的读数口径（29 units vs 历史记录 41/43）建议下轮以同一验证器版本固化基线读数。
- r3_28（1/5）、r3_31（3/5）为 B11/B1b 范围（`_detect_while_condition_boolop_chain` / `_build_boolop_expression` 家族），本轮按纪律未触碰。
