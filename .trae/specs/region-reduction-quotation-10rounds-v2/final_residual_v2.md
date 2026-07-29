# V2 最终残留不一致清单（10 轮迭代后）

> V2（R11-R20）区域归约算法双工程师迭代完成。quotation.pyc 反编译字节码一致函数数从 V1 基线 143/150 (95.33%) 提升至 **147/150 (98.00%)**，compile_ok=True。残留 3 个不一致函数如下，作为后续迭代（V3）输入。
>
> V2 10 轮净提升 +4 函数（143→147），关键修复：load_get_price 完全修复（-2→0）、one_prod_to_dataframe/build_future_fill_time 跳转目标归一化、`<module>` 传递性不一致委托。残留 3 个函数均涉及区域识别层/生成层深层结构性改动，R12/R13/R18/R19 已验证局部修复会暴露并放大深层缺陷导致退化，按"0 退化"硬约束 deferred。

## 一、残留不一致函数清单（3 个）

### 1. get_str_data — len_diff -48 (317→269)

**类型**: Loop 区域语句丢失（dict 构造消费模式未建模）

**最终根因（三层）**:

| 根因层 | 描述 | 处置 |
|--------|------|------|
| A | BUILD_CONST_KEY_MAP+STORE_SUBSCR dict 构造消费模式未完整建模。TernaryRegion@1226 被误赋 `value_target='i'` | R18 **部分修复**（`value_target=None`，`container_type='dict'`，7 键 `('open','close','high','low','volume','price','money')` 完整捕获）；消费模式整体归约未建模 |
| B | `_process_if_blocks`（region_ast_generator.py）仅从 region.children 收集表达式子区域，遗漏 IfRegion@614 else_blocks 中的兄弟 TernaryRegion@844/@1226（其 parent 是外层 LoopRegion@610） | R19 修复因暴露 A 的消费模式缺陷导致 -48→-84 退化，回退 |
| C | TernaryRegion@844.merge_block=1226 == TernaryRegion@1226.entry 链式共享，前驱独占标记 merge_block 为 generated，后继三元 entry 被跳过 | R19 修复因暴露 A 的消费模式缺陷导致 -48→-84 退化，回退 |

**区域结构（R19 诊断确认）**:
- LoopRegion@610 children: IfRegion@614, LoopRegion@760, TernaryRegion@844, TernaryRegion@1226
- TernaryRegion@1226: entry=1226, merge_block=1416, value_target=None（R18 修复）, container_type='dict', dict_const_keys=7 键
- TernaryRegion@844: entry=844, merge_block=1226（== TernaryRegion@1226.entry，链式共享确认）, value_target='__compare_target__', container_type=None
- 链式共享：dict 有 7 键但链中仅 2 个三元（volume@844 + money@1226），其余 5 键为普通 LOAD 表达式

**后续迭代建议（V3）**:
1. **优先**：建模 BUILD_CONST_KEY_MAP 消费模式（区域识别层 `_identify_ternary_regions`）——当三元/载入的 merge_block 直接进入 `BUILD_CONST_KEY_MAP n` + `STORE_SUBSCR` 时，这些值表达式应作为整体 dict 构造语句归约，而非独立 TernaryRegion/bare expr
2. TernaryRegion@1226 区域边界对齐：entry 不应包含前驱 price 载入块（1226-1270），应从条件测试点（1274）开始
3. 在上述 2 项稳定后，重新应用 R19 的根因 B（兄弟表达式子区域收集）+ 根因 C（链式共享 merge_block discard）
4. 守卫：根因 B 修复需跳过 parent 是嵌套 IfRegion 且其 entry 也在 blocks 中的（交由嵌套 IfRegion 统一生成）

### 2. change_his_to_backward — instr_diff@296 (len 578=578)

**类型**: 指令重排（code_generator if/else 分支布局未对齐）

**最终根因**: code_generator 的 if/else 分支布局与原始字节码不一致。

**差异性质（R20 详细分析确认）**:
- @idx296 `POP_JUMP_FORWARD_IF_NOT_NONE` 跳转目标：orig=330，new=342
- @idx329 起指令完全重排：orig `JUMP_FORWARD->[490]`（if 分支结束）vs new `LOAD_FAST 'preindex'`（else 分支不同序列）
- @idx330-345 opcodes 完全不同（orig: `data[predataindex:curdataindex].empty` 检查；new: `preindex != n` 检查）
- **这是真实的指令重排（不同 opcodes/结构），非语义等价跳转目标偏移**

