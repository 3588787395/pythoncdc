# R28 修复工程师报告

## 修复点

### Fix 1: 空 except body（try/except/finally/else 全路径）
- **文件**: `core/cfg/code_generator.py`
- **问题**: `_generate_try_dict` 和 `_generate_try`/`_generate_except_handler` 中，当 body/handler_body/orelse/finalbody 非空但节点不产生输出时，不生成 `pass`，导致 `IndentationError`
- **修复**: 在所有 body 生成路径（dict 和 AST 节点两套）添加输出跟踪：记录生成前后的 output 值，若相等则写 `pass`
- **算法依据**: 每块唯一归属 — 空块归 `pass` 语句，不泄漏到相邻块

### Fix 2: nonlocal 声明误添加不在父作用域的变量
- **文件**: `core/cfg/region_analyzer.py`
- **问题**: `_detect_global_declarations` 中 STORE_DEREF 检测路径添加了不在父函数 co_cellvars 中的变量，导致 `SyntaxError: no binding for nonlocal`
- **修复**: 在第一个检测路径（STORE_DEREF）添加父函数 co_cellvars 验证；在 fallback 路径添加 STORE_DEREF/DELETE_DEREF 指令验证
- **算法依据**: 字节码驱动 — nonlocal 声明必须由 co_freevars + parent co_cellvars 双重验证

## 注释更新
- `_generate_try_dict`: `[R28 fix]` 标记输出跟踪逻辑
- `_generate_try`: `[R28 fix]` 标记 AST 节点路径输出跟踪
- `_generate_except_handler`: `[R28 fix]` 标记 handler body 输出跟踪
- `_detect_global_declarations`: `[R28 fix]` 标记 parent cellvars 验证

## 回归结果
4 个文件从 failed → partial，无新增回归。
