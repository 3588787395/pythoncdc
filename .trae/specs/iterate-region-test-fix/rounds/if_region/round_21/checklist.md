# Checklist

- [x] C5 根因已定位：`_collect_await_predecessor_chain` 仅收集单个 setup+poll 对（region_analyzer.py:4434-4486）
- [x] `_collect_await_predecessor_chain` 已重构为沿前驱链反向迭代收集所有 setup+poll 对
- [x] 调用点已正确消费多组 setup+poll 块并纳入 IfRegion.all_condition_blocks
- [x] test_adv19_await_in_if_cond.py 单测通过（反编译结果保留完整 await 条件链）
- [x] IF region 全量回归失败数未增加（基线 35 failed → 34 failed，净减 1）
- [x] IF + ternary region 联合回归失败数未增加（34 failed / 1289 passed / 46 skipped）
- [x] spurious TernaryRegion（`None if 0 else None`）已消除（`_is_boolop_ternary_candidate` GET_AWAITABLE 检查）
- [x] spurious `await a` 语句已消除（`_process_if_blocks` `_nested_if_skip` 真值检查修复）
- [x] ternary region 回归无回归（506 passed / 36 skipped / 0 failed）
- [x] 修复未引入跨区域启发式特殊 case（遵循 4 原则）
- [x] 修复未破坏已有 C1/C3/C4 修复
- [x] 未修改任何测试文件
- [x] 未在源码中添加 print/pdb/breakpoint 语句
- [x] 未创建根级 _debug_*.py 调试文件
- [x] fix_report.md 已写入 /workspace/.trae/specs/iterate-region-test-fix/rounds/if_region/round_21/fix_report.md
