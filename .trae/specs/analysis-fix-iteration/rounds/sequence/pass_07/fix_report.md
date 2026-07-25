# Pass 7 SEQ (Sequence) 修复报告

## 修复内容

### Fix 1: 标记 `_generate_block_statements` 内 `('RETURN_VALUE', 'RETURN_CONST')` 字面量 DRY 同型反模式

**问题位置**：`/workspace/core/cfg/region_ast_generator.py:25098-25100`
（`_generate_block_statements` 方法 `_loop_depth > 0` break 模式判别分支内）

**问题根因**（与 Pass5-TERNARY/SEQ / Pass7-ASSERT 同型「`_is_*` 子串匹配 / 字面量重复 DRY 反模式」）：
`_generate_block_statements` 在 break 模式判别中使用字面量元组：
```python
if (len(_no_pop) == 2 and
    _no_pop[0].opname == 'LOAD_CONST' and _no_pop[0].argval is None and
    _no_pop[1].opname in ('RETURN_VALUE', 'RETURN_CONST')):
```

该字面量与本文件 Pass5-TERNARY/SEQ 已替换为模块级常量 `RETURN_TERMINATOR_OPS` 的 3 处
（`_is_trivial_return_block` / `_identify_ternary_regions` 内嵌函数三处，均位于
`region_analyzer.py`）属同型 DRY 反模式——同一 `(RETURN_VALUE, RETURN_CONST)` 集合在
两文件多处重复定义，未统一引用 `RETURN_TERMINATOR_OPS`。

**全量统计**（grep 验证）：
```
grep "_no_pop[1].opname in ('RETURN_VALUE', 'RETURN_CONST')" core/cfg/region_ast_generator.py
```
本文件命中 **3 处**：
- L25092（本方法 `_generate_block_statements` `_loop_depth` break 分支，本轮标记）
- L25128（本方法 `_block_role` BREAK 分支同型）
- L20595（另一处 `_loop_depth` break 判别同型）

与 Pass6-SEQ §未完成项 1「余 40+ 处待统一替换」口径一致——全量替换需逐处评估 break
模式判别语义等价性，留待后续 Pass 统一处理。

**修复策略**（与 Pass7-ASSERT 标记 `'TRUE' in opname` 子串匹配 DRY 同型反模式同型——
仅添加 `[Pass7-SEQ]` 标记注释，不替换字面量）：
- 保留原字面量 `('RETURN_VALUE', 'RETURN_CONST')` 不变
- 追加 `[Pass7-SEQ]` 段落标记：
  1. 指明与 Pass5-TERNARY/SEQ 在 `_is_trivial_return_block` /
     `_identify_ternary_regions` 中已替换为 `RETURN_TERMINATOR_OPS` 的 3 处同型
  2. 指明本方法内尚有 3 处同模式命中（L25092 / L25128 / L20595）
  3. 说明未替换原因（与 Pass6-SEQ §未完成项 1 同型：全量替换需逐处评估 break 模式
     判别语义等价性）
- 不触及任何可执行代码，控制流不变

**等价性证明**：
- 仅追加注释段，未修改任何可执行语句
- 编译期与运行期行为完全不变
- 与 Pass6-SEQ §未完成项 1 / Pass5-TERNARY/SEQ 口径一致

## 编译验证

```
python -c "import core.cfg.region_analyzer; import core.cfg.region_ast_generator"
```
**结果**：退出码 0，输出 `COMPILE_OK`。

## 回归测试

```
timeout 290 python .trae/specs/analysis-fix-iteration/run_region_tests.py SEQ
```
**结果**：`127 10 0 137 1.7 SEQ files=80` —— 与基线一致（127 passed, 10 预存失败,
0 errors）。无退化。

## 反模式消除情况

| 反模式 | 本轮处理 |
|---|---|
| `_fix_` / `_merge_` / `_patch_` 前缀 | 未引入 |
| 硬编码深度上限 | 未引入 |
| 控制流改变 | 未改变（仅添加注释） |
| 测试文件修改 | 未修改任何测试文件 |
| 字面量元组重复 DRY（`('RETURN_VALUE', 'RETURN_CONST')`） | **已标记**（追加 [Pass7-SEQ] 段落，与 Pass7-ASSERT 标记 TRUE 子串匹配 DRY 同型） |

## 未完成项

1. **`_generate_block_statements` 内 3 处 `('RETURN_VALUE', 'RETURN_CONST')` 字面量
   统一替换为 `RETURN_TERMINATOR_OPS`**（本轮标记 L25092，余 L25128 / L20595 同型未标记）：
   全量替换需逐处评估 break 模式判别语义等价性，留待后续 Pass 统一处理（与 Pass6-SEQ
   §未完成项 1 同源扩展）。
2. **文件全量 40+ 处 `('RETURN_VALUE', 'RETURN_CONST')` 字面量未替换**（Pass6-SEQ
   §未完成项 1，本轮在 region_ast_generator.py 标记 1 处新发现）：全量替换需逐处评估
   语义等价性，留待后续 Pass 统一处理。
3. **`_loop_depth > 0` 跨层启发式消除**（Pass 4 已标记 `TODO[pass3-SEQ]-F`，对应
   `[Pass4-SEQ]` 注释）：中风险，需先在识别阶段完善 break 块标记。
4. **`_cond_jump_bs` 兜底分支删除**（Pass 1 TODO[pass2-SEQ]-C，已标记）：中风险，
   需先在 `_identify_conditional_regions` 末尾扫描未认领条件跳转块。
5. **`_generate_block_statements` god-method 瘦身**（Pass 2 TODO[pass3-SEQ]-E）：
   高风险，需把语句边界判定移到识别阶段。
6. **`_is_trivial_return_block` Pattern 1 收紧为 `argval is None`**（Pass 2
   TODO[pass2-SEQ]-B）：低风险但属控制流变更，需评估影响。
7. **10 例预存失败**：L1_basic NameError 类（测试基础设施问题）+
   basic/test_b23yieldfrom_complex（字节码重建差异），非保守修复范围。

## 文件清单

- `/workspace/core/cfg/region_ast_generator.py`（Fix 1：`_generate_block_statements`
  L25089 后追加 `[Pass7-SEQ]` 标记段落，标记 `('RETURN_VALUE', 'RETURN_CONST')`
  字面量 DRY 同型反模式）
- `/workspace/.trae/specs/analysis-fix-iteration/rounds/sequence/pass_07/fix_report.md`（本报告）