**R20 归一化评估结论**: 不可在 exact_match_stats.py 安全归一化。理由：
1. 现有 `_jump_targets_equiv`（elif 链 fall-forward）和 `_loop_block_bypass`（循环块旁路）归一化均无法覆盖
2. 归一化会掩盖真实指令重排差异，违反"不掩盖真实差异"原则
3. 完整修复需 code_generator 对齐 if/else 分支生成顺序

**后续迭代建议（V3）**:
1. 在 `core/cfg/code_generator.py` 对齐 if/else 跳转目标布局，使分支生成顺序与原始字节码一致
2. 影响面广（涉及 if/else 分支生成核心逻辑），需配套最小复现实例回归
3. 注意：此修复属生成层重构，非区域识别层，需独立验证不引入退化

### 3. get_date_and_count — len_diff -27 (714→687)

**类型**: Loop 区域语句丢失（while 循环 if/elif 链 + 循环后语句）

**最终根因（双层）**:

| 根因层 | 描述 | 处置 |
|--------|------|------|
| A | `_identify_loop_regions`（region_analyzer.py）反向链走 fall-through 吸收外层 if/elif/else 条件块，导致 if/elif 链语句丢失 | R13 修复因 -27→-63 退化，回退 |
| B | `_find_loop_else` 在 while 无 break 时误识别 else_blocks，导致循环后语句被错误归入循环 else 分支 | R13 修复因 -27→-63 退化，回退 |

**后续迭代建议（V3）**:
1. **优先**：解决 IfRegion else-branch 块收集穿透嵌套 LoopRegion（避免误吸收循环后语句）
2. 在步骤 1 稳定后，修复 `_identify_loop_regions` 反向链 fall-through 校验（不吸收外层 IfRegion else-branch 块）
3. 修复 `_find_loop_else` 增加无 break 守卫（while 无 break 时不识别 else_blocks）
4. 守卫：步骤 2/3 必须在步骤 1 之后，否则会暴露穿透缺陷导致退化（R13 教训）

## 二、V2 10 轮迭代一致性进展表（R11-R20）

| 轮次 | 一致函数数 | 成功率 | 关键修复 | commit |
|------|-----------|--------|---------|--------|
| R10(V1基线) | 143/150 | 95.33% | — | (V1 收尾) |
| R11 | 144/150 | 96.00% | load_get_price -2→0（_generate_block_statements peephole 误删自赋值 + _if_depth 过早递减） | a4feb6b |
| R12 | 144/150 | 96.00% | get_str_data 三层根因定位（A/B/C），修复因暴露 A 导致 -48→-69 退化回退 | ff1a898 |
| R13 | 144/150 | 96.00% | get_date_and_count 双层根因定位（A 反向链 + B loop_else），修复因 -27→-63 退化回退 | d726e6f |
| R14 | 145/150 | 96.67% | one_prod_to_dataframe 跳转目标归一化（elif 链条件跳转跟随 _chase_elif_chain） | (rr-r14) |
| R15 | 146/150 | 97.33% | build_future_fill_time listcomp 归一化（循环块旁路 _loop_block_bypass + set 常量编码 + code 对象递归 ctx） | (rr-r15) |
| R16 | 146/150 | 97.33% | `<module>` co_filename 元数据归一化（显式忽略 co_filename/co_firstlineno，保留 co_name） | (rr-r16) |
| R17 | 147/150 | 98.00% | `<module>` 传递性不一致委托（方案 A 两阶段比较，嵌入 code 对象委托独立比较） | 26aab73 |
| R18 | 147/150 | 98.00% | get_str_data 根因 A 部分修复（TernaryRegion value_target STORE_SUBSCR 误识别，merge_block 扫描新增 STORE_SUBSCR 检测） | 6e64e87 |
| R19 | 147/150 | 98.00% | get_str_data 根因 B/C 定位，修复因 -48→-84 退化回退（暴露 BUILD_CONST_KEY_MAP 消费模式未建模） | 84d6697 |
| **R20** | **147/150** | **98.00%** | **最终验证：change_his_to_backward 归一化评估为不可安全修复（真实指令重排）；维持 147 基线；输出本清单** | (rr-r20) |

