# Pass 5 SEQ (Sequence) 修复报告

## 修复内容

### Fix 1: 替换 `_is_trivial_return_block` 内 `('RETURN_VALUE', 'RETURN_CONST')` 字面量为 `RETURN_TERMINATOR_OPS` 常量（重复代码消除）

**问题位置**：`/workspace/core/cfg/region_analyzer.py:16352`（`_is_trivial_return_block` 内 `if len(meaningful) == 1 and meaningful[0].opname in ...`，原 L16341）

**问题根因**（Pass 1-4 未触及的 DRY 违背，与 Pass5-TERNARY 同型）：
`_is_trivial_return_block` 内 L16341 使用字面量 `('RETURN_VALUE', 'RETURN_CONST')` 做成员检测，
而模块级常量 `RETURN_TERMINATOR_OPS = frozenset({'RETURN_VALUE', 'RETURN_CONST'})`（L54 定义）
已存在并已在同文件其他位置使用（L12204/L12216/L12259 `_block_is_return_body` 等嵌套函数内）。

`_is_trivial_return_block` 为 SEQ 区域调用的通用工具：
- `_generate_basic_region` / `_generate_block_statements` 通过 `_is_exit_like_block` →
  `_is_trivial_return_block` 路径检测 trivial return 块
- `_is_exit_like_block`（L16357）直接调用 `_is_trivial_return_block`
- 与 Pass5-TERNARY `_is_ternary_block` 内同型 DRY 违背修复一致

**修复策略**：
按 Pass5-TERNARY 同型「重复代码消除」替换：
- L16341（现 L16352）`meaningful[0].opname in ('RETURN_VALUE', 'RETURN_CONST')`
  → `meaningful[0].opname in RETURN_TERMINATOR_OPS`

同时追加 `[Pass5-SEQ]` 段落说明：
1. 与 Pass5-TERNARY 同型 DRY 违背修复
2. `_is_trivial_return_block` 为 SEQ 区域调用的通用工具
3. 通过 `_is_exit_like_block` / `block_roles` 等路径被 SEQ 生成逻辑使用
4. 语义等价性验证：`x in tuple` 与 `x in frozenset` 均为成员检测，对 hashable 字符串完全等价
5. 本文件 L12204/L12216/L12259 等已使用 RETURN_TERMINATOR_OPS，本替换使 _is_trivial_return_block 与之一致

**语义等价性证明**：
- `x in tuple` 与 `x in frozenset` 均为成员检测，当 x 为 hashable 字符串时两者语义
  完全等价（frozenset 略快 O(1)，但 2 元素差异可忽略）
- `RETURN_TERMINATOR_OPS` 已在 L12204/L12216/L12259 等同文件位置使用，本替换使
  `_is_trivial_return_block` 与之一致
- 编译期与运行期行为完全不变（True/False 结果在替换前后完全一致）

控制流不变，仅把字面量替换为已存在的模块级常量。

## 编译验证

```
python -c "import core.cfg.region_analyzer; import core.cfg.region_ast_generator"
```
**结果**：退出码 0，输出 `COMPILE_OK`。

## 回归测试

```
timeout 290 python .trae/specs/analysis-fix-iteration/run_region_tests.py SEQ
```
**结果**：`127 10 0 137 1.7 SEQ files=80` —— 与基线一致（127 passed, 10 预存失败, 0 errors）。无退化。

## 反模式消除情况

| 反模式 | 本轮处理 |
|---|---|
| `_fix_` / `_merge_` / `_patch_` 前缀 | 未引入 |
| 硬编码深度上限 | 未引入 |
| 控制流改变 | 未改变（字面量→常量替换，`in` 语义等价） |
| 测试文件修改 | 未修改任何测试文件 |
| 实例驱动判据（DRY 违背） | **已消除 1 处**（`_is_trivial_return_block` 内 `('RETURN_VALUE', 'RETURN_CONST')` 字面量替换为 `RETURN_TERMINATOR_OPS` 模块级常量，与 Pass5-TERNARY 同型，与 L12204/L12216/L12259 等位置一致） |

## 未完成项

1. **文件其他位置 50+ 处 `('RETURN_VALUE', 'RETURN_CONST')` 字面量**未替换（本轮仅替换
   Pass 5-TERNARY/SEQ 标记的 `_is_ternary_block` / `_is_trivial_return_block` 内 3 处）。
   全量替换需逐处评估语义等价性，留待后续 Pass 统一处理。
2. **`_loop_depth > 0` 跨层启发式消除**（Pass 4 已标记，对应 TODO[pass3-SEQ]-F）：中风险，
   需先在识别阶段完善 break 块标记。
3. **`_cond_jump_bs` 兜底分支删除**（Pass 1 TODO[pass2-SEQ]-C，已标记）：中风险，需先在
   `_identify_conditional_regions` 末尾扫描未认领条件跳转块。
4. **`_generate_block_statements` god-method 瘦身**（Pass 2 TODO[pass3-SEQ]-E）：高风险，
   需把语句边界判定移到识别阶段。
5. **`_is_trivial_return_block` Pattern 1 收紧为 `argval is None`**（Pass 2 TODO[pass2-SEQ]-B）：
   低风险但属控制流变更，需评估影响（本轮仅替换字面量为常量，未收紧 argval 检查）。
6. **10 例预存失败**：L1_basic NameError 类（测试基础设施问题）+ basic/test_b23yieldfrom_complex
   （字节码重建差异），非保守修复范围。

## 文件清单

- `/workspace/core/cfg/region_analyzer.py`（Fix 1：`_is_trivial_return_block` L16352 字面量→`RETURN_TERMINATOR_OPS` 替换 + 追加 [Pass5-SEQ] 段落）
- `/workspace/.trae/specs/analysis-fix-iteration/rounds/sequence/pass_05/fix_report.md`（本报告）
