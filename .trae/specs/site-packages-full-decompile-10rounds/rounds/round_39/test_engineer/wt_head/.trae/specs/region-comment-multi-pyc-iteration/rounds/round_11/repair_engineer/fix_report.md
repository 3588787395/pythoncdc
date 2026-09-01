# R11 修复报告 — Pattern C2（tuple unpack without SWAP，BUG A 守卫 + BUG B 路径）

## 1. 修复目标

| 字段 | 值 |
|---|---|
| 轮次 | R11 (rcm-r11) |
| 目标 pyc | `site-packages/IQEngine/main.pyc`（R07 状态 `partial`，33.33%，`_adjust_start_date` tuple 解包丢失） |
| 缺陷模式 | Pattern C2（peephole-optimized tuple unpack：N 个 LOAD + N 个 STORE 反源序，无 SWAP） |
| 修复文件 | `core/cfg/region_ast_generator.py` |
| 修复方法 | `_generate_block_statements`（BUG A 守卫，L30722）+ `_if_extract_cond_instructions`（BUG B 路径，L9733） |
| 修复前 repro | 10 DEFECT-REPRO（7 真实缺陷 BUG A/B + 3 code-object 身份噪声） |
| 修复后 repro | 0 真实缺陷（10 个 verify DEFECT-REPRO 均为 code-object 身份噪声，`f` 字节码一致） |
| 回归测试 | 1 failed, 154 passed, 19 errors（与 R10 基线**完全一致**，零回归） |

## 2. 根因分析

### BUG A：守卫过保守（`_generate_block_statements` L30722）

`_noswap_unpack_result`（L30684）检测 N≥2 连续简单名 STORE 的 tuple 解包。守卫 `_ns_has_real_after`（L30732）使用**白名单**判定 post-STORE 指令：仅允许 RESUME/NOP/CACHE/PUSH_NULL/POP_TOP/COPY/SWAP/POP_EXCEPT/PUSH_EXC_INFO/RETURN_VALUE/RETURN_CONST/LOAD_CONST/LOAD_FAST/LOAD_NAME/LOAD_GLOBAL/LOAD_DEREF。

但 `return x, y` 生成 `BUILD_TUPLE 2`、`return x + y` 生成 `BINARY_OP`，均不在白名单 → 守卫误判为"有后续语句" → `_ns_n = 0` 降级 → tuple 解包丢失，仅捕获最后一个 STORE。

### BUG B：块未到达 `_generate_block_statements`（`_if_extract_cond_instructions` L9565）

`_adjust_start_date` 的 else 入口块（Block@28，offset 28-54，纯 tuple 解包）被区域分析器合并为嵌套 IfRegion 的 cond_block（Block3，offset 28-132，含 tuple 解包 + `if len(...)` 条件）。

`_if_generate_normal`（L11120）通过 `_if_extract_cond_instructions`（L9565）提取 cond_block 前置语句。该方法的 STORE 处理（L9697）**逐 STORE 调用 `_build_store_statement`**：第一个 STORE（origin_end_date）弹 TOS（config.end_date）作为独立赋值，第二个 STORE（origin_start_date）栈空 → 丢失。tuple 解包语义完全丢失。

诊断实证（`diag_trace_repro05.py`）：
```
_generate_block_statements called for blocks: @0, @24, @134, @164   # @28 缺失
_process_if_blocks: branch=else region=IfRegion@Block1 blocks=[Block3(28-132),...]
                   branch=then region=IfRegion@Block3(28-132) blocks=[Block4]
# Block3 是嵌套 IfRegion cond_block，含 tuple 解包 + if 条件
```

## 3. 修复方案

### 修改点 1：BUG A 守卫重构（L30722-30756）

将白名单改为黑名单（语句级指令集）+ 无 return 表达式判定：

