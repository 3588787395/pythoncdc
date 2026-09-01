# R31 修复工程师报告

## 修复点

### Fix 1: 重复 case _ 通配符去重（dict + AST 路径）
- **文件**: `core/cfg/code_generator.py`
- **问题**: matcher.pyc 中 `match account:` 后出现两个 `case _:`，导致 `SyntaxError: wildcard makes remaining patterns unreachable`
- **根因**: 模式识别错误导致 MatchAs (无 name) 被生成为 `case _`，且同一 match 语句中出现多个
- **修复**:
  1. dict 路径 (`_generate_dict_node` Match 分支): 检测 pattern 为 None 或 MatchAs(无 name) 且无 guard 的 case，只保留最后一个
  2. AST 路径 (`_generate_match`): 同上，额外检测 `ASTName('_')` (MatchAs 经 ast_converter 转换后的形式)

### Fix 2: ''.join([Constant, FormattedValue, ...]) → f-string 转换
- **文件**: `core/cfg/code_generator.py`
- **问题**: trade_info_utils.pyc 中 `''.join(["""...""", {iqe_strategy!s}, """..."""])` 被生成为多个三引号字符串片段，导致 `SyntaxError: invalid syntax`
- **根因**: 反编译器将 `BUILD_STRING` 结果错误识别为 `''.join([...])` 调用，列表元素交替为字符串常量和 FormattedValue
- **修复**:
  1. dict 路径 (`_generate_expression` Call 分支): 检测 `Attribute(value=Constant(''), attr='join')` + `List` 参数含 FormattedValue，转换为 `JoinedStr` 并调用 `_generate_joined_str_from_dict`
  2. AST 路径 (`_generate_call`): 同上，检测 `ASTAttribute(attr='join')` + `ASTConstant(value='')` + `ASTList` 参数含 `ASTFormattedValue`，创建 `ASTJoinedStr` 并调用 `_generate_joined_str`

## 回归验证
- wizard_quant_api.pyc: 仍为 partial ✓
- scheduler.pyc: 仍为 partial ✓
- 无新增回归
