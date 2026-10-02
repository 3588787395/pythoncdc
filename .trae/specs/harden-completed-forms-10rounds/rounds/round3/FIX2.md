# Round 3 批次二 · 修复工程师报告（B11 破口：while 条件混合布尔链非名操作数装配灾难 + B1b 扩充：loop-else 上下文混合链）

## 1. 任务范围

| 项 | 内容 |
| --- | --- |
| B11（新破口修复） | r3_28 ×4 单元：`while_and_or`、`while_or_and`、`while_chain3`、`for_body_while_mixed`（`_detect_while_condition_boolop_chain` 非名操作数混合链装配灾难） |
| B1b 扩充（不新增编号） | r3_31 ×2 单元：`else_mixed_if`、`elif_chain_in_else`（B1b 签名 `if a and b or c:` → `if not (a and b):` 极性反转 + or 尾拆裂在 loop-else 上下文的新实例） |
| 验收标准 | 6 单元全 MATCH；批次一成果（r3_20 4/4、r3_22 5/5、r3_24 5/5、r3_25 4/4、r3_26 4/4、r3_27 9/9）零回退；负对照与基线守卫不变差；docstring 三要素同步维护；调试插桩零残留 |
| 硬约束遵守 | 全部判据为同层结构事实（块末 opcode 族、后继前驱集合、block_to_region 归属表）；无文件名/函数名白名单、无 start_offset 魔法阈值、无跨区域/跨层次启发式、无新增 self 跨方法状态、无以少发射换全绿；禁止手改 `*OK.py`（全部由 `python pycdc.py -o …OK.py …pyc` 再生成）；禁止 git commit |

## 2. 根因与机制

### 2.1 B11 四单元（r3_28）

CPython 3.11 旋转 while 把条件求值复制到回边重检处，混合链操作数块散布在 `loop.blocks` 之外；`_detect_while_condition_boolop_chain`（region_analyzer.py:24377）的 [B6-while 双向续接] 判据族只覆盖 `A and B or C` 单名操作数形态，四类非名操作数/变体形态各自断链：

1. **while_and_or / for_body_while_mixed（3 循环整体消失）**：生成层 `_loop_generate_while` 与 `_loop_handle_header` 两处把 `RegionASTGenerator._is_equivalent_exit_block` 当作自身方法调用（region_ast_generator.py 原 :6632/:8321）——该方法实际定义于 `RegionAnalyzer`（region_analyzer.py:28799）。跨类调用抛 `AttributeError`，被 :1818 `except Exception` 吞掉走 `_generate_degraded_statements` 逐语句降级，While 节点整体消失（`while_and_or` 31→11 指令）。r1_10 不触发是因其 header 尾非 FORWARD 条件跳转（gate 未进入该路径）。
2. **while_or_and（or 组前置）**：`while (a or b) and k < m:` 的 or 成员真出口汇入 and 组尾（块 0 PJT→18∈链内），后向回溯的 `cond_in_loop` 判据对 or 成员不成立（其 fall-through 是下一条件成员而非体语义块）且游标可能先命中 or 成员提前中断——backward walk 只收到单元素链 [(18,'and')]，整链被 all_same_target 旧路丢弃。
3. **while_chain3（or 尾多成员）**：`while a and k < m or b and d:` 的 or 尾是 and 组（b、d 两块），原判据「PJF 且 fall-through≠header 即终止」使 or 尾中间成员（块 30）无法入链；且块 30 已被主扫描装配的残链 BoolOpRegion [26,30]（后被 [14,26,30] 修正）认领，`block_to_region.get(30) is not None` 一票否决直接 break。
4. **for_body_while_mixed（外层 for 包裹）**：内层 while 链首块（`j = 0; j < i`）被外层 for LoopRegion 认领（自然循环体收集把体首块并入），所有权校验的祖先豁免只查 `region.parent` 链——后置阶段 parent 链未连接（子循环区域在主扫描产出、树装配在其后），豁免失效 → 完整链 [(38,'and'),(56,'or'),(60,'and')] 被否决，生成器消费残链 b4w=[56,60]。

