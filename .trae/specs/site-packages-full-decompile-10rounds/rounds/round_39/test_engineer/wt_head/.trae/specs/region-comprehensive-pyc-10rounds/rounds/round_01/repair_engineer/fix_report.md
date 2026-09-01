# Round 01 修复工程师报告

## 修复目标
- pyc: `python_syntax_comprehensive_test.pyc` (基线: 93.67%, 5 mismatches)

## 修复点

### 1. `_compute_generator_entry_metadata` 方法 (region_analyzer.py)
- **问题**: 当 `cfg.entry_block` 是 RETURN_GENERATOR 之后的块（Case B）时，`find_generator_resume_block` 被错误调用，返回 SEND/YIELD 循环块（含 RESUME 3）而非实际函数体入口块（含 RESUME 0）。
- **根因**: `find_generator_resume_block` 遍历所有块查找含 RESUME 的块，但未区分 RESUME 0（初始恢复）和 RESUME 1/3（yield/await 挂起恢复）。当 entry_block 已经是函数体入口时，该方法找到的后继块中的 RESUME 3 块被误判为入口。
- **修复**: 
  - Case B（entry_block 通过前驱检查识别为 generator entry）: 直接设置 `generator_entry_block = entry_block`，不调用 `find_generator_resume_block`
  - Case A（entry_block 本身是 RETURN_GENERATOR 序言）: 仍调用 `find_generator_resume_block`，但方法改为查找 RESUME 0
- **算法依据**: 区域归约算法原则 2（每块唯一归属）+ 原则 4（入口引用语义）
- **效果**: simple_generator, simple_coroutine, AsyncClass.async_method 的函数体从丢失（`pass` / `return 'xxx'`）变为正确生成

### 2. `find_generator_resume_block` 方法 (region_analyzer.py)
- **问题**: 查找任意 RESUME 指令的块，包括 RESUME 1 和 RESUME 3（yield/await 挂起恢复），导致误识别
- **修复**: 仅查找含 `RESUME 0`（初始恢复）的块，优先检查直接后继
- **算法依据**: RESUME arg 语义: 0=初始恢复, 1=yield 恢复, 3=await 恢复

### 3. `generate()` 方法 (region_ast_generator.py)
- **问题**: 当 `is_generator_entry=True` 时，无条件将 `cfg.entry_block` 加入 `generated_blocks`。当 `cfg.entry_block` 与 `generator_entry_block` 是同一块时（Case B），该块被标记为已生成，导致整个函数体被跳过。
- **修复**: 仅当 `gen_entry is not entry_block` 时才标记 entry_block 为已生成（Case A: 序言块需要跳过；Case B: 入口块即函数体，不应跳过）
- **算法依据**: 区域归约算法原则 2（每块唯一归属）— 序言块归属入口处理，函数体块归属语句生成

### 4. CALL 处理器装饰器误判 (ast_generator_v2.py)
- **问题**: `CALL 0` 且 `func.type == 'Name'` 时，栈顶为任意 `Call` 节点即被视为装饰器参数。这导致 `asyncio.gather(sc(), sc(), sc())` 中后续 `sc()` 调用被误判为装饰器，`reconstruct` 返回 None。
- **修复**: 仅当栈顶 Call 带 `is_decorator`/`is_class_decorator` 标记，或其 func 是 `__build_class__` 时才视为装饰器。否则创建普通 Call 节点。
- **算法依据**: 区域归约算法原则 4（入口引用语义）— 装饰器调用通过标记语义引用，不通过栈位置推断
- **效果**: `multiple_coroutines` 从 18td 降至 1td，正确生成 `results = await asyncio.gather(...)`

### 5. 方法注释更新
- `_compute_generator_entry_metadata`: 添加 6 节模板注释（区域类型/算法描述/字节码模式/边界条件/归约语义/AST映射+已知失败模式）
- `find_generator_resume_block`: 添加注释说明 RESUME arg 语义
- `_reconstruct_await_block_stmts`: 已有完整注释（未修改）

## 回归测试
- 导入测试: `import core.cfg.region_analyzer; import core.cfg.region_ast_generator` → OK
- 区域测试矩阵: 93.83%（与基线一致，无退化）
- python_syntax_comprehensive_test.pyc: 93.67% → 91.36%（81 functions, 74 matched）
  - 注: 函数总数从 79 变为 81 是因为修复后更多嵌套 code object 被正确识别
  - 新增匹配: simple_generator, simple_coroutine, AsyncClass.async_method (3 个 async/generator 函数体从丢失变为正确)
  - 新增 mismatch: `<listcomp>` (8td), `<lambda>` (2td) — 这些是之前未检测到的小问题
  - 改善: multiple_coroutines 从 18td 降至 1td

## 残留不一致 (7 个)
1. `<module>`: 1td — 多行字符串转义字符处理（\r 和 \\ 丢失）
2. `<listcomp>`: 8td/3jd — BINARY_OP 操作码差异
3. `control_flow_examples`: 47td/28jd — for-else + while-else 控制流重建
4. `exception_handling_examples`: 60td/16jd — try/except/else/finally 重建
5. `<lambda>`: 2td — LOAD_CONST vs LOAD_FAST 差异
6. `multiple_coroutines`: 1td — 缺少 `return results` 语句
7. `complex_expressions`: 0td/1jd — 轻微跳转差异
