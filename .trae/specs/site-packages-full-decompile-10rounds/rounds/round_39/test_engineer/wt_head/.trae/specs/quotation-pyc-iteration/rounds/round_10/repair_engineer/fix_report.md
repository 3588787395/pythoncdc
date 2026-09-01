# R10 修复工程师报告

## 概述

本轮在 R8/R9 基础上，针对测试工程师发现的 quotation.pyc 反编译缺陷，
依据区域归约算法（原则 2：每块唯一归属；原则 4：嵌套区域在父区域中
作为单个抽象节点表示）完成 8 项修复（R10-N1 ~ R10-N5）。

## 字节码一致性统计

- 完全匹配（指令+签名）: 71 / 149 = 47.7%
- 指令匹配（仅指令）:    71 / 149 = 47.7%

注：本统计使用 exact_match_stats.py，递归比较 code object 字节码，
排除 co_filename / co_firstlineno 等环境相关属性，比 R8/R9 的
co_code-only 统计更严格。

## 修复列表

### R10-N1: 入口块 STORE_SUBSCR/STORE_ATTR 丢失

- **文件**: core/cfg/region_ast_generator.py
- **方法**: generate() 入口块 pre-stmts 提取循环
- **根因**: 仅处理 STORE_FAST/NAME/GLOBAL/DEREF，遗漏 STORE_SUBSCR/STORE_ATTR
- **修复**: 添加 STORE_SUBSCR/STORE_ATTR 处理，调用
  _build_subscript_assign / _build_attr_assign 生成赋值语句
- **原则**: 原则 2（每块唯一归属）—— 入口块中的 dict[key]=val 和 obj.attr=val
  必须作为独立 pre_stmt 提取，否则会被累积并错误合并或丢失

### R10-N2: IfRegion 条件块 STORE_SUBSCR/STORE_ATTR 丢失

- **文件**: core/cfg/region_ast_generator.py
- **方法**: _if_extract_cond_instructions
- **根因**: 同 N1，遗漏 STORE_SUBSCR/STORE_ATTR
- **修复**: 镜像 N1，在条件块 pre-stmts 提取中添加相同处理

### R10-N3: elif 条件块 pre-stmts 丢失

- **文件**: core/cfg/region_ast_generator.py
- **方法**: _if_generate_elif_chain
- **根因**: elif 条件块中可能含前置赋值（如 fields = re_fields），
  但手动指令循环遇到 STORE_FAST 时直接清空指令列表
- **修复**: 调用 _if_extract_cond_instructions 提取 pre-stmts
  （含 N2 的 STORE_SUBSCR/STORE_ATTR 处理），前置到返回结果
- **原则**: 原则 2 + 原则 4（父引用子入口）—— elif 条件块的 pre-stmts
  属于 elif 分支的顺序块序列，不应丢失

### R10-N4: else 分支不识别 IfRegion 子区域

- **文件**: core/cfg/region_ast_generator.py
- **方法**: _if_generate_else_branch
- **根因**: else 分支仅收集 TryExceptRegion/WithRegion/LoopRegion 子区域，
  遗漏 IfRegion，导致嵌套 if/elif 被当作顺序块处理，条件判断丢失
- **修复**: 在子区域收集 isinstance 检查中添加 IfRegion
- **原则**: 原则 4（嵌套区域在父区域中作为单个抽象节点表示）——
  else 分支也必须识别 IfRegion 子区域（与 then 分支一致）

### R10-N5: IfRegion 与复合子区域块所有权冲突（DEEP12 回归）

- **文件**: core/cfg/region_ast_generator.py
- **方法**: _if_generate_else_branch
- **根因**: R10-N4 添加 IfRegion 后，当 IfRegion.entry 落在已收集的
  TryExceptRegion/WithRegion/LoopRegion 的 blocks 内时，两者同时被收集，
  导致块所有权冲突，TryExceptRegion 的 AST 被 IfRegion 覆盖
  （TestDEEP12RecursivePatternWithExceptions 回归：try_count < 2）
- **修复**: 两阶段收集 —— 第一阶段收集复合子区域（Try/With/Loop），
  记录其 blocks 到 _claimed_blocks_c3；第二阶段收集 IfRegion，
  跳过 entry 已在 _claimed_blocks_c3 中的（嵌套 IfRegion 应由
  外层复合区域的 _generate_region 递归处理）
- **原则**: 原则 2（每块唯一归属）—— 嵌套 IfRegion 由其外层复合区域
  递归处理，不在父 IfRegion 的 else 分支平铺展开
- **镜像**: then 分支 L8599 的 generated_blocks 检查（then 分支逐个
  即时生成并标记，else 分支两阶段收集需显式追踪 _claimed_blocks_c3）
- **验证**: DEEP12 回归测试通过，control_flow_matrix 无新增失败

### R10-N6: 循环前驱块 STORE_ATTR/STORE_SUBSCR/CALL+POP_TOP 丢失

- **文件**: core/cfg/region_ast_generator.py
- **方法**: _loop_extract_for_iter_pre_stmts, _loop_extract_pre_stmts_from_block
- **根因**: 仅处理 STORE_FAST/NAME/GLOBAL/DEREF，未处理 STORE_SUBSCR/STORE_ATTR
  及 POP_TOP 作为 CALL 表达式语句终结符
- **修复**: 添加 STORE_SUBSCR/STORE_ATTR 处理；将 POP_TOP 作为
  CALL 表达式语句终结符，构建独立 Expr 语句

### R10-N7: WHILE 循环 header/condition/back_edge 块 STORE_SUBSCR/STORE_ATTR 丢失

- **文件**: core/cfg/region_ast_generator.py
- **方法**: _loop_process_header_instructions, _loop_generate_while,
  _loop_extract_pre_stmts_from_instrs
- **根因**: 同 N6，遗漏 STORE_SUBSCR/STORE_ATTR
- **修复**: 在三个方法中添加 STORE_SUBSCR/STORE_ATTR 处理，
  调用 _build_subscript_assign / _build_attr_assign

## 回归测试

- tests/control_flow_matrix/: 322 passed, 5 failed (均为预存失败，与基线一致), 11 skipped
- DEEP12 回归测试: 通过（R10-N4 引入的回归已由 R10-N5 修复）
- quotation.pyc 反编译: compile OK, exec 因缺少第三方依赖（pytz/numpy/yaml/...）失败
  （环境问题，非反编译问题）

## 后续方向

- get_growth_ability / get_balance_statement 等函数的条件分支结构仍有
  指令差异，需进一步分析 IfRegion 嵌套结构的 AST 生成
- get_history 的 return None 路径被误判为 JUMP_FORWARD，需分析
  IfRegion merge_block 的隐式 return 识别
- 成功率从 R9 的统计口径（co_code-only）到 R10 的严格口径
  （递归 code object + 签名）有自然下降，后续轮次应在严格口径上提升
