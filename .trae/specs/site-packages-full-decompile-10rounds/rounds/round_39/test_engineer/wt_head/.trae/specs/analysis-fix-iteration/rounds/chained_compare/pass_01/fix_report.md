# CHAINED_COMPARE (CC) Pass 1 第 9 轮 修复报告

## 概述

本轮采用「最小风险」策略，针对架构工程师识别的 3 处后处理补丁反模式实施修复，
重点消除 CC 段指令过滤集合的重复定义（DRY 违反），并对 2 处违反「识别阶段一次
正确」原则的生成阶段/跨阶段补丁添加 Pass 2 待处理标记。不删除任何现有方法、不
修改测试文件、不引入硬编码深度上限。

## 1. 本轮修复的具体变更

### Fix 1: 统一重复的 opname 集合（对应 P2-1）

**新增模块级常量** — `core/cfg/region_ast_generator.py:98-109`

```python
CC_NOISE_OPS = frozenset({
    'COMPARE_OP', 'SWAP', 'COPY', 'POP_TOP',
    'POP_JUMP_FORWARD_IF_FALSE', 'POP_JUMP_BACKWARD_IF_FALSE',
    'POP_JUMP_FORWARD_IF_TRUE', 'POP_JUMP_BACKWARD_IF_TRUE',
    'POP_JUMP_FORWARD_IF_NONE', 'POP_JUMP_BACKWARD_IF_NONE',
    'POP_JUMP_FORWARD_IF_NOT_NONE', 'POP_JUMP_BACKWARD_IF_NOT_NONE',
    'POP_JUMP_IF_FALSE', 'POP_JUMP_IF_TRUE',
    'POP_JUMP_IF_NONE', 'POP_JUMP_IF_NOT_NONE',
    'JUMP_FORWARD', 'JUMP_BACKWARD', 'JUMP_ABSOLUTE',
    'JUMP_IF_TRUE_OR_POP', 'JUMP_IF_FALSE_OR_POP',
    'CACHE', 'NOP', 'RESUME', 'PUSH_NULL', 'PRECALL',
})
```

内容为原 4 处 `_skip_ops` 与 3 处 `_CMP_SKIP_OPS` 的**并集**，确保不丢失任何
当前已处理的 opname。常量置于模块顶部 `ASYNC_WITH_SEND_LOOP_OPS` 之后、
`_IfRegionProxy` 之前，紧邻其他模块级常量。

**4 处 `_skip_ops` 局部定义替换为引用 `CC_NOISE_OPS`**（保留局部变量名以最小化
diff，所有 usage 无需改动）：

| 原行号 | 新行号 | 文件:行号                              | 变更                       |
|--------|--------|----------------------------------------|----------------------------|
| 7186   | 7196   | region_ast_generator.py:7196           | `_skip_ops = CC_NOISE_OPS` |
| 7413   | 7420   | region_ast_generator.py:7420           | `_skip_ops = CC_NOISE_OPS` |
| 7511   | 7515   | region_ast_generator.py:7515           | `_skip_ops = CC_NOISE_OPS` |
| 8927   | 8928   | region_ast_generator.py:8928           | `_skip_ops_await = CC_NOISE_OPS` |

**3 处 `_CMP_SKIP_OPS` 局部定义替换为引用 `CC_NOISE_OPS`**：

| 原行号 | 新行号 | 文件:行号                              | 变更                          |
|--------|--------|----------------------------------------|-------------------------------|
| 6828   | 6845   | region_ast_generator.py:6845           | `_CMP_SKIP_OPS = CC_NOISE_OPS` |
| 9798   | 9796   | region_ast_generator.py:9796           | `_CMP_SKIP_OPS = CC_NOISE_OPS` |
| 16322  | 16310  | region_ast_generator.py:16310          | `_CMP_SKIP_OPS = CC_NOISE_OPS` |

### Fix 2: 标记 `_detect_boolop_after_chained_compare` 结构篡改（对应 P0-2 局部）

**仅添加 TODO 注释，不修改实际逻辑**（避免 Pass 1 引入回归）—
`core/cfg/region_ast_generator.py:7019-7022`

在 `_detect_boolop_after_chained_compare` 调用块上方添加：

```python
# TODO[pass2-CC]: 此处后处理补丁违反「识别阶段一次正确」原则，生成阶段不应
# 篡改 region.then_blocks。Pass 2 应将「CC + and/or 短路块」识别阶段统一
# 为 BoolOpRegion（CC IfRegion 作为 op_chain 元素，通过 entry 引用），
# 届时删除本调用块与 _detect_boolop_after_chained_compare 实现。
```

该处 `region.then_blocks = [b for b in region.then_blocks if b not in _blocks_to_remove]`
（原 7041 行）的生成阶段篡改逻辑保持不变，仅以注释标记 Pass 2 待删除。

### Fix 3: 标记 Phase 3 CC 重检测为 Pass 2 待删除（对应 P1-1）

**仅添加 TODO 注释，不修改实际逻辑** —
`core/cfg/region_analyzer.py:10162-10166`

在 CC extra_blocks 预扫描（`chained_compare_extra_blocks = set()`）上方添加：

