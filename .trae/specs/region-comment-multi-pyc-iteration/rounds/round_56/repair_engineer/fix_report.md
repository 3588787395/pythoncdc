# R56 修复工程师修复报告

## 修复概述
修复 Pattern TRY-NO-HANDLER：当 TryExceptRegion 的 handlers 列表为空且无 finalbody 时，不生成 Try AST 节点，直接返回 body 语句。

## 根因
`region_ast_generator.py` 的 `_generate_try` 方法在 handlers 列表为空时仍构造 `{'type': 'Try', 'handlers': []}` AST 节点。代码生成器输出 `try:` 但不生成 `except:` 或 `finally:`，导致 SyntaxError。

## 修复点

### 1. region_ast_generator.py — `_generate_try` 方法 (L17601)
在 `try_ast = {'type': 'Try', ...}` 构造之前插入守卫：
- 检查 `not handlers and not finalbody_stmts and not region.has_finally`
- 若为真，不生成 Try 节点，直接返回 `body_stmts + orelse_stmts + post-try 语句`
- post-try 代码生成逻辑完整保留（包括 for-iter-setup 检测、嵌套区域检测等）

### 2. code_generator.py — `_generate_try_dict` 方法 (L649)
Defense in depth 守卫：
- 检查 `not handlers and not finalbody`
- 若为真，跳过 `try:` 关键字，直接生成 body 语句
- 若有 orelse，将 orelse 合并到 body 后输出

## 算法依据
- **原则 2（每块唯一归属）**：handler 块已由其他区域拥有，本 TryExceptRegion 不应生成空的 try 节点
- **原则 3（嵌套即抽象节点）**：嵌套区域的 handler 不出现在父区域的展开中
- 非补丁：守卫基于 handlers 列表是否为空，无硬编码 offset / 无跨区域启发式 / 无后处理

## 注释更新
- `region_ast_generator.py` L17601: 添加 `[R56 fix] Pattern TRY-NO-HANDLER` 注释段，说明缺陷/触发条件/修复/算法依据
- `code_generator.py` L655: 添加 `[R56 fix] Defense in depth` 注释段

## 修复效果
- real_quote.pyc: failed 0% → partial 68.18% (30/44 matched, +30)
- trade_info_utils.pyc: failed 0% → partial 52.50% (21/40 matched, +21)
- 0 failed 文件（从 2 → 0）
- 累计匹配率增加 ~51 函数 (5815 → ~5866)

## 回归测试
- `import core.cfg.region_ast_generator; import core.cfg.code_generator` 编译通过
- 12 个最小复现实例全部 NO-DEFECT（未引入回归）
- 既有测试矩阵不受影响（仅在 handlers 为空时跳过 Try 节点，不影响正常 try-except 生成）

## 残留不一致
- real_quote.pyc: 14 mismatch 函数（主要是表达式顺序错乱、变量名混淆、PUSH_EXC_INFO 结构重建不完整）
- trade_info_utils.pyc: 19 mismatch 函数（主要是语句顺序错位、变量名混淆、try-except 结构重建不完整）
- 这些是独立的深层缺陷，后续轮次修复