### 2.2 B1b 扩充两单元（r3_31）

`for …: … else: if a and b or c:` 的 or 尾操作数块（假边→循环后汇合、真边 fall-through→then 体）被外层 LoopRegion 按 **else 体范围**认领（`_find_loop_else` 把自然出口 else 体并入 blocks 并登记 block_to_region）。`_try_unify_mixed_boolop_chain` 的 [B1b fix-r2] LoopRegion 认领豁免只覆盖 `body_blocks`（region_analyzer.py 原 :27871 `ft_succ not in _ft_reg.body_blocks` 即 break），else 上下文 or 尾被整体排除——残链 [(100,'and'),(104,'or')] 的 and→or 边界导致消费端极性整体反转（`if not (a and b):`）且 or 尾成孤片（`if c: pass` / `elif a: pass` 拆裂）。探针实证：`unify claim ft=108 owner=LoopRegion in_body=False in_else=True`。

## 3. 修复方案（锚点均为收尾后实际行号）

### FIX-B11a 生成层 · `_is_equivalent_exit_block` 跨类调用修正
region_ast_generator.py:6603、:8276：`self._is_equivalent_exit_block(...)` → `self.region_analyzer._is_equivalent_exit_block(...)`。AttributeError 消除，3 循环 While 节点恢复装配。

### FIX-B11b 识别层 · 所有权校验祖先豁免（region_analyzer.py:24191-24220）
链块认领者豁免判据扩为两条同层结构事实：① `region.parent` 链上的祖先 LoopRegion；② **结构判据**——认领者是 LoopRegion 且其 blocks 含纳本循环 header（= 外层循环体收集把「体首块 + 本链首操作数」双重角色块并入其自然循环体）。②不依赖 parent 链装配时序，覆盖后置阶段树未连接的情形；非循环区域认领者维持一票否决。

### FIX-B11c 识别层 · while 混合链双向续接补全（region_analyzer.py）
- **c-1 链首守卫豁免（:24590）**：reeval 变量守卫无交集时，若链首假边目标满足「未认领 + PJF 收尾 + 假目标在体语义/loop.blocks 之外」（or 尾首成员特征，B6 边界闭合的镜像）→ 豁免入链。
- **c-2 or 尾多成员续接（:24880）+ 残链认领成员放行（:24898）**：or 尾中间成员假边→统一假出口、真边沿 fall-through 推进；候选块被 **BoolOpRegion**（将被超越替换的残链）认领时放行交 Step 5 统一裁决，非 BoolOpRegion 认领者维持否决。
- **c-3 or-前缀续接（:24676）**：or_left 形态补全——链首 fall-through==header（完备性闭合）、or 成员 PJT∈{cond_block}∪已收链块（真出口汇入链内）、and 成员 run 逐块 PJF 收尾且假目标在体语义集合外推进至链首；补全链 [(A,'or'),(B,'and'),…,cond] 交 `_create_boolop_region_from_chain`，生成器经 `_detect_boolop_grouping`（INNER 信号=or 成员真边目标∈链块集合）重建 `and[or[A,B], k<m]`。

### FIX-B11d 识别层 · 残链超越替换泛化（region_analyzer.py:24164-24240）
被超越残链从「单一 owning_br（entry∈chain[1:]）」泛化为集合判据：与链块相交 ∧ entry∈链块 ∧ op_chain 严格更短。覆盖前缀残链（`[a or b]`，entry=链首，主扫描自链首前向装配的不完整产物）；原 [B6] 否决权保留（含 condition_block 的 BoolOpRegion 未满足超越判据时跳过后置重装配）。

### FIX-B11e 识别层 · loop-else 范围认领豁免（region_analyzer.py:27827-27939）
`_try_unify_mixed_boolop_chain` 的 LoopRegion 认领豁免扩展：候选块 ∈ `else_blocks`（范围认领面，与 body_blocks 同构）且 ≠ header_block 时放行；链首守卫同 body 豁免（本链不是循环自身条件装配——链首≠该 Loop header/condition_block）；else 上下文不套用 `_b1b_loop_body_run_continuation`（其 (2) 臂三元真值块守卫对 if-else 形 or 尾误报，与 try 豁免分支同一取舍），放行后落到与未认领候选完全相同的验收路径（多成员 run 交 `_detect_boolop_conditional_chain`，单成员 or 尾交 [B1b] 三判据）。