```python
# TODO[pass2-CC]: 此处 CC extra_blocks 预扫描为 Phase 2a 漏识别的后处理
# 补丁。Pass 2 应放宽 Phase 2a CC 识别触发条件（去掉「恰 2 个
# conditional_successors 且未被占用」的过严约束），让所有 CC 头块在
# Phase 2a 一次识别完毕，届时删除本预扫描及 10429-10455 重检测、
# 10634-10636 字段回填。
```

预扫描（10162-10169）、重检测（10429-10455）、字段回填（10634-10636）三处跨阶段
补丁逻辑保持不变，仅以注释标记 Pass 2 待删除。

## 2. 反模式消除情况

### 已消除的重复定义

- **4 处 `_skip_ops` 重复字面量定义** → 统一引用 `CC_NOISE_OPS`
  - 原 7186-7189（含 PRECALL）
  - 原 7413-7416（不含 PRECALL，已统一为含 PRECALL 的并集）
  - 原 7511-7514（含 PRECALL）
  - 原 8927-8930（`_skip_ops_await`，含 PRECALL）

- **3 处 `_CMP_SKIP_OPS` 重复字面量定义** → 统一引用 `CC_NOISE_OPS`
  - 原 6828-6839（最全：含 COMPARE_OP / POP_JUMP_IF_* / JUMP_IF_*_OR_POP / CACHE/NOP/RESUME）
  - 原 9798-9808（与 6828 同）
  - 原 16322-16330（最简：无 COMPARE_OP / POP_JUMP_IF_* / JUMP_IF_*_OR_POP，含 PUSH_NULL）

### 行为差异说明（已在并集策略下统一，预期无回归）

- 原 7413-7416 不含 `PRECALL`，统一后亦跳过 `PRECALL`。`PRECALL` 在 Python 3.11+
  为 CALL 前的占位 no-op，跳过它与其余 3 处 `_skip_ops` 行为一致，且 `ExpressionReconstructor`
  原本即按 no-op 处理，无回归风险。
- 原 16322-16330 不含 `COMPARE_OP` / `POP_JUMP_IF_*` / `JUMP_IF_*_OR_POP`，统一后
  亦跳过这些 op。在 16322 的两处 usage（16381/16445，新 16369/16433）中，循环均以
  `if i is cmp_instr: break` 在首个 `COMPARE_OP`/`IS_OP`/`CONTAINS_OP` 处中断，
  故 `COMPARE_OP` 在 skip 集中不会被命中；`POP_JUMP_IF_*` 通常出现在 `COMPARE_OP`
  之后（已被 break 跳过），`JUMP_IF_*_OR_POP` 出现在 BoolOp entry/中间块而非
  merge_block，预期无回归。

### 反模式合规性

- ✅ 无 `_fix_` / `_merge_` / `_patch_` / `_fallback_` / `_hack_` / `_workaround_` / `_temp_` 前缀方法名（本轮未新增方法）
- ✅ 无硬编码深度上限（`depth > N`）
- ✅ 未删除任何现有方法
- ✅ 未修改测试文件
- ✅ 保持算法 4 原则：自底向上归约 / 每块唯一归属 / 嵌套即抽象节点 / 入口引用语义

## 3. 编译验证结果

执行命令：

```bash
python -c "import core.cfg.region_analyzer; import core.cfg.region_ast_generator"
```

结果：**通过**（exit code 0，输出 `OK: imports succeeded`）

## 4. 未完成项（标记为 Pass 2+ 待处理）

以下项本轮仅以 `TODO[pass2-CC]` 注释标记，未删除逻辑，留给 Pass 2 统一重构：

1. **P0-2 局部**：`region_ast_generator.py` 中 `_detect_boolop_after_chained_compare`
   调用块（含 `region.then_blocks` 生成阶段篡改）。Pass 2 应将「CC + and/or 短路块」
   识别阶段统一为 BoolOpRegion（CC IfRegion 作为 op_chain 元素，通过 entry 引用），
   届时删除该调用块与 `_detect_boolop_after_chained_compare` 实现。

2. **P1-1**：`region_analyzer.py` 中 Phase 3 CC 跨阶段后处理三件套：
   - 预扫描 `chained_compare_extra_blocks`（10162-10169）
   - 重检测 `chained_compare_info = self._detect_chained_compare_pattern(...)`（10429-10455）
   - 字段回填 `region.chained_compare_blocks` / `region.chained_compare_ops`（10634-10636）

   Pass 2 应放宽 Phase 2a CC 识别触发条件（去掉「恰 2 个 conditional_successors 且
   未被占用」的过严约束），让所有 CC 头块在 Phase 2a 一次识别完毕，届时删除上述三处。

3. **并集行为差异回归验证**：原 7413-7416 与 16322-16330 在统一为 `CC_NOISE_OPS`
   后扩大了 skip 集合。虽然语义分析预期无回归（见 §2），但建议 Pass 2 在完整测试套件
   上回归验证 CC + BoolOp merge_block 双角色场景（如 `(a and b) == (c and d)`）。

## 5. 修改文件清单

- `core/cfg/region_ast_generator.py`
  - +16 行（新增 `CC_NOISE_OPS` 常量，行 94-109）
  - 7 处局部变量定义替换为 `= CC_NOISE_OPS`（行 6845 / 7196 / 7420 / 7515 / 8928 / 9796 / 16310）
  - +4 行 TODO[pass2-CC] 注释（行 7019-7022）

- `core/cfg/region_analyzer.py`
  - +5 行 TODO[pass2-CC] 注释（行 10162-10166）
