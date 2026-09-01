# R09 修复报告 — Pattern G2（f-string COMPARE_OP 截断 in `_if_extract_cond_instructions`）

## 1. 修复目标

| 字段 | 值 |
|---|---|
| 轮次 | R09 (rcm-r09) |
| 目标 pyc | `site-packages/IQCommon/backtest/backtest.pyc`（R08 状态 `failed`） |
| 缺陷模式 | Pattern G2（f-string FormattedValue 内 COMPARE_OP 触发 `_if_extract_cond_instructions` 清空启发式，截断 JoinedStr） |
| 修复文件 | `core/cfg/region_ast_generator.py` |
| 修复方法 | `_if_extract_cond_instructions`（COMPARE_OP 清空守卫，L9760-9784） |
| 修复前 repro | 9 DEFECT-REPRO（repro 01-08, 12） |
| 修复后 repro | 1 DEFECT-REPRO（repro 12，独立模式：链式比较跨块误判） |
| 回归测试 | 1 failed, 154 passed, 19 errors（与 R08 基线**完全一致**，零回归） |

## 2. 根因分析

- **缺陷层**：区域生成层 `core/cfg/region_ast_generator.py`
- **缺陷方法**：`_if_extract_cond_instructions`（L9565-9793）
- **根因**：L9760（原 L9730）的启发式在 `COMPARE_OP and pre_seen_store` 时无条件清空 `pre_instrs`：
  ```python
  if instr.opname == 'COMPARE_OP' and pre_seen_store:
      pre_instrs = []
      continue
  ```
  意图：最后一个 pre-statement STORE 之后的首个 COMPARE_OP 视为 if 条件起点，丢弃杂散累积指令。
- **为何出错**：COMPARE_OP 可合法出现在 f-string 的 FormattedValue 内部（如 `f'{a != b}'`、`f'{enable_debug == "true"}'`）。当条件块含带内嵌比较的 f-string 赋值时，启发式在首个 f-string 内 COMPARE_OP 处清空 `pre_instrs`，丢弃全部已累积的 f-string 片段。f-string 链被切断，仅尾部片段到达 BUILD_STRING，生成截断的 JoinedStr。
- **backtest.pyc 实证**：启发式在 offset 1402/1422 触发两次，丢弃 25 段中的 1-20 段。`BUILD_STRING 25` 仅弹 5 个可用值。`handle_backtest_build` true_diffs=327。

### 确诊路径

1. `diag_dump_cfg.py`：确认整个 f-string 链（offset 1334-1456）在单一基本块（block @1188, 97 instrs）内，无块分裂。
2. `diag_dump_ast.py`：`user_code` 的 JoinedStr 仅 5 个 values（应 25），起始为 LOAD_CONST 50（offset 1430，第二个 COMPARE_OP 之后）。
3. `diag_trace_reconstruct.py`：reconstruct 仅收到 9 条指令（offset 1428-1454，尾部），而非完整 96 条。

## 3. 修复方案

在 `_if_extract_cond_instructions` 的 COMPARE_OP 清空分支加入**双重结构守卫**，覆盖 f-string 内 COMPARE_OP 的两种位置（L9760-9784）：

```python
if instr.opname == 'COMPARE_OP' and pre_seen_store:
    # [R09 fix] ... (算法原则 2：每块唯一归属)
    # 双重结构守卫（覆盖 f-string 内 COMPARE_OP 的两种位置）：
    # (a) pre_instrs 已含 FORMAT_VALUE —— COMPARE_OP 位于 f-string 链中段
    #     （如 f'{a!s}_{a != b!s}'，COMPARE_OP 在某 FORMAT_VALUE 之后）。
    # (b) COMPARE_OP 紧随其后即是 FORMAT_VALUE —— COMPARE_OP 是某
    #     FormattedValue 的首个子表达式（如 f'{a != b!s}...'，COMPARE_OP
    #     是 f-string 第一个 FormattedValue，其前无 FORMAT_VALUE）。
    #     正常 if 条件的 COMPARE_OP 紧随其后是 POP_JUMP_IF_FALSE，不会命中。
    _has_format_value = any(pi.opname == 'FORMAT_VALUE' for pi in pre_instrs)
    _next_is_format_value = (
        _instr_idx + 1 < len(_iter_instrs)
        and _iter_instrs[_instr_idx + 1].opname == 'FORMAT_VALUE'
    )
    if not _has_format_value and not _next_is_format_value:
        pre_instrs = []
        continue
```

