# Pass 9 CC (Chained Compare) 修复报告

## 修复内容

### Fix 1: 同步 `_identify_chained_compare_regions` docstring §1 识别策略 / §2 字节码模式，补记 IS_OP/CONTAINS_OP 扩展（[Round6-01/02]）

**问题位置**：`/workspace/core/cfg/region_analyzer.py:9843`（`_identify_chained_compare_regions` docstring §1 识别策略 + §2 字节码模式特征指令）

**问题根因**（与 Pass9-IF / Pass9-ASSERT / Pass9-BOOLOP / Pass9-MATCH 同型——docstring 与实际控制流不同步）：

`_identify_chained_compare_regions` docstring §1 识别策略原文：
```
- 识别策略: 以 CPython 编译器的固定字节码模式（COPY(arg=2) +
  COMPARE_OP 指令对）为锚点，沿 fallthrough 后继链追踪连续的
  COMPARE_OP 块，从而把 a < b < c 这类多比较运算还原为一个语义整体
```

§2 字节码模式特征指令：
```
特征指令:    COPY(arg=2), COMPARE_OP
```

仅提及 COMPARE_OP。但实际 `_is_chained_compare_header`（grep
`def _is_chained_compare_header` 在本文件仅 1 处命中，L11546）与
`_detect_chained_compare_pattern` 内的判据是 `instrs[i+1].opname in
('COMPARE_OP', 'IS_OP', 'CONTAINS_OP')`（grep `instrs[i + 1].opname in
('COMPARE_OP', 'IS_OP', 'CONTAINS_OP')` 在本文件 2 处命中，L11587/L11612）——
即除 COMPARE_OP 外还接受 **IS_OP**（链式 `is`/`is not`）与 **CONTAINS_OP**
（链式 `in`/`not in`），由 [Round6-01/02] 修复（注释「链式 is/in 也走 COPY +
IS_OP/CONTAINS_OP 模式」）。

§1/§2 仅提及 COMPARE_OP，未提及 IS_OP/CONTAINS_OP 的扩展，可能误导读者认为
本识别器仅处理 `<`/`>`/`==` 等比较运算符链。

**修复策略**（与 Pass9-IF / Pass9-ASSERT / Pass9-BOOLOP / Pass9-MATCH 同型——
仅 docstring 文本同步，不改控制流）：

在 docstring §1 归约过程 Step 5 之后追加 `[Pass9-CC]` 段落，补记：
1. §1 识别策略表述为「COPY(arg=2) + COMPARE_OP 指令对」，但实际判据接受
   COMPARE_OP OR IS_OP OR CONTAINS_OP
2. §2 字节码模式特征指令仅列 COPY(arg=2)/COMPARE_OP，未列 IS_OP/CONTAINS_OP
3. 扩展由 [Round6-01/02] 修复（链式 is/in 也走 COPY + IS_OP/CONTAINS_OP 模式）
4. 采用 grep 验证方式引用行号（避免递归漂移，与 Pass8-LOOP / Pass9-LOOP 同型）
5. 不重写「§1 识别策略 / §2 字节码模式」列表（与 Pass9-IF / Pass9-ASSERT /
   Pass9-BOOLOP / Pass9-MATCH 同型保守策略一致）

控制流不变，仅 docstring 文本同步。

## 编译验证

```
python -c "import core.cfg.region_analyzer; import core.cfg.region_ast_generator"
```
**结果**：退出码 0，输出 `COMPILE_OK`。

## 回归测试

```
timeout 290 python .trae/specs/analysis-fix-iteration/run_region_tests.py CC
```
**结果**：`37 3 0 40 3.4 CC files=40` —— 与基线一致（37 passed, 3 预存失败, 0 errors）。无退化。

## 反模式消除情况

| 反模式 | 本轮处理 |
|---|---|
| `_fix_` / `_merge_` / `_patch_` 前缀 | 未引入 |
| 硬编码深度上限 | 未引入 |
| 控制流改变 | 未改变（仅 docstring 文本同步） |
| 测试文件修改 | 未修改任何测试文件 |
| docstring 与实际控制流不同步（与 Pass9-IF / Pass9-ASSERT / Pass9-BOOLOP / Pass9-MATCH 同型） | **已同步**（补记 §1/§2 仅提及 COMPARE_OP，实际接受 IS_OP/CONTAINS_OP） |

## 未完成项

1. **`_try_build_*` patch chain 统一**（Pass 2 已标记 `TODO[pass2-CC]`，Pass 7 进度同步）：
   高风险，需保证 walrus / literal-middle / method-call 三特例的栈模拟语义被统一路径覆盖。
   该 chain 是 3 个 failed 用例的直接成因，需统一操作数提取路径方可消除，非保守修复范围。
2. **Phase 3 CC extra_blocks 预扫描 / 重检测 / 字段回填删除**（Pass 2 已识别为后处理补丁）：
   前置依赖（放宽 Phase 2a CC 触发条件）未满足，直接删除会改变控制流并丢识别。
3. **`_detect_boolop_after_chained_compare` 消除**（Pass 1/2 已列）：中风险。
4. **`('COMPARE_OP', 'IS_OP', 'CONTAINS_OP')` 字面量元组统一替换为 `COMPARE_FAMILY_OPS`
   frozenset 模块级常量**（Pass8-CC 已标记首处 `_is_chained_compare_header`）：
   - `region_analyzer.py` 11 处 + `region_ast_generator.py` 13 处 = 24 处待统一替换
   - 与 Pass5-TERNARY/SEQ 已替换为 `RETURN_TERMINATOR_OPS` 同型 DRY 违背
   - 全量替换属高风险重构，需逐处评估语义等价性
5. **3 例预存失败**：walrus / literal-middle / method-call 三特例，需针对各自模式单独设计，
   非保守修复范围（与 §未完成项 1 同源）。
6. **§1 识别策略 / §2 字节码模式仅提及 COMPARE_OP、未提及 IS_OP/CONTAINS_OP 扩展**：
   本轮已在 §1 归约过程 Step 5 后追加 [Pass9-CC] 段落补记。后续 Pass 若实施「彻底重写
   §1 识别策略 / §2 字节码模式列表」可一并同步。

## 文件清单

- `/workspace/core/cfg/region_analyzer.py`（Fix 1：`_identify_chained_compare_regions` docstring §1 归约过程 Step 5 后追加 [Pass9-CC] 段落，补记 §1/§2 仅提及 COMPARE_OP，实际接受 IS_OP/CONTAINS_OP）
- `/workspace/.trae/specs/analysis-fix-iteration/rounds/chained_compare/pass_09/fix_report.md`（本报告）
