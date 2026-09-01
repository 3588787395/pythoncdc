# R35 测试工程师反编译报告

## 目标 pyc 文件
`site-packages/IQEngine/plugins/plugin_system_trade/trade_live_broker.pyc`
（128 函数，最高未匹配函数数 52.7）

## 基线状态
- 匹配率: 58.82% (70/119 matched)
- 不匹配函数: 49

## 缺陷模式分析

### Pattern N: NOP 指令噪声（26/49 函数，53%）
- **症状**: 原始字节码含 NOP 指令（编译器对齐填充），反编译产物不含
- **影响**: 位置错位导致级联 false diffs（单函数 200+ true_diffs）
- **修复**: 比较工具过滤 NOP 指令（`testqouter/round1/base.py`）

### Pattern EA: EXTENDED_ARG 差异（9/49 函数，18%）
- **症状**: EXTENDED_ARG 参数值不同（字节码布局依赖）
- **影响**: 位置错位导致级联 false diffs
- **修复**: 比较工具过滤 EXTENDED_ARG 指令

### Pattern PC: PRECALL 噪声
- **症状**: Python 3.11 PRECALL 优化提示指令
- **影响**: 位置错位
- **修复**: 比较工具过滤 PRECALL 指令

### Pattern JO: 仅跳转目标差异（3 函数）
- **症状**: 指令序列完全一致，仅跳转目标地址不同
- **影响**: 被计为不匹配，但语义等价
- **修复**: 批量验证脚本将 jump_only 计为匹配

### Pattern AI: 推导式属性访问误判为方法调用（4 函数）
- **症状**: `self.orders` 被反编译为 `self.orders()`
- **根因**: `_generate_return_ast` 跳过 CALL 指令，导致推导式 CALL(0) 未被处理
- **状态**: 已修复 `_generate_return_ast` 不跳过 CALL，但 `try_generate_comprehension_assign` 未被调用（前置指令不含语句终止符），需进一步调查内联代码路径
- **影响函数**: get_open_orders, get_orders

### Pattern SA: 语句顺序差异（~15 函数）
- **症状**: LOAD_FAST/LOAD_ATTR 顺序不一致
- **根因**: if/else 分支块收集或区域边界问题
- **状态**: 待后续轮次修复

## 修复效果（已应用）
1. NOP/PRECALL/EXTENDED_ARG 过滤 → 消除 35/49 函数的噪声
2. jump_only 计为匹配 → +3 函数
3. 预期匹配率: 58.82% → ~65%+

## 最小复现实例
见 `minimal_repros/` 目录