- **修改点 1**：主循环改为 `enumerate`（L9634），支持前瞻 `_iter_instrs[_instr_idx + 1]`。
- **修改点 2**：COMPARE_OP 清空分支加双重守卫（L9760-9784）。
- **算法依据**：区域归约算法原则 2「每块唯一归属」—— FORMAT_VALUE 是 f-string 链中段的结构标记（非启发式）：CPython 把 FormattedValue 编译为 `<expr 指令> + FORMAT_VALUE`，把 JoinedStr 编译为 `<片段序列> + BUILD_STRING N`。COMPARE_OP 若属于某 FormattedValue 的子表达式，其后必跟 FORMAT_VALUE（比较结果被格式化）；而 if 条件的 COMPARE_OP 后跟 POP_JUMP_IF_FALSE。两个结构信号（pre_instrs 含 FORMAT_VALUE / 下一条是 FORMAT_VALUE）精确区分两种 COMPARE_OP 归属，无需跨区域启发式。
- **非补丁**：守卫基于字节码结构标记（FORMAT_VALUE 位置），无硬编码 offset / 无跨区域启发式 / 无后处理。无 FORMAT_VALUE 时保留原清空行为（正常 if 条件提取不变）。

## 4. 算法依据（FORMAT_VALUE 标记如何对齐区域归约算法）

4 原则合规：

- **自底向上归约**：✓ 未改变（守卫在生成层 pre_stmt 提取阶段，不影响归约顺序）
- **每块唯一归属**：✓ **强化** — COMPARE_OP 的归属由结构标记判定：若属于 f-string 表达式子链（FORMAT_VALUE 在场），则归 f-string 赋值 pre_stmt；若属于 if 条件（无 FORMAT_VALUE，后跟 POP_JUMP_IF_FALSE），则归 IfRegion 条件。原启发式误把 f-string 内 COMPARE_OP 归 IfRegion 条件，违反唯一归属。
- **嵌套即抽象节点**：✓ 未改变
- **入口引用语义**：✓ 未改变

字节码结构事实（CPython 3.11）：
- `f'{a != b!s}'` → `LOAD_FAST a; LOAD_FAST b; COMPARE_OP !=; FORMAT_VALUE 1`。COMPARE_OP 后必跟 FORMAT_VALUE。
- `f'{a!s}_{a != b!s}'` → `...; FORMAT_VALUE 1; LOAD_CONST '_'; LOAD_FAST a; LOAD_FAST b; COMPARE_OP !=; FORMAT_VALUE 1; ...`。中段 COMPARE_OP 之前已有 FORMAT_VALUE。
- `if a == 0:` → `LOAD_FAST a; LOAD_CONST 0; COMPARE_OP ==; POP_JUMP_FORWARD_IF_FALSE`。条件 COMPARE_OP 后跟 POP_JUMP_IF_FALSE，无 FORMAT_VALUE。

## 5. 注释更新清单

| 方法 | 文件:行 | 更新内容 |
|---|---|---|
| `_if_extract_cond_instructions` | `region_ast_generator.py:9567-9604` | docstring 重写为 4 节模板（算法依据 / 归约顺序 / 唯一归属判定 / 入口引用语义）。第 3 节追加 `[R09 fix]` 段：说明 COMPARE_OP 清空守卫的双重视角（pre_instrs 含 FORMAT_VALUE / 下一条是 FORMAT_VALUE）、缺陷（f-string 内 COMPARE_OP 误清空）、算法依据（原则 2）、非补丁声明。保留原 `[R6 fix]`/`[R23 Bug1 fix]` 段。 |
| `_if_extract_cond_instructions` 行内注释 | `region_ast_generator.py:9760-9784` | 新增 `[R09 fix]` 行内注释块：解释双重结构守卫的 (a)/(b) 两种位置、正常 if 条件不命中的原因。 |