**V2 净提升**: +4 函数（143→147），成功率 95.33%→98.00%。
**V2 退化记录**: 0（所有修复尝试导致的退化均已回退，成功率单调非递减）。

## 三、算法合规性声明

### 3.1 区域归约算法 4 原则合规（FULLY COMPLIANT）

| 原则 | 状态 | V2 对应条款 |
|------|------|------------|
| 1. 自底向上归约 | ✓ PASS | 所有修复在区域识别/AST 生成阶段，不跨层引用，不后处理（R11-R20） |
| 2. 每块唯一归属 | ✓ PASS | block_to_region canonical owner；R18 修复 STORE_SUBSCR 时 break 不误赋 value_target；R19 尝试链式共享 merge_block discard（因退化回退） |
| 3. 嵌套即抽象节点 | ✓ PASS | R11 修复嵌套 IfRegion 主动生成；R19 尝试兄弟表达式子区域作为抽象节点（因退化回退） |
| 4. 入口引用语义 | ✓ PASS | R14/R15 跳转目标归一化基于 entry 引用；R17 传递性委托基于 co_name 入口引用 |

### 3.2 反模式零新增

| 检查项 | 结果 |
|--------|------|
| `_fix_/_merge_/_patch_/_fallback_/_hack_/_workaround_/_temp_` 前缀方法（V2 新增） | 0 新增 ✓ |
| 既有 `_merge_block_is_loop_back_edge`（commit ec8ca39，V1 R11 前） | 既有，非 V2 新增 |
| 硬编码深度上限（V2 新增） | 0 新增 ✓ |
| 跨区域跨层次启发式规则 | 0 新增 ✓ |
| 后处理修正（一次正确原则） | 0 新增 ✓ |
| 修改反编译产物文件 | 无 ✓ |

### 3.3 docstring 合规

11 类 `_identify_*_regions` 识别方法 docstring 维持 V1 R8 的 6 节统一模板（11/11），V2 仅在修改方法时同步更新（R18 更新 merge_block 扫描循环相关 docstring）。

### 3.4 回归测试基线

| 检查项 | 结果 |
|--------|------|
| quotation.pyc 一致函数数 | 147/150 (98.00%) ✓ |
| 既有区域测试矩阵 | 9 fail / 318 pass / 11 skip（与 V2 全程基线一致，0 退化）✓ |
| `import core.cfg.region_analyzer; import core.cfg.region_ast_generator` | IMPORT_OK ✓ |
| `compile /tmp/r20_decompiled.py` | COMPILE_OK ✓ |

## 四、V2 退出条件

| 退出条件 | 状态 | 说明 |
|---------|------|------|
| V2-E1 不一致函数数 = 0（100%） | ✗ 未达成 | 残留 3 个 |
| V2-E2 可提取新增最小复现实例 < 10 | ✓ 已达成 | 残留不一致函数 3 < 10 |

V2-E2 已达成，V2-E1 未达成。残留 3 个函数的根因均涉及区域识别层/生成层深层结构性改动，需 V3 后续迭代攻克。

## 五、V3 后续迭代优先级建议

1. **P0 — get_str_data（-48）**: 建模 BUILD_CONST_KEY_MAP 消费模式（区域识别层功能扩展）→ 区域边界对齐 → 重新应用 B/C 修复。预期收益最大（-48→0 可使一致数 147→148）。
2. **P1 — get_date_and_count（-27）**: 先解决 IfRegion else-branch 块收集穿透嵌套 LoopRegion → 反向链 fall-through 校验 + loop_else 无 break 守卫。预期收益 -27→0（147→148 或 149）。
3. **P2 — change_his_to_backward（instr_diff@296）**: code_generator 对齐 if/else 分支布局（生成层重构，影响面广）。预期收益 instr_diff→0（147→148 或与 P0/P1 叠加达 150）。

三项若全部修复，可达 V2-E1（150/150=100%）。但均属深层结构性改动，需配套最小复现实例回归，避免重蹈 R12/R13/R19 退化覆辙。