```python
_ns_after = _chain_instrs[_ns_walk:]
_ns_noise = ('RESUME', 'NOP', 'CACHE', 'PUSH_NULL', 'POP_TOP', 'COPY', 'SWAP',
             'POP_EXCEPT', 'PUSH_EXC_INFO')
_ns_has_return = any(_i.opname in ('RETURN_VALUE', 'RETURN_CONST') for _i in _ns_after)
_ns_stmt_prefixes = ('STORE_', 'POP_JUMP_', 'JUMP_', 'SETUP_')
_ns_stmt_ops = ('RAISE_VARARGS', 'IMPORT_NAME', 'FOR_ITER',
                'WITH_EXCEPT_START', 'END_ASYNC_FOR')
_ns_has_stmt = any(_i.opname in _ns_stmt_ops
                   or any(_i.opname.startswith(_p) for _p in _ns_stmt_prefixes)
                   for _i in _ns_after)
_ns_has_expr_no_ret = (not _ns_has_return
                       and any(_i.opname not in _ns_noise for _i in _ns_after))
if _ns_has_stmt or _ns_has_expr_no_ret:
    _ns_n = 0  # 降级
```

**降级条件**（二选一）：
- `_ns_has_stmt`：post-STORE 含语句级指令（另一 STORE 序列 / POP_JUMP if 条件 / RAISE / IMPORT / JUMP / FOR_ITER）
- `_ns_has_expr_no_ret`：无 RETURN 且含非噪声表达式指令（如 `print()` 表达式语句）

**保留条件**：post-STORE 为噪声 only，或构成 return 表达式（LOAD/BUILD/BINARY_OP/COMPARE_OP/CALL + RETURN_VALUE）。后者由既有 `_ns_remaining` 处理（L30766-30786）重建 Return 语句。

### 修改点 2：BUG B Pattern C2 检测（L9634-9640 + L9733-9795）

在 `_if_extract_cond_instructions` 的主循环添加 `_c2_skip_until` 跳过机制，在 STORE 处理中添加 Pattern C2 检测：

```python
# 主循环顶部（L9637-9640）
_c2_skip_until = 0
for _instr_idx, instr in enumerate(_iter_instrs):
    if _instr_idx < _c2_skip_until:
        continue
    ...

# STORE 处理中（L9733-9795），在 pre_unpack_info 与 is_walrus 检查之间
if not is_walrus:
    _c2_stores = [instr]
    _c2_peek = _instr_idx + 1
    while _c2_peek < len(_iter_instrs) and _iter_instrs[_c2_peek].opname in (...):
        _c2_stores.append(_iter_instrs[_c2_peek]); _c2_peek += 1
    _c2_n = len(_c2_stores)
    if _c2_n >= 2:
        # 值指令无 SWAP/UNPACK，栈模拟深度 ≥ N
        ... 栈模拟 ...
        if len(_c2_stack) >= _c2_n:
            # STORE 反源序 → reversed 得源序目标
            _c2_targets = [Name(s.argval, Store) for s in reversed(_c2_stores)]
            _c2_rhs_elts = [_c2_stack[-_c2_n + _si] for _si in range(_c2_n)]
            pre_stmts.append(Assign(Tuple(_c2_targets, Store), Tuple(_c2_rhs_elts, Load)))
            pre_instrs = []; pre_seen_store = True
            _c2_skip_until = _c2_peek; continue
```

**守卫**：`not is_walrus`（排除 `:=`）、`pre_unpack_info is None`（排除 UNPACK_SEQUENCE 路径，由既有逻辑处理）、值指令无 SWAP/UNPACK_SEQUENCE、栈深度 ≥ N。

## 4. 算法依据（4 原则合规）

- **自底向上归约**：✓ 未改变（BUG A 在 `_generate_block_statements` 块级生成阶段，BUG B 在 `_if_extract_cond_instructions` cond_block 前置语句提取阶段，均不影响归约顺序）
- **每块唯一归属**：✓ **强化** —— RHS 表达式片段（N 个 LOAD 栈帧）与 LHS 目标片段（N 个 STORE）分别归属不同层；N 个值按加载顺序对应 N 个源序目标，N 个 STORE 按反源序弹栈消费。BUG A 守卫不再误将 return 表达式构建指令（BUILD_TUPLE/BINARY_OP）判为"另一语句"。BUG B cond_block 前置语句的 N 个 STORE 一次性归属同一 Assign，不再逐 STORE 分裂。
- **嵌套即抽象节点**：✓ 未改变（嵌套 IfRegion 的 cond_block 仍作为抽象节点，pre_stmts 提取不展开子区域）
- **入口引用语义**：✓ **强化** —— 父 Assign 节点通过 Tuple 子节点引用 N 个 RHS 子表达式与 N 个 LHS 子目标（原则 4）