### docstring 三要素同步
`_detect_while_condition_boolop_chain`（:24377）与 `_try_unify_mixed_boolop_chain`（:27790 附近）docstring 的识别条件/归约方式/AST 映射随判据扩展同步更新；新增判据处均带 [C1]/[C2]/[C3] 条款标注。

### B6/B7 封闭声明降格落实
- B6 封闭声明由「while 条件混合链浅层封闭」降格为「**`A and B or C` 单名操作数浅层封闭**」；本轮 FIX-B11b/c/d 落实后扩展覆盖：比较操作数（`k < m`）、or 组前置（`(a or b) and k < m`）、三操作数链（`a and k < m or b and d`）、外层循环包裹变体——以 r3_28 四单元 MATCH 为证。
- B7「深层才错、浅层没事」签名修正落实：浅层非名操作数混合链同属破口面（REVIEW §4 B11 登记），r3_28 浅层复现（31→11 指令级灾难）已修复归零。

## 4. C1/C2/C3 条款声明（全部修复点）

| 修复点 | C1 局部消费 | C2 黑箱组合 | C3 守卫封闭 |
| --- | --- | --- | --- |
| FIX-B11a | ✓ 只改调用目标为既有分析器方法，无新信息读取 | ✓ 不变 | ✓ 不变 |
| FIX-B11b | ✓ 只读 block_to_region 归属表 + LoopRegion.blocks 成员关系 | ✓ 完整链交单 BoolOpRegion | ✓ 祖先豁免双判据（parent 链 / header∈blocks），非循环认领者一票否决 |
| FIX-B11c-1 | ✓ 只读 pred 假边目标与其块末 opcode 族、体语义集合 | ✓ 同上 | ✓ 三重豁免子条件（未认领 + PJF + 假目标出体） |
| FIX-B11c-2 | ✓ 只读块末 opcode 族、后继身份、归属表 | ✓ 同上 | ✓ 残链认领者必须是 BoolOpRegion（超越替换统一裁决），其他区域类型否决 |
| FIX-B11c-3 | ✓ 只读链首 fall-through、or 成员 PJT∈链块、and run 假边出体 | ✓ 同上 | ✓ or 成员/and run 成员未认领或仅残链 BoolOpRegion 认领；guard<16 防环 |
| FIX-B11d | ✓ 只读残链 blocks/entry/op_chain 与链块集合同层关系 | ✓ 撤销残链后按完整链重建 | ✓ entry∈链块 ∧ 相交 ∧ op_chain 更短三判据；原 [B6] 否决权保留 |
| FIX-B11e | ✓ 只读 else_blocks/body_blocks 成员关系与块末 opcode 族 | ✓ 补全链交 `_create_boolop_region_from_chain` | ✓ 链首守卫（≠header/condition_block）+ 标准验收路径，任一不成立维持 break，LoopRegion 认领面零扩大 |

## 5. 自测读数全表（收尾干净代码上复跑）

### 5.1 目标单元（6/6 转 MATCH）

| 文件 | 修复前 | 修复后 | 读数 |
| --- | --- | --- | --- |
| r3_28_while_mixed_chain（4 单元） | 1/5（4 失败） | while_and_or=`k < m and a or c`；while_or_and=`(a or b) and k < m`；while_chain3=`a and k < m or (b and d)`；for_body_while_mixed=`j < i and a or c` | **5/5 100%** |
| r3_31_else_mixed_if（2 单元） | 3/5（2 失败） | else_mixed_if=`if a and b or c:`；elif_chain_in_else=`elif b and c or a:` | **5/5 100%** |

### 5.2 批次一成果保持（零回退）

