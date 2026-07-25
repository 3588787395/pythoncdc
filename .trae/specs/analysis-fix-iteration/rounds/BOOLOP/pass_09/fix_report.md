# Pass 9 BOOLOP 修复报告

## 修复内容

### Fix 1: 同步 `_identify_boolop_regions` docstring §1 归约过程 Step 1 / Step 3，补记 5 个排除集合与 _detect_boolop_chain_start 调度器入口

**问题位置**：`/workspace/core/cfg/region_analyzer.py:13900`（`_identify_boolop_regions` docstring §1 归约过程 Step 1 + Step 3）

**问题根因**（与 Pass9-IF / Pass9-ASSERT / Pass9-MATCH 同型——docstring 与实际控制流不同步）：

`_identify_boolop_regions` docstring §1 归约过程 Step 1 原文：
```
Step 1: 构建 claimed 集合（已占用块集合）
        - 收集所有已被其他区域占用的块
        - 特殊排除: 循环条件块（允许循环条件中的boolop）
```

Step 3 原文：
```
Step 3: 链式检测（两种模式）
        - 模式A: _detect_boolop_short_circuit_chain()
                JUMP_IF_FALSE_OR_POP / JUMP_IF_TRUE_OR_POP 链
        - 模式B: _detect_boolop_conditional_chain()
                POP_JUMP_IF_FALSE / POP_JUMP_IF_TRUE 链
```

与实际控制流存在两处口径差异：

(a) **Step 1 实际构建 5 个排除/协调集合**：表述为「构建 claimed 集合 + 特殊排除
循环条件块（loop_condition_blocks）」，但实际代码在主循环前构建 **5 个**排除/协调
集合（grep `= set\(\)` 在本函数内命中：match_case_body_blocks L14228 /
assert_region_entries L14238 / value_chain_cmp_if_entries L14247 等）：
- claimed + loop_condition_blocks（Step 1 已述）
- match_case_body_blocks / match_case_entry_offsets（MatchRegion guard 块排除）
- assert_region_entries（[Round4-12] AssertRegion.entry 不被 BoolOp 抢占）
- value_chain_cmp_if_entries（[Round4-04] 值上下文链式比较 IfRegion.entry 不被
  BoolOp 抢占）

Step 1 仅提及前 2 个，未提及后 3 个 [Round4-12] / [Round4-04] 新增排除集合。

(b) **Step 3 实际入口为 _detect_boolop_chain_start 调度器**：表述为「模式A:
_detect_boolop_short_circuit_chain() / 模式B: _detect_boolop_conditional_chain()」，
但实际代码主循环入口调用的是 **_detect_boolop_chain_start** 调度器（grep
`chain = self._detect_boolop_chain_start(block, claimed)` 在本文件仅 1 处命中，
L14307），由调度器内部按字节码模式分派到 _detect_boolop_short_circuit_chain /
_detect_boolop_conditional_chain。Step 3 直接列两个 _detect_*_chain 方法，未提及
_detect_boolop_chain_start 调度器层（仅在下方「原有简要说明 / 调用链」段提及）。

原表述可能误导读者认为 Step 1 仅 2 个集合、Step 3 直接调用两个检测器。

**修复策略**（与 Pass9-IF / Pass9-ASSERT / Pass9-MATCH 同型——仅 docstring 文本同步，
不改控制流）：

在 docstring §1 归约过程 Step 6 之后追加 `[Pass9-BOOLOP]` 段落，补记：
1. (a) Step 1 实际构建 5 个排除集合（含 [Round4-12] / [Round4-04] 新增 3 个）
2. (b) Step 3 实际入口为 _detect_boolop_chain_start 调度器，内部分派到两个检测器
3. 采用 grep 验证方式引用行号（避免递归漂移，与 Pass8-LOOP / Pass9-LOOP 同型）
4. 不重写「Step 1 / Step 3」列表（与 Pass9-IF / Pass9-ASSERT / Pass9-MATCH
   同型保守策略一致）

控制流不变，仅 docstring 文本同步。

## 编译验证

```
python -c "import core.cfg.region_analyzer; import core.cfg.region_ast_generator"
```
**结果**：退出码 0，输出 `COMPILE_OK`。

## 回归测试

```
timeout 290 python .trae/specs/analysis-fix-iteration/run_region_tests.py BOOLOP
```
**结果**：`79 0 0 79 1.5 BOOLOP files=80` —— 与基线一致（79 passed, 0 failed, 0 errors）。无退化。

## 反模式消除情况

| 反模式 | 本轮处理 |
|---|---|
| `_fix_` / `_merge_` / `_patch_` 前缀 | 未引入 |
| 硬编码深度上限 | 未引入 |
| 控制流改变 | 未改变（仅 docstring 文本同步） |
| 测试文件修改 | 未修改任何测试文件 |
| docstring 与实际控制流不同步（与 Pass9-IF / Pass9-ASSERT / Pass9-MATCH 同型） | **已同步**（补记 Step 1 五个排除集合 + Step 3 _detect_boolop_chain_start 调度器入口） |

## 未完成项

1. **`'FALSE' in opname` / `'TRUE' in opname` 子串匹配统一替换为结构判据**（Pass 5 已标记首处，
   Pass6-BOOLOP 同步行号引用；Pass7-ASSERT 已标记 `_detect_assert_boolop_chain` /
   `_build_assert_boolop_condition` 同型；Pass8-BOOLOP 在 region_ast_generator.py 的
   `_generate_boolop` 内标记首处；余 16+ 处待统一替换）：需先按
   FALSE/TRUE/IF_NONE/IF_NOT_NONE/NONE 多类归类，再分别定义 frozenset 常量，
   高风险重构。
2. **`_generate_boolop` 内 if-like 复杂短路结构分支两处同型子串匹配判据未单独标记**
   （Pass8-BOOLOP 仅标记 `_is_outer_condition` 分支首处）：本轮 grep 验证 3 处命中，
   仅首处添加 [Pass8-BOOLOP] 标记，余 2 处与本处同型，待后续 Pass 统一标记或替换。
3. **`_identify_boolop_regions` 两段重复 docstring 合并**（Pass 2/3 已评估）：长版 +
   短版「保留供快速参考」，删除任一段都会损失独有信息，需谨慎合并。
4. **BOOLOP→TERNARY 识别顺序调换**（Pass 1 已明确为高风险）：影响全流水线。
5. **`_detect_boolop_after_chained_compare` 生成期后处理**（Pass 1 已列为后续建议）：
   与 IF 区域 TODO[pass2-CC] 同源，需识别阶段统一为 BoolOpRegion 后删除。
6. **Step 1 / Step 3 表述与实际控制流差异**：本轮已在 §1 归约过程 Step 6 后追加
   [Pass9-BOOLOP] 段落补记。后续 Pass 若实施「彻底重写 Step 1 / Step 3 列表」可一并同步。

## 文件清单

- `/workspace/core/cfg/region_analyzer.py`（Fix 1：`_identify_boolop_regions` docstring §1 归约过程 Step 6 后追加 [Pass9-BOOLOP] 段落，补记 Step 1 五个排除集合 + Step 3 _detect_boolop_chain_start 调度器入口）
- `/workspace/.trae/specs/analysis-fix-iteration/rounds/BOOLOP/pass_09/fix_report.md`（本报告）
