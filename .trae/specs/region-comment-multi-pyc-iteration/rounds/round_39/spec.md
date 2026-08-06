# R39 Spec Round — 栈深度守卫 + DELETE_SUBSCR 语句识别

## 修复概述

### Fix 1: 栈深度守卫（region_ast_generator.py L31837）
- **问题**: `_generate_block_statements` 中 Pattern C2 (tuple unpack WITHOUT SWAP) 路径，
  `if _ns_n >= 2:` (L31837) 与 `if len(_ns_stack) >= _ns_n:` (L31802) 是同级（均嵌套于
  `if _ns_value_ok:`），当栈深度不足时跳过 L31802 检查但仍进入 L31837，
  导致 `_ns_stack[-_ns_n + _si]` 越界 → IndexError → 函数体完全丢失（pass）。
- **修复**: 在 L31837 补加 `len(_ns_stack) >= _ns_n` 守卫。
- **影响文件**: `live_future_position.pyc` 的 `load_from_kwargs` 函数体恢复（不再为 pass）。

### Fix 2: DELETE_SUBSCR/DELETE_ATTR 语句终止符识别（region_analyzer.py + region_ast_generator.py）
- **问题**: `STATEMENT_TERMINATORS` 集合缺少 `DELETE_SUBSCR`/`DELETE_ATTR`，
  导致 `del obj.attr` / `del container[key]` 语句不被识别为语句边界。
  前驱 LOAD 指令被当作孤立 Expr 发射，DELETE_* 指令被丢弃。
  `del self._positions[symbol]` 被错误反编译为裸 `symbol` 表达式。
- **修复**: 
  1. 将 `DELETE_SUBSCR`/`DELETE_ATTR` 添加到 `STATEMENT_TERMINATORS`（region_analyzer.py）
  2. 在 CONTINUE 块处理路径中添加显式 DELETE_SUBSCR/DELETE_ATTR → Delete 语句处理（region_ast_generator.py）
- **影响文件**: `future_account.pyc`、`option_account.pyc` 的 `_on_settlement` 函数中
  `del self._positions[symbol]` 不再丢失。

## 验证结果
- 批量验证: 5715/6617 = 86.37%（与 R38 持平，修复改善输出质量但未改变匹配计数）
- 回归测试: 157 failed / 2438 passed（与 R38 相同，无新增回归）
- OK 文件: 229 / Partial: 173 / Failed: 0

## 方法注释模板 (6/4 节)
### region_analyzer.py - _detect_block_roles 方法
- **修改说明 (6/4)**:
  - 前 4 行（修改概要）: R39 将 DELETE_SUBSCR/DELETE_ATTR 加入 STATEMENT_TERMINATORS，
    使 del 语句被识别为语句边界，防止前驱 LOAD 被当作孤立 Expr。
  - 后 4 行（技术依据）: 区域归约算法原则 2（每块唯一归属）—— del 语句的 LOAD 前驱
    应归属本 Delete 语句，不应泄漏为孤立 Expr。DELETE_SUBSCR/DELETE_ATTR 是语句终止
    指令（与 STORE_SUBSCR/STORE_ATTR 对称），必须在 STATEMENT_TERMINATORS 中。

### region_ast_generator.py - _generate_block_statements 方法 (CONTINUE 路径)
- **修改说明 (6/4)**:
  - 前 4 行（修改概要）: R39 在 CONTINUE 块处理路径补加 DELETE_SUBSCR/DELETE_ATTR →
    Delete 语句处理，与 _build_statement 中的 DELETE_* 路径保持一致。
  - 后 4 行（技术依据）: CONTINUE 块（JUMP_BACKWARD 回边块）的指令序列处理循环
    原仅识别 STORE_*/POP_TOP 为语句边界，遗漏 DELETE_*。补加后，del 语句在 CONTINUE
    块中不再退化为裸 Expr，与 NORMAL 块路径行为一致（原则 1: 自底向上归约）。
