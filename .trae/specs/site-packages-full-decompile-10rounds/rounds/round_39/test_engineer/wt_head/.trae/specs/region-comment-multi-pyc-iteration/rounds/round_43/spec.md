# R43 Spec Round — 修复 Python 名称重整 (Name Mangling) 问题

## 修复概述

### Fix: 名称重整导致函数定义名错误 (region_ast_generator.py)
- **问题**: `region_ast_generator.py` 中 9 处 `func_def['name'] = target_name` 用
  `STORE_NAME` 的 mangled 名（如 `_BaseDatabase__load_table_names`）覆盖了
  `_build_function_def` 从 `co_name` 获取的正确名（如 `__load_table_names`）。
- **根因**: Python 名称重整规则——类体中以 `__` 开头(但不以 `__` 结尾)的标识符
  会被编译器重整为 `_ClassName__name`。字节码 `STORE_NAME` 存储重整名，但
  code object 的 `co_name` 保留原始名。反编译器应使用 `co_name`。
- **修复**: 
  1. 添加 `_is_mangled_name(target_name, co_name)` 方法检测名称重整
  2. 添加 `_safe_set_func_name(func_def, target_name)` 方法安全设置函数名
  3. 将所有 9 处 `func_def['name'] = target_name` 替换为
     `self._safe_set_func_name(func_def, target_name)`
- **效果**: 匹配率从 86.67% 提升至 86.96%（+19 匹配函数，+2 OK 文件）

## 受影响文件
- `iqdata_db_base.pyc`: 9 个函数（`__load_table_names`, `__load_view_names` 等）
- `iqdata_db_helper.pyc`: 3 个函数（`__create_engine` 等）
- 其他含 `__method` 私有方法的类

## 验证结果
- 批量验证: 5754/6617 = 86.96%（+0.29% vs R42）
- OK 文件: 231 / Partial: 171 / Failed: 0
- 回归测试: 157 failed / 2438 passed（与 R42 一致，无新增回归）

## 方法注释模板 (6/4 节)
### region_ast_generator.py - _is_mangled_name 方法
- **修改说明 (6/4)**:
  - 前 4 行（修改概要）: R43 新增 `_is_mangled_name` 方法检测 target_name
    是否是 co_name 的名称重整形式，防止 STORE_NAME 的 mangled 名覆盖
    code object 的 co_name。
  - 后 4 行（技术依据）: Python 名称重整规则(CPython compile.c _Py_Mangle()):
    类体中 __method → _ClassName__method。co_name 保留原始名 __method，
    STORE_NAME 存储重整名 _ClassName__method。检测条件: co_name 以 __
    开头且不以 __ 结尾, target_name 以 co_name 结尾且不同。

### region_ast_generator.py - _safe_set_func_name 方法
- **修改说明 (6/4)**:
  - 前 4 行（修改概要）: R43 新增 `_safe_set_func_name` 方法，在设置函数名时
    检测名称重整，若 target_name 是 mangled 形式则保留 co_name。
  - 后 4 行（技术依据）: 被 9 处原 `func_def['name'] = target_name` 覆盖点
    调用。当 func_def 类型为 FunctionDef/AsyncFunctionDef 且 target_name
    是 co_name 的重整形式时跳过覆盖，否则正常设置。