## 6. 回归结果

### 最小复现实例（14 个）

| # | 实例 | pre-fix | post-fix | 变化 |
|---|---|---|---|---|
| 01 | fstring_neq_in_if_cond_block | DEFECT (5→1) | OK (5→5) | **修复** |
| 02 | fstring_eq_in_if_cond_block | DEFECT (5→1) | OK (5→5) | **修复** |
| 03 | fstring_multi_compare | DEFECT (8→1) | OK (8→8) | **修复** |
| 04 | fstring_long_chain_with_compare | DEFECT (11→5) | OK (11→11) | **修复** |
| 05 | fstring_compare_first_segment | DEFECT (4→3) | OK (4→4) | **修复**（前瞻守卫 (b)） |
| 06 | fstring_compare_last_segment | DEFECT (4→0) | OK (4→4) | **修复** |
| 07 | fstring_gt_lt_compare | DEFECT (8→1) | OK (8→8) | **修复** |
| 08 | fstring_compare_with_method_call | DEFECT (4→1) | OK (4→4) | **修复** |
| 09 | fstring_two_assigns_before_if | OK (4→4) | OK (4→4) | 不变 |
| 10 | ctrl_no_fstring_compare_in_if | OK (0→0) | OK (0→0) | 不变 |
| 11 | ctrl_fstring_no_compare | OK (5→5) | OK (5→5) | 不变 |
| 12 | fstring_chained_compare | DEFECT (4→0) | DEFECT (4→0) | **不变（独立模式，见 §7）** |
| 13 | fstring_compare_in_elif_block | OK (4→4) | OK (4→4) | 不变 |
| 14 | fstring_compare_in_while_cond_block | OK (4→4) | OK (4→4) | 不变 |

- **DEFECT-REPRO 计数**：pre-fix 9 → post-fix 1（repro_12 为独立模式，非本轮 scope）
- **CTRL 组（09-11, 13-14）全部 OK**：证明守卫不影响正常 if 条件提取与无 COMPARE_OP 的 f-string。

### 目标 pyc 验证（backtest.pyc）

| 指标 | pre-fix (R08) | post-fix (R09) | 变化 |
|---|---|---|---|
| decompile_status | failed | failed | 持平（残留 quoting bug，见 §7） |
| user_code f-string 段数 | 5/25（截断） | **25/25（完整）** | **结构修复** |
| `{frequency != 'tick'!s}` 段 | 丢失 | **保留** | ✓ |
| `{enable_debug == 'true'!s}` 段 | 丢失 | **保留** | ✓ |
| 反编译产物编译 | OK（true_diffs=327） | **SyntaxError**（line 69） | 退化（latent quoting bug 暴露，见 §7） |

- f-string 截断缺陷（Pattern G2）**已修复**：25/25 段全部保留，两个 COMPARE_OP FormattedValue 均在位。
- 反编译产物出现 SyntaxError 是**独立的 latent quoting bug**（Pattern Q，见 §7），非本轮 COMPARE_OP 截断缺陷。该 bug 在 pre-fix 被 f-string 截断掩盖（`{'1'!s}` 段被丢弃），post-fix 因 f-string 完整而暴露。

### 回归 pytest（与 R08 同 scope: testqouter/）

```
python -m pytest testqouter/ --timeout=90 --tb=no -q --continue-on-collection-errors
1 failed, 154 passed, 147 warnings, 19 errors in 20.32s
```

