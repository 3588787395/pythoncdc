# Round 03 修复报告 — 修复工程师

## 概述

- **基线**：101 partial / 2655 函数 / 2319 匹配（87.3%）
- **结果**：2 ok（翻转）+ 99 partial / **2329 匹配**（87.7%），0 回归
- **复现集**：11/11 PASS + 对照组 4/4
- **quotation.pyc**：143/143（修复前后均无退化）

## 本轮修复缺陷

| 缺陷 | 描述 | 状态 | 修复位置 |
|------|------|------|----------|
| F7 | 三元值 STORE_ATTR/STORE_SUBSCR 整条语句丢失（静默语义错误） | ✓ | region_ast_generator.py：merge_block 含 STORE_ATTR/STORE_SUBSCR/DELETE_SUBSCR 时 merge 返回 None，走 `_try_build_ternary_store_assign` 生成 Assign(target, IfExp) |
| F2 | 类体 `X = X` 别名赋值丢失 | ✓ | code_generator.py：删除历史反模式补丁（target_code == value_code 文本等值跳过）。`x = x` 是真实指令序列必须生成 Assign（「一次正确」原则） |
| F8 | if 体语句重排：[嵌套if, boolop赋值] 输出为 [boolop, return None, 嵌套if]（嵌套if不可达） | ✓ | region_ast_generator.py：`_if_generate_then_branch` 锚点发射机制——BoolOp/Ternary 子区域按 entry.start_offset 记录锚点，`_process_if_blocks` 新增 anchor_stmts 参数在对应块位置发射；未锚定语句回退前置 |
| F6 | for-else 的 `else: return None` 整体丢失 | ✓ | region_ast_generator.py `_loop_generate_for`：else 体只含 return None 的过滤器增加结构性判据——FOR_LOOP 且 has_break 时保留 orelse（回边证据），否则维持丢弃 |

## F6 修复算法依据

**根因定位**（插桩验证）：
1. `region_analyzer._find_loop_else` 正确：FOR_ITER 穷尽出口 block 6（`LOAD_CONST None; RETURN_VALUE`）经 break 证据 + 后必经路径（post_else=block 7 ≠ for_iter_exit）识别为 else_blocks，正确挂载 LoopRegion.else_blocks
2. `region_ast_generator._loop_generate_for` 丢失：else 体只含 `return None` 时被「隐式函数返回过滤器」整体清空

**结构性区分判据**（区域归约算法原则 2：每块唯一归属 + 回边证据）：
- **无 break**：else_blocks 来自自然出口路径，for_iter_exit 即函数尾声，`return None` 是隐式返回（编译器自动补发），丢弃正确
- **有 break**：else_blocks 由 break 目标的后必经路径证明（post_else ≠ for_iter_exit）。隐式尾声必然位于所有路径的汇合点——若 for_iter_exit 是尾声，break 会直接跳入它（`_break_hits_for_iter_exit=True` → else_blocks=None）。故此形态下 else 体中的 `return None` 只能是用户显式语句（else 路径在汇合点前提前返回），丢弃改变语义

**限定范围**：仅 FOR_LOOP。while 的 else_blocks 由自然出口可达性计算，有 break 时仍可能混入函数尾声，维持旧行为待独立复现再修。

## 验证

- 复现集：repro_01-11 全部 PASS（F2: 01/11, F6: 02/05/06, F7: 03/07/08, F8: 04/09/10）+ 对照组 4/4
- quotation.pyc：143/143（F6 修复后复验）
- 批量回归（regress_000.json vs baseline/batch_000.json）：
  - **翻转 partial→ok（2）**：
    - `IQEngine/account/base_account.pyc` 11/12 → 12/12
    - `IQEngine/data/data_proxy.pyc` 8/9 → 9/9
  - **匹配数提升（6 文件，+10 函数）**：finance 18→20/24、local_finance 16→18/19、wizard_quant_api 48→49/53、web_socket_client 5→6/7、fly_api/base 39→40/41、ptradeOptionAccount 35→36/38
  - **回退：0**

## 反模式自检

- git diff 新增 `def`：无（仅既有方法 `_process_if_blocks` 签名扩展）
- 新增代码无 `_fix_`/`_patch_`/`_hack_`/`_workaround_` 前缀
- 无跨区域启发式、无 `depth > N` 硬编码、无单文件特判
- 修复均为结构性判据：指令操作码守卫（F7）、删除违反「一次正确」的历史补丁（F2）、entry 锚点发射（F8）、回边证据区分隐式/显式 return（F6）
- 所有修改方法的 docstring 已按算法依据模板更新

## 进度

- 总体：303 ok / 99 partial / 402（75.4%）
- 函数匹配：2329/2655（87.7%）