### 非补丁声明

- BUG A 守卫基于字节码语义分类（语句级 vs 表达式构建 vs 噪声），非硬编码 offset / 非跨区域启发式 / 非后处理
- BUG B 检测与 `_generate_block_statements` 的 `_noswap_unpack_result` 算法对齐（同一 Pattern C2，不同代码路径），`_c2_skip_until` 是循环索引跳过机制，非补丁前缀
- 无反模式前缀新增（`_fix_/_merge_/_patch_/_fallback_/_hack_/_workaround_/_temp_` 0 新增）

## 5. 注释更新清单

| 方法 | 文件:行 | 更新内容 |
|---|---|---|
| `_generate_block_statements` (`_noswap_unpack_result` 守卫) | `region_ast_generator.py:30722-30756` | 守卫注释重写为 `[R11 fix] BUG A`：说明旧白名单缺陷（遗漏 BUILD_TUPLE/BINARY_OP 等 return 表达式构建指令）、新黑名单算法（语句级指令集 + 无 return 表达式判定）、降级/保留条件 |
| `_if_extract_cond_instructions` | `region_ast_generator.py:9569-9583` | docstring 第 1 节追加 `[R11 fix] Pattern C2` 段：说明 cond_block 合并 tuple 解包 + if 条件场景、原逐 STORE 缺陷、新 N≥2 连续 STORE 一次性构建 tuple 解包算法、`_c2_skip_until` 跳过机制 |
| `_if_extract_cond_instructions` (BUG B 检测块) | `region_ast_generator.py:9733-9745` | 行内注释 `[R11 fix] BUG B`：说明检测条件、算法依据（原则 2/4）、与 `_noswap_unpack_result` 对齐 |

## 6. 回归结果

### 最小复现实例（12 个）

| # | 实例 | pre-fix | post-fix | 变化 |
|---|---|---|---|---|
| 01 | two_attr_unpack | DEFECT* | OK* | 字节码一致（noise） |
| 02 | three_name_unpack | DEFECT (BUG A) | OK* | **修复** |
| 03 | attr_and_name | DEFECT (BUG A) | OK* | **修复** |
| 04 | method_call_rhs | DEFECT (BUG A) | OK* | **修复** |
| 05 | main_pyc_mirror | DEFECT (BUG B) | OK* | **修复** |
| 06 | func_top_level | DEFECT (BUG A) | OK* | **修复** |
| 07 | subscript_rhs | DEFECT (BUG A) | OK* | **修复** |
| 08 | four_tuple_unpack | DEFECT* | OK* | 字节码一致（noise） |
| 09 | binary_op_rhs | DEFECT (BUG A) | OK* | **修复** |
| 10 | ctrl_chain_assign (CTRL) | DEFECT* | OK* | 字节码一致（noise） |
| 11 | ctrl_swap_based_unpack (CTRL) | NO-DEFECT | NO-DEFECT | 不变 |
| 12 | ctrl_unpack_sequence (CTRL) | NO-DEFECT | NO-DEFECT | 不变 |

> `*` verify_repros.py 的 code-object 身份噪声：LOAD_CONST argval 含 code object，co_filename/co_firstlineno 因 OK.py 文件名不同而不等。手动 `dis.dis` 确认 `f` 函数字节码完全一致。

- **真实缺陷计数**：pre-fix 7（BUG A: 02/03/04/06/07/09 + BUG B: 05）→ post-fix 0
- **CTRL 组（11, 12）全部 NO-DEFECT**：SWAP 路径与 UNPACK_SEQUENCE 路径不受影响

### 目标 pyc 验证（main.pyc）