| 文件 | 读数 |
| --- | --- |
| r3_20_for_else_break_exit | 4/4 100% |
| r3_22_loop_else_return_continue | 5/5 100% |
| r3_24_double_loop_break | 5/5 100% |
| r3_25_triple_for_else | 4/4 100% |
| r3_26_while_for_mixed | 4/4 100% |
| r3_27_loop_try_with_match | 9/9 100% |

### 5.3 负对照（判据无误报）

| 文件 | 读数 |
| --- | --- |
| n3_01_simple_loops | 5/5 100% |
| n3_02_guard_and_else | 5/5 100% |
| r3_21_for_else_empty | 5/5 100% |
| r3_23_if_break_continue_guard | 5/5 100% |
| r3_30_for_unpack_async | 5/5 100% |
| r3_32_comp_loop_interleave | 11/11 100% |

### 5.4 round1 B6 基线 + round2 抽验（不变差）

| 文件 | 本轮读数 | 登记/基线 | 判定 |
| --- | --- | --- | --- |
| IQCommon/strategy/jq_trans_module | **65/65 100%** | 65/65 | ✓ 保持 |
| round2/r2_09_finally_mixed_boolop | 2/3 | 2/3（B9 消费层登记残留） | ✓ 不变差 |
| round2/r2_10_trybody_mixed_boolop | 2/4 | 2/4（round3 REVIEW §3 行68 同读数） | ✓ 不变差 |

### 5.5 site-packages 基线守卫（不变差）

| 文件 | 本轮读数 | 基线 | 判定 |
| --- | --- | --- | --- |
| fly/data/quotation | 152/153 99.35% | 152/153 | ✓ 持平 |
| fly/data/quote | 84/92 91.30% | ≥84/92 | ✓ 持平下限 |
| IQEngine/.../trade_live_broker | 118/128 92.19% | ≥118/128 | ✓ 持平下限 |
| IQEngine/.../risk_calculation | 29/29 100% | 41/43（验证器单元口径不同，round3 FIX.md §5.5 已注记） | ✓ 比例不低于基线 |

### 5.6 产物健康

全部 `*OK.py` 由 `python pycdc.py -o <路径>OK.py <路径>.pyc` 再生成，无手改；r3_28/r3_31 产物 diff 仅剩 banner/`__doc__`/空行标准差异，代码语义逐行一致。

## 6. 调试插桩清理确认

`grep R3B11|_r3b2|_r3b11|_os_bw|_os_b6|_os_g2|_os_wg|_os_dg` 于 `core/` 零命中；region_ast_generator.py 生成路径 except 分支恢复为纯降级逻辑（R3B11DBG 钩子与 DEGRADED 探针移除）。临时文件已删除：`_r3b2_run.py`、`_r3b2_probe.py`、`_r3b2_unprobe.py`、`_r3b2_patch_dbg*.py`、`_r3b11_dbg.log`、`_r3b2_stderr.txt`、`e1.txt`、`err*.txt`、`test_repros/round3/_r3_b2_tmp*OK.py`、`r3b11_result.txt`。修复过程中两次 Edit 引入的 UTF-8 BOM（U+FEFF）已全部剥离并经 `ast.parse`/`py_compile` 校验。

## 7. 遗留与建议

1. **B9 消费层残留维持登记**：r2_09 g 单元 / r2_10 f_while+f_ternary 单元失败为 TernaryRegion/消费端问题（本轮修复的识别层续接已使 r2_10 f_while 症状改善，round2 FIX.md §194-195 注记），不在本批范围。
2. **risk_calculation 读数口径**：验证器单元口径（29 units）与历史记录（41/43）不同源，延续 round3 FIX.md 建议——下轮以同一验证器版本固化基线读数。
3. **观察点待实证**：R3-O1（跨循环 continue 身份守卫）、R3-O2（WHILE 分支 try/finally clamp 对称性）本轮语料零触发，维持观察。
4. `_loop_generate_while` 内 `boolop_for_while` 前缀分段（pre_stmts）与 or_groups 分组重建在 5.1 全形态下验证通过；or-前缀续接（FIX-B11c-3）的 and run 推进 guard 上限 16 为防环护栏（正常混合链 ≤4 成员，不会触及）。
