# R32 测试工程师报告

## 批量验证结果（Python 3.11.7）

| 指标 | R31 | R32 | 变化 |
|------|-----|-----|------|
| total_pyc | 402 | 402 | — |
| ok_pyc | 222 (55.2%) | 222 (55.2%) | — |
| partial_pyc | 176 (43.8%) | 177 (44.0%) | +1 |
| failed_pyc | 4 (1.0%) | 3 (0.7%) | -1 ✓ |
| matched_functions | 5397 | 5420 | +23 |
| cumulative_match_rate | 81.56% | 81.91% | +0.35% |

## R32 修复效果

| 文件 | R31 状态 | R32 状态 | 修复内容 |
|------|----------|----------|----------|
| pboxAccount_jupyterhub.pyc | failed (SyntaxError line 88) | failed (SyntaxError line 129) | merge computation: JUMP_FORWARD in successor chain |

## 修复详情

pboxAccount_jupyterhub.pyc 的语法错误从行 88 移到行 129，说明 merge 修复部分生效：
- `IF_ELIF_CHAIN entry@14` 的 merge_block 从 None 变为 1154
- then_blocks 从 31 个块减少到 6 个块
- 行 88 的错误消失，但行 129 仍有 `else:` 语法错误（`IF_THEN_ELSE entry@1686` 的 else_blocks 过度收集）

## 剩余 3 个失败文件

| 文件 | 错误类型 | 根因 | 修复难度 |
|------|----------|------|----------|
| backtest.pyc | 0% bytecode match (编译通过) | try-except 范围不正确 | 中 |
| strategy_info_utils.pyc | 0% bytecode match (编译通过) | 模块级结构错误 | 中 |
| pboxAccount_jupyterhub.pyc | SyntaxError (else line 129) | IF_THEN_ELSE else_blocks 过度收集 | 高 |