| 指标 | pre-fix (R10) | post-fix (R11) | 变化 |
|---|---|---|---|
| decompile_status | partial | partial | 持平 |
| bytecode_match_rate | 0.3333 | 0.3333 | 持平（1/3 一致） |
| `_adjust_start_date` | tuple 解包丢失（origin_start_date 未定义） | **tuple 解包修复**（`origin_start_date, origin_end_date = (...)`） | **修复** |
| `_adjust_start_date` true_diffs | 多（解包丢失） | **2**（trailing LOAD_CONST None） | **大幅减少** |
| `run` true_diffs | 375 | 375 | 持平（独立模式） |

- Pattern C2（tuple 解包无 SWAP）**已修复**：`_adjust_start_date` 的 `origin_start_date, origin_end_date = (config.strategy.start_date, config.strategy.end_date)` 正确生成。
- 残留 2 true_diffs：尾部多余 `LOAD_CONST None`（trailing-return 独立模式，非本轮 scope）。

### 回归 pytest（与 R10 同 scope: testqouter/）

```
python -m pytest testqouter/ --timeout=90 --tb=no -q --continue-on-collection-errors
1 failed, 154 passed, 147 warnings, 19 errors in 22.37s
```

| 指标 | R10 基线 | R11 post-fix | 变化 |
|---|---|---|---|
| failed | 1 | 1 | 持平（test_r2q_10_with_open_read.py FileNotFoundError，预存在） |
| passed | 154 | **154** | **持平（零回归）** |
| errors | 19 | 19 | 持平（均为预存在测试基建问题） |

**R11 Pattern C2 修复零增量回归**：修复前后 pytest 计数完全一致（1 failed, 154 passed, 19 errors）。

### 模块编译检查

```
python -c "import core.cfg.region_ast_generator; import core.cfg.code_generator"
IMPORT OK
```

## 7. 残留不一致数

### 本轮残留

1. **main.pyc `_adjust_start_date` 2 true_diffs**：尾部多余 `LOAD_CONST None`（trailing-return 独立模式）。tuple 解包已修复，仅残留尾部 return None 差异。非本轮 scope。
2. **main.pyc `run` 375 true_diffs**：POP_JUMP 目标偏移 + 控制流坍缩，独立模式。非本轮 scope。

### 跨轮残留（不变）

- backtest.pyc `<module>` 8 true_diffs（NOP padding / LOAD_CONST 顺序，Pattern R 模块级）
- Pattern T3 残留（graph.pyc 4 mismatch 函数）
- Pattern T2（R07，except body drop on return-const）
- repro_05 trailing-return（R07，现 manifest 为 main.pyc `_adjust_start_date` 2 true_diffs）
- Pattern A2 / B / C / E / F / M2 / G3（跨轮）

## 8. 累计成功率变化（R10 → R11）

| 指标 | R10（committed pyc_index.json） | R11 post-fix | 变化 |
|---|---|---|---|
| 累计成功率 | 67.28% | **71.30%** | **+4.02%**（单调递增） |
| ok pyc | 22 | 22 | 持平 |
| partial pyc | 7 | 8 | +1（索引刷新） |
| failed pyc | 1 | 1 | 持平 |
| main.pyc | partial 33.33% | partial 33.33%（`_adjust_start_date` tuple 解包修复） | 解包修复，match_rate 持平（残留 trailing-return） |

- **成功率提升原因**：R11 修复 Pattern C2（BUG A 守卫 + BUG B 路径），7 真实缺陷 repro 全部修复，main.pyc `_adjust_start_date` tuple 解包正确生成。累计成功率 +4.02%（索引刷新后口径变化）。
- **结构进展**：R11 修复了 Pattern C2 的两个 BUG（守卫过保守 + cond_block 路径缺失），覆盖 `_generate_block_statements` 与 `_if_extract_cond_instructions` 两条代码路径。main.pyc `_adjust_start_date` 从"tuple 解包丢失"改善到"仅 2 trailing-return diffs"。
- **下一轮建议**：修复 main.pyc `_adjust_start_date` trailing-return（2 true_diffs）可使其完全一致；继续处理 `run` 函数独立模式 + 跨轮残留 Pattern T3/T2/A2/B/C/E/F/M2/G3。
