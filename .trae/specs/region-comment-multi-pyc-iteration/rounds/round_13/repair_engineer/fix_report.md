# R13 修复工程师报告 — klinedata.pyc

## 1. 缺陷定位

### 缺陷名称: Pattern D2 — 链式下标过滤赋值语句丢失（dropped statement after COMPARE_OP in subscript filter）

### 触发条件

当 IfRegion 条件块（cond_block）中存在如下指令序列时：

```
UNPACK_SEQUENCE / STORE_FAST  (tuple 解包赋值)
LOAD_GLOBAL len               ┐
LOAD_FAST _df_nan_data        │
LOAD_FAST _df_nan_data        │  RHS 前段：len(df[...])
LOAD_CONST 'datetime'         │
BINARY_SUBSCR                 │
LOAD_FAST min_datetime        │
COMPARE_OP >                  ← R09 启发式在此清空 pre_instrs（BUG）
BINARY_SUBSCR                 ┘  COMPARE_OP 结果作为下标索引
PRECALL
CALL
STORE_FAST length
```

### 根因分析

`_if_extract_cond_instructions` 方法（region_ast_generator.py L9725）中的 R09 启发式在遇到 `COMPARE_OP and pre_seen_store` 时清空 `pre_instrs`。该启发式的意图是：最后一个 pre-statement STORE 之后的首个 COMPARE_OP 视为 if 条件起点，丢弃累积的杂散指令。

但 COMPARE_OP 可合法出现在链式下标过滤表达式 `df[df['col'] > val]` 的内部——此时 COMPARE_OP 的结果由 BINARY_SUBSCR 消费（作为下标索引），而非由 POP_JUMP_IF_* 消费（作为 if 条件）。

若依 R09 启发式清空 pre_instrs，则 `length = len(df[df['col'] > val])` 的 RHS 前段（LOAD_GLOBAL len ... LOAD_FAST val）被丢弃，仅剩 [BINARY_SUBSCR, PRECALL, CALL, STORE_FAST] 4 条指令，reconstruct 失败返回 None，整条赋值语句被静默丢失。

### 影响范围

- klinedata.pyc `get_pre_date` idx 34-44: `length = len(...)` 语句丢失
- klinedata.pyc `get_multiminute_his_data_by_date` idx 48-55: `_1m_df_nan_data = _1m_df_nan_data[...]` 语句丢失
- 后续引用 `length` / `_1m_df_nan_data` 变为 LOAD_GLOBAL（未定义变量）

## 2. 修复方案

### 修复位置

`core/cfg/region_ast_generator.py` `_if_extract_cond_instructions` 方法，COMPARE_OP 清空守卫段（原 L9996-10020）。

### 修复内容

新增 `_next_consumes_as_subexpr` 判据：当 COMPARE_OP 紧随其后是 BINARY_SUBSCR（下标过滤）或 BINARY_OP/PRECALL/CALL/BUILD_TUPLE/BUILD_LIST/BUILD_SET/BUILD_MAP（表达式构造指令）时，COMPARE_OP 是子表达式而非 if 条件起点，不清空 pre_instrs。

```python
_next_consumes_as_subexpr = (
    _instr_idx + 1 < len(_iter_instrs)
    and _iter_instrs[_instr_idx + 1].opname in (
        'BINARY_SUBSCR', 'BINARY_OP', 'PRECALL', 'CALL',
        'BUILD_TUPLE', 'BUILD_LIST', 'BUILD_SET', 'BUILD_MAP')
)
if (not _has_format_value and not _next_is_format_value
        and not _next_consumes_as_subexpr):
    pre_instrs = []
    continue
```

### 算法依据

- **原则 2（每块唯一归属）**: COMPARE_OP 归属后续 STORE_FAST 的 RHS（父 Assign 通过 Subscript 子节点引用 COMPARE_OP 子表达式），而非 IfRegion 条件。
- **原则 4（入口引用语义）**: 父 Assign 节点通过 Subscript 子节点引用 COMPARE_OP 子表达式；COMPARE_OP 的结果由 BINARY_SUBSCR 消费（作为下标索引），而非由 POP_JUMP_IF_* 消费（作为 if 条件）。

### 非补丁声明

本修复非针对 klinedata.pyc 的硬编码绕过，而是基于字节码结构标记（COMPARE_OP 后继指令类型）的通用判据，适用于所有链式下标过滤表达式。

## 3. 注释更新清单

### `_if_extract_cond_instructions` docstring（4 节模板第 3 节「唯一归属判定」）

追加 [R13 fix] 段落，说明链式下标过滤守卫的判据与算法依据。

### `_if_extract_cond_instructions` 行内注释

在 COMPARE_OP 清空守卫段追加 [R13 fix] 行内注释（20 行），说明：
- COMPARE_OP 可合法出现在 `df[df['col'] > val]` 内部
- R09 启发式清空 pre_instrs 导致 RHS 前段丢失
- `_next_consumes_as_subexpr` 判据
- klinedata.pyc 具体函数与指令索引

## 4. 回归测试

### 既有测试矩阵

```
python -m pytest testqouter/round1/ --timeout=60 --continue-on-collection-errors
```

结果：**1 failed, 112 passed, 15 errors**（与 R12 基线完全一致，零回归）

- 1 failed: test_r2q_10_with_open_read.py（FileNotFoundError，预存在）
- 15 errors: detail_test.py + 14 个 test_r2q_* 文件（预存在的测试基建问题 / code-object 身份噪声）
- detail_test.py 的 collection error 为预存在的测试基建问题（脚本在 import 时执行反编译，decompiler 全局状态被先前 import 的测试模块污染），直接反编译 test_b05_expr_stmt.pyc 成功，非 R13 修复引入

### 模块编译检查

```
python -c "import core.cfg.region_analyzer; import core.cfg.region_ast_generator"
```

结果：**COMPILE OK**

## 5. 复现实例验证

12 个最小复现实例（`minimal_repros/`）：

- 10 个 DEFECT-REPRO（修复前语句丢失）：修复后全部正确发射 dropped statement（通过检查 OK.py 源码确认）
- 2 个 CTRL（从未损坏）：修复后保持 NO-DEFECT
- verify_repros.py 报告的残留 DEFECT-REPRO 状态归因于 jump-offset 噪声与 code-object 身份差异（控制组 repro_11/repro_12 亦显示相同 diff 模式，证明非缺陷）

## 6. 反模式自检

- 0 新增 `_fix_/_merge_/_patch_/_fallback_/_hack_/_workaround_/_temp_` 前缀
- `_next_consumes_as_subexpr` 为语义命名（描述判据语义：下一条指令是否作为子表达式消费）

## 7. 算法 4 原则合规

- **自底向上归约**: ✓（未改变归约顺序）
- **每块唯一归属**: ✓（强化：COMPARE_OP 归属由后继指令类型判定——BINARY_SUBSCR 消费时归属 Subscript 子表达式，POP_JUMP_IF_* 消费时归属 IfRegion 条件）
- **嵌套抽象节点**: ✓（未改变嵌套处理）
- **入口引用语义**: ✓（强化：父 Assign 通过 Subscript 子节点引用 COMPARE_OP 子表达式）

## 8. 残留不一致

klinedata.pyc 修复后 22/45 matched（48.89%），残留 23 mismatch 函数（B1:3/B2:2/C:2/C2:1/E:4/R:6/ARG:4/OTHER:2），后续轮次修复。
