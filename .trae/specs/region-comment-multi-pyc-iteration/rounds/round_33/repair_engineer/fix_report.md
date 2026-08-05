# R33 修复工程师报告

## 修复点

### Fix: _generate_remaining_stmts 委托 region_ast_gen._build_store_statement
- **文件**: `core/cfg/comprehension_generator.py`
- **问题**: `bar.pyc` 中类定义（`LOAD_BUILD_CLASS` + `MAKE_FUNCTION` + `CALL` + `STORE_NAME`）被错误反编译为 `__build_class__` 调用包装在 `Assign` 中，而非 `ClassDef`。匹配率仅 1.72%。
- **根因**: `ComprehensionGenerator._generate_remaining_stmts` 处理推导式后的剩余指令时，直接使用 `self.expr_reconstructor.reconstruct(value_instrs)` + `Assign` 构造语句，跳过了 `RegionASTGenerator._build_store_statement` 中的高级语句识别逻辑（`ClassDef`/`FunctionDef`/装饰器/walrus 等）。当 `bar.pyc` 的模块级代码包含推导式后跟类定义时，类定义指令落入 `_generate_remaining_stmts` 路径，无法被识别为 `ClassDef`。
- **诊断**: 通过 Monkey-patch 追踪调用栈，确认 `__build_class__` 的 `Call` 节点由 `_generate_remaining_stmts` 第 379 行的 `self.expr_reconstructor.reconstruct(value_instrs)` 生成，而非 `RegionASTGenerator._build_store_statement`。
- **修复**:
  1. `_generate_remaining_stmts` 方法签名新增 `region_ast_gen=None` 参数
  2. 调用点（`try_generate_comprehension_assign` 第 294 行）传入 `region_ast_gen`
  3. STORE 处理分支：当 `region_ast_gen` 可用时，委托 `region_ast_gen._build_store_statement(current_instrs)` 进行高级语句识别；否则保留原 `reconstruct + Assign` 回退逻辑
  4. 与 `_generate_pre_comp_stmts`（第 341-344 行）已有的同模式保持一致
- **算法依据**: 区域归约算法原则 3（嵌套即抽象节点）— 推导式作为独立语句被归约后，剩余指令应通过标准的语句归约路径（`_build_store_statement`）处理，该路径能正确识别 `__build_class__` Call 并归约为 `ClassDef` 抽象节点
- **效果**: `bar.pyc` 匹配率从 1.72% 提升至 81.03%，`BarData`/`TickBar`/`BarDict` 三个类定义正确生成为 `ClassDef`

## 回归验证
- 批量测试 60 个文件（round 33），累计匹配率 82.91%（R32 为 81.91%，+1.00%）
- 第二个 `bar.pyc`（local_variables）：95.45%，无回归 ✓
- 无新增回归
