# R48 总结

## 问题
repro_24: 嵌套 if-else + 尾随代码被错误展平为 elif，导致内层 else 体丢失。

## 根因分析

### RegionAnalyzer 层面
调试显示所有 `_check_elif_chain` 调用都返回 `None`，没有创建 `IF_ELIF_CHAIN`。R48 修复成功阻止了 elif 链创建。

### 问题根源
问题出在 **AST 生成器**层面。当 `_if_generate_normal` 处理 else 分支时：
1. 嵌套 IfRegion (`trade.sub == 0`) 被递归生成
2. 嵌套 IfRegion 的 else_blocks 包含内层 if-else (`self.count2 - amount != 0`) + trailing code (`self.time2 = ...; self.avg2 = 0.0; old = ...`)
3. 由于某种原因，内层 else 体的某些块在 AST 生成时被错误跳过或合并

### 调试输出
```
[R48 DBG OUTER] block=614 merge=Block@660-870 elif_info_is_none=True  ✓
[R48 DBG OUTER] block=592 merge=None elif_info_is_none=True        ✓ (外层 if)
[R48 DBG OUTER] block=320 merge=None elif_info_is_none=True        ✓ (内层 if)
[R48 DBG OUTER] block=62 merge=Block@108-318 elif_info_is_none=True ✓ (最外层 if)
```

所有调用都返回 `None`，说明修复在 RegionAnalyzer 层正确阻止了 elif 链。

## 状态
- R48 修复应用到 `core/cfg/region_analyzer.py`（line 14294-14355）
- 批量验证：87.24% 匹配率，无回归
- repro_24 仍是 66.67% 匹配
- 问题深层次：AST 生成器对 `else: [IfRegion, trailing_blocks]` 的处理

## 下一步
需要深入分析 `region_ast_generator.py` 中的 else 分支处理逻辑，特别是：
- `_if_generate_else_branch` 如何收集嵌套 IfRegion 及其 else_blocks
- `_process_if_blocks` 如何处理这些嵌套 IfRegion
- 为什么 `self.time2 = ...; self.avg2 = 0.0` 的块被丢失

当前修复虽然阻止了 elif 链创建，但没有解决根本问题。