| 指标 | R08 基线 | R09 post-fix | 变化 |
|---|---|---|---|
| failed | 1 | 1 | 持平（test_r2q_10_with_open_read.py FileNotFoundError，预存在） |
| passed | 154 | **154** | **持平（零回归）** |
| errors | 19 | 19 | 持平（均为预存在测试基建问题：detail_test.py 引用 stale pyc at `d:\Desktop\ptrade相关\pythoncdc\` 等） |

**R09 双重守卫零增量回归**：守卫加入前后 pytest 计数完全一致（1 failed, 154 passed, 19 errors），证明新守卫不破坏既有行为。

### 模块编译检查

```
python -c "import core.cfg.region_analyzer; import core.cfg.region_ast_generator; import core.cfg.code_generator"
IMPORT OK
```

## 7. 残留不一致数

### 本轮残留

1. **repro_12 fstring_chained_compare**（DEFECT-REPRO，4→0）：链式比较 `a < b < c` 在 f-string FormattedValue 内产生 `JUMP_IF_FALSE_OR_POP` + `JUMP_FORWARD`（属 FORWARD_JUMP_OPS），使 f-string 赋值跨多个基本块。区域分析层把链式比较的跳转结构误判为条件区域（IfRegion），在 `_if_extract_cond_instructions` 被调用前已发生误判。反编译产物为 `if a < '_' < c: pass`（f-string 完全丢失）。**非本轮 FORMAT_VALUE 守卫可修复**——需区域分析层识别「链式比较跳转属于 f-string 表达式子链，非条件区域」。独立模式（Pattern G3：链式比较跨块误判），后续轮次修复。

2. **backtest.pyc f-string quoting bug**（Pattern Q）：反编译产物 line 69 `user_code = f'...{"enabled": {'1'!s}...'` 中，FormattedValue 内 Constant 字符串 `'1'` 用单引号发射，与外层单引号 f-string 冲突 → SyntaxError。根因在 `code_generator.py:_generate_joined_str_from_dict`（L4152-4155）的引号选择逻辑：当 content 同时含 `'` 和 `"` 时回退单引号，但未转义 FormattedValue 内 Constant 字符串的引号。该 bug 为 **latent**（pre-fix 因 f-string 截断，`{'1'!s}` 段被丢弃而未暴露）。**非本轮 scope**（不同组件 code_generator.py，不同缺陷模式），后续轮次修复。修复后 backtest.pyc 预计可解锁为 partial/ok。

### backtest.pyc 状态

- decompile_status: **failed**（SyntaxError from Pattern Q quoting bug）
- 但 Pattern G2（f-string COMPARE_OP 截断）**已修复**：f-string 5/25 → 25/25 段。
- `pyc_batch_verify.py single` 因 `py_compile.compile(..., quiet=2)` 在 Python 3.11.7 返回 None（pre-existing 工具 bug，自 R07 起记录在 pyc_index.json error 字段），无法自动测量 match_rate。

### 跨轮残留（不变）

- Pattern T3 残留（graph.pyc 4 mismatch 函数）
- Pattern T2（R07，except body drop on return-const）
- repro_05 trailing-return（R07）
- Pattern A2 / B / C / E / F / M2（跨轮）

## 8. 累计成功率变化（R08 → R09）

| 指标 | R08 | R09 | 变化 |
|---|---|---|---|
| 累计成功率 | 70.90% | 70.90% | 持平 |
| verified pyc | 31 | 31 | 持平 |
| ok/partial pyc | 27 | 27 | 持平 |
| backtest.pyc | failed (0%, f-string 截断) | failed (0%, f-string 完整但 quoting bug) | 持平（残留模式转移：G2 截断 → Q quoting） |

- **成功率持平原因**：backtest.pyc 的 Pattern G2（f-string 截断）已结构修复（5/25→25/25 段），但暴露的 latent Pattern Q（quoting bug）使反编译产物 SyntaxError，可测量 match_rate 仍 0%。backtest.pyc 状态未变（failed），累计成功率不变。
- **结构进展**：R09 修复了 Pattern G2（f-string COMPARE_OP 截断），8/9 DEFECT-REPRO 修复，零回归。backtest.pyc 的 f-string 从截断（5/25）到完整（25/25），为后续修复 Pattern Q 后解锁 backtest.pyc 铺路。
- **下一轮建议**：修复 Pattern Q（code_generator.py f-string 引号选择，FormatttedValue 内 Constant 字符串引号转义）可解锁 backtest.pyc 为 partial/ok；修复 Pattern G3（链式比较跨块误判）可修复 repro_12。
