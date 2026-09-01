# R18 反编译验证报告 — IQCommon/strategy/strategy.pyc

## 1. 目标 pyc 信息

| 字段 | 值 |
|---|---|
| pyc 路径 | `F:/Downloads/pythoncdc-main/site-packages/IQCommon/strategy/strategy.pyc` |
| 文件大小 | 4975 字节 |
| 函数数 | 2（含 `<module>` / `trade_strategy_add`） |
| Python 版本 | 3.11 |
| 验证轮次 | R18 (rcm-r18) |
| 反编译产物 | `F:/Downloads/pythoncdc-main/site-packages/IQCommon/strategy/strategyOK.py` (3799 chars) |
| 上轮状态 | pending（未验证，按轮询规则本轮选取） |
| 本轮 R18 match_rate | **0.00%** (0/2) — failed（KW_NAMES 修复降低 diff，但 if-drop 新发现残留致 0/2） |

## 2. 反编译 + 字节码 diff 结果

本轮目标：按轮询规则选取下一个 `decompile_status != ok` 的 pyc。从 `pyc_index.json` 按路径字母序轮询，首个 pending 条目为 `IQCommon/strategy/strategy.pyc`（pending, function_count=2, last_tested_round=0, size=4975）。

执行命令：

```bash
python scripts/pyc_batch_verify.py single "F:/Downloads/pythoncdc-main/site-packages/IQCommon/strategy/strategy.pyc"
```

完整输出（R18 KW_NAMES 修复后）：

```
[SINGLE] F:\Downloads\pythoncdc-main\site-packages\IQCommon\strategy\strategy.pyc
  OK.py: F:\Downloads\pythoncdc-main\site-packages\IQCommon\strategy\strategyOK.py
  source: 3799 chars

字节码 diff 报告:
  decompile_status:   failed
  total_functions:   2
  matched_functions: 0
  match_rate:        0.00%
  missing_in_decomp: []
  extra_in_decomp:   []
  mismatches (2):
    - <module>: orig=85 decomp=76 jump_diffs=0 true_diffs=39
      first_diff: {'index': 46, 'orig_op': 'LOAD_CONST', 'decomp_op': 'LOAD_CONST', ...}
    - trade_strategy_add: orig=315 decomp=313 jump_diffs=0 true_diffs=61
      first_diff: {'index': 250, 'orig_op': 'LOAD_FAST', 'decomp_arg': 'strategy_hub_name', ...}
```

**结论**：该 pyc 反编译后 0/2 函数字节码一致。R18 修复了 KW_NAMES 关键字参数丢失缺陷（trade_strategy_add 的 `with open(path, 'r', encoding='utf-8')` encoding= 保留），true_diffs 从诊断阶段 189 降至 61。但残留 61 diffs 来自**新发现的 if-drop 缺陷**（`if strategy_lv2_name is not None:` 守卫被 WithRegion cleanup 误消费），trade_strategy_add 仍 mismatched。

## 3. 当前 pyc 成功率

| 指标 | 修复前（pending / 诊断阶段） | R18 修复后 | 变化 |
|---|---|---|---|
| 总函数数 | 2 | 2 | — |
| 一致函数数 | 0 | **0** | — |
| 当前 pyc 成功率 | 0.00%（pending） | **0.00%** | — |
| decompile_status | pending | **failed** | 降级（首次验证） |
| trade_strategy_add true_diffs | 189 | **61** | -128（KW_NAMES 修复贡献） |

**结论**：KW_NAMES 修复显著降低 diff（189→61，-67%），但 if-drop 新发现缺陷致 0/2。该 pyc 状态 failed。

## 4. 不一致函数清单（2 个）

### 4.1 `<module>` — 39 true_diffs（Pattern R2 不可修复残留）

**根因**：原始 `from fly.common.enums import common, enums` 编译为异常字节码 `IMPORT_FROM common; SWAP 2; POP_TOP`（丢弃 common）+ `IMPORT_FROM enums; STORE_NAME enums`（CPython 字节码优化器 artifact）。Python 3.11.7 对任意 `from X import a, b` 均生成 `STORE_NAME a; STORE_NAME b`，无源码能复现 SWAP+POP 模式。反编译器丢弃整个 import（产物中 `enums.BUSINESS_MODE_2` 无 import 绑定）。即使修复为生成 import，重编字节码为 `STORE_NAME common` ≠ 原始 `SWAP+POP`，`<module>` 无法匹配。compare_bytecode 严格比较（仅归一化 code-object 地址 + .py 路径，不归一化 opcode）。

**不可修复**：Pattern R2（字节码优化器 artifact，不可从源码复现）。

### 4.2 `trade_strategy_add` — 61 true_diffs（KW_NAMES 已修复 + if-drop 新发现残留）

**R18 修复（Defect 2 — KW_NAMES）**：`with open(strategy_template_path, 'r', encoding='utf-8') as strategy_template:` 的 `encoding=` 关键字（KW_NAMES ('encoding',)）被 with-statement 上下文管理器调用重建丢弃。根因：`region_analyzer.py:8694` 的 ctx_expr 白名单遗漏 KW_NAMES，导致 KW_NAMES 指令在收集 with 上下文表达式时被丢弃，下游 `ExpressionReconstructor.reconstruct` 把 'utf-8' 当位置参数。R18 修复：白名单加入 'KW_NAMES'。修复后 encoding= 正确保留，贡献 -128 diffs。

**新发现残留（Defect 3 — if-drop）**：`if strategy_lv2_name is not None: strategy_hub_name = strategy_hub_name + '_' + strategy_lv2_name` 的 `if` 守卫（LOAD_FAST + POP_JUMP_FORWARD_IF_NONE）被 WithRegion cleanup 误消费，仅保留 body（赋值）。根因：WithRegion 的 cleanup_blocks / generated_blocks 误包含 with 语句之后的块（if 条件块 / return None 块）。最小复现：`with open(p,'r',encoding='utf-8') as f: ...; if b is not None: x = x + '_' + b` 触发 if-drop；`with open(p,'r',encoding='utf-8') as f: ...; return None` 触发 return-drop。该缺陷为 R19 修复目标。

## 5. 累计成功率（跨所有已验证 pyc）

| 指标 | R17 累计（基线 commit 68b7080） | R18 累计 |
|---|---|---|
| verified_pyc | 35 | **36** |
| ok_pyc | 24 | 24 |
| partial_pyc | 10 | 10 |
| failed_pyc | 1 | **2** |
| total_functions | 456 | **458** |
| matched_functions | 306 | **306** |
| cumulative_match_rate | 67.11% | **66.81%** |

### 与上一轮对比

- **R17 → R18 累计 match_rate**：67.11% → 66.81%（-0.30 pp，下降）。
- **下降原因**：strategy.pyc 首次验证 0/2（<module> Pattern R2 不可修复 + trade_strategy_add if-drop 新发现），累计 +0 matched functions、+2 total_functions、+1 failed_pyc、+1 verified_pyc。
- **与预测对比**：诊断阶段预测 1/2=50%（partial，307/458=67.03%），实际 0/2=0%（failed，306/458=66.81%）。预测偏差来自诊断阶段未发现 if-drop 缺陷（KW_NAMES 修复后 if-drop 才暴露，189 diffs 中 128 为 KW_NAMES 贡献、61 为 if-drop 贡献）。
- **非回归**：下降来自新验证 pyc 的 0/2，非既有 pyc 退化。R17 repros 10/10 NO-DEFECT 不变。

## 6. 复现实例清单

验证脚本：`minimal_repros/verify_repros.py`（从 R17 复制，函数级字节码 diff，含 code-object 身份噪声归一化）。

11 个复现实例（8 DEFECT-REPRO for with-keyword-drop pattern + 3 CTRL），R18 修复后全部 NO-DEFECT：

| # | 实例文件 | 模式 | 结果 | 说明 |
|---|---|---|---|---|
| 01 | repro_01_with_open_encoding | with open(path,'r',encoding='utf-8') as f | NO-DEFECT ✓ | KW_NAMES ('encoding',) 保留 |
| 02 | repro_02_with_open_encoding_write | with open(path,'w',encoding='gbk') as f | NO-DEFECT ✓ | KW_NAMES write 模式变体 |
| 03 | repro_03_with_open_two_kwargs | with open(path,'r',encoding=,newline=) as f | NO-DEFECT ✓ | 2 keywords (encoding, newline) |
| 04 | repro_04_with_open_errors_encoding | with open(path,'r',errors=,encoding=) as f | NO-DEFECT ✓ | 2 keywords (errors, encoding) |
| 05 | repro_05_with_call_single_kwarg | with Ctx(path, mode='r') as f | NO-DEFECT ✓ | 自定义 ctx 单 keyword |
| 06 | repro_06_with_call_two_kwargs | with Ctx(path, mode='r', timeout=10) as f | NO-DEFECT ✓ | 自定义 ctx 2 keywords |
| 07 | repro_07_with_open_encoding_no_as | with open(path,'r',encoding='utf-8') (no as) | NO-DEFECT ✓ | 无 as 绑定 POP_TOP 变体 |
| 08 | repro_08_with_open_encoding_after_if_else | if/else-return + with open(encoding=) | NO-DEFECT ✓ | with 前置 if-else-return |
| 09 | repro_09_ctrl_with_no_kwargs | with open(path,'r') as f (CTRL) | NO-DEFECT ✓ | 无 keyword 控制 |
| 10 | repro_10_ctrl_with_simple_ctx | with Ctx() as f (CTRL) | NO-DEFECT ✓ | 裸 ctx 无 call 控制 |
| 11 | repro_11_ctrl_call_kwarg_no_with | f(content, key=k, iv=v) 非 with (CTRL) | NO-DEFECT ✓ | 非 with CALL 路径控制 |

```
Found 11 repros
  repro_01_with_open_encoding.py                               NO-DEFECT      2/2 matched
  repro_02_with_open_encoding_write.py                         NO-DEFECT      2/2 matched
  repro_03_with_open_two_kwargs.py                             NO-DEFECT      2/2 matched
  repro_04_with_open_errors_encoding.py                        NO-DEFECT      2/2 matched
  repro_05_with_call_single_kwarg.py                           NO-DEFECT      3/3 matched
  repro_06_with_call_two_kwargs.py                             NO-DEFECT      3/3 matched
  repro_07_with_open_encoding_no_as.py                         NO-DEFECT      2/2 matched
  repro_08_with_open_encoding_after_if_else.py                 NO-DEFECT      2/2 matched
  repro_09_ctrl_with_no_kwargs.py                              NO-DEFECT      2/2 matched
  repro_10_ctrl_with_simple_ctx.py                             NO-DEFECT      3/3 matched
  repro_11_ctrl_call_kwarg_no_with.py                          NO-DEFECT      2/2 matched

Summary: 0 DEFECT-REPRO, 11 NO-DEFECT, 0 ERROR
```

**11/11 NO-DEFECT**。8 DEFECT-REPRO（with-keyword-drop 模式）经 R18 修复后全部 NO-DEFECT，3 CTRL 确认非 with CALL 路径不受影响。

**注**：repro_02/07/10 初版使用 `return None` 后置，触发 WithRegion cleanup 误消费 return 块（Defect 3 if-drop 同类），改为变量 return（`return len(s)` / `return path` / `return f`）以隔离 KW_NAMES 修复验证。Defect 3 的最小复现保留在诊断文件（R19 修复目标）。

## 7. 缺陷根因分析

### 7.1 Defect 2 — KW_NAMES 关键字参数丢失（R18 已修复）

**函数**: `trade_strategy_add`（strategy.pyc）

**原始字节码**（offset 570-606）:
```
570 LOAD_GLOBAL 21 (NULL + open)
582 LOAD_FAST 10 (strategy_template_path)
584 LOAD_CONST 11 ('r')
586 LOAD_CONST 12 ('utf-8')
588 KW_NAMES 13                      <- ('encoding',)
590 PRECALL 3
594 CALL 3
604 BEFORE_WITH
606 STORE_FAST 11 (strategy_template)
```

**修复前产物字节码**（KW_NAMES 丢失）:
```
570 LOAD_GLOBAL 21 (NULL + open)
582 LOAD_FAST 10 (strategy_template_path)
584 LOAD_CONST 11 ('r')
586 LOAD_CONST 12 ('utf-8')
588 PRECALL 3                        <- KW_NAMES 丢失
592 CALL 3
602 BEFORE_WITH
```

**根因**: `region_analyzer.py:8694` 的 `_extract_with_items` ctx_expr 白名单包含 LOAD_NAME/LOAD_GLOBAL/LOAD_ATTR/LOAD_FAST/LOAD_CONST/LOAD_METHOD/CALL/PRECALL/PUSH_NULL/SWAP/COPY/BINARY_SUBSCR/BINARY_OP/BUILD_*/UNPACK_SEQUENCE/IS_OP/CONTAINS_OP，但**遗漏 KW_NAMES**。KW_NAMES 不在 NOISE_OPS（不被跳过），但也不在白名单（不被收集），故静默丢弃。下游 `region_ast_generator.py:_generate_with` 的 `expr_reconstructor.reconstruct(expr_instrs)` 收到不含 KW_NAMES 的指令列表，`ast_generator_v2.py:_process_instruction` 的 KW_NAMES handler（L1112-1127）+ CALL handler（L1180-1195）无法拆分关键字参数，'utf-8' 被当位置参数。

**对照**: 非 with 上下文的 CALL（如 `aes_encrypt(content, aes_key=, aes_iv=, return_str=)`）走 `_build_statements_from_instructions` 路径，KW_NAMES 正常传入 reconstruct，关键字正确拆分。仅 with 上下文调用受影响。

**修复**: `region_analyzer.py:8694` 白名单加入 `'KW_NAMES'`（+[R18 fix] 注释）。`region_ast_generator.py:_generate_with` docstring 加 [R18 fix] 段落。

### 7.2 Defect 3 — if-drop / return-drop（新发现，R19 修复目标）

**函数**: `trade_strategy_add`（strategy.pyc）

**原始字节码**（offset 1338-1358）:
```
89  >> 1338 LOAD_FAST 3 (strategy_lv2_name)        <- if 条件
       1340 POP_JUMP_FORWARD_IF_NONE 8 (to 1358)   <- if 守卫
90      1342 LOAD_FAST 20 (strategy_hub_name)      <- body 开始
       ...
       1356 STORE_FAST 20 (strategy_hub_name)      <- body 结束
92  >> 1358 LOAD_FAST 4 (strategy_id)              <- if 之后
```

**修复后产物字节码**（if 守卫丢失）:
```
56  >> 1338 LOAD_FAST 20 (strategy_hub_name)       <- if 条件+守卫丢失
       1340 LOAD_CONST 3 ('_')
       ...
       1352 STORE_FAST 20 (strategy_hub_name)
57      1354 LOAD_FAST 4 (strategy_id)
```

**根因**: WithRegion 的 cleanup_blocks / generated_blocks 误包含 with 语句之后的块（if 条件块 / return None 块）。with 语句的 cleanup 路径（WITH_EXCEPT_START 等）经异常传播流到后续块，但这些块不属于 with cleanup，应归函数体序列。与 R07 fix（post-body 块循环 block_to_region 归属守卫）同类，但 R07 fix 未覆盖此场景。

**最小复现**:
- `with open(p,'r',encoding='utf-8') as f: ...; if b is not None: x = x + '_' + b` → if 守卫丢失
- `with open(p,'r',encoding='utf-8') as f: ...; return None` → return None 丢失

**R19 修复方向**: WithRegion cleanup_blocks 计算（`region_analyzer.py` _extract_with_items / _identify_with_regions）增加归属守卫，排除 with 语句之后的非 cleanup 块。

### 7.3 Defect 1 — <module> Pattern R2（不可修复残留）

见 §4.1。原始 `from fly.common.enums import common, enums` 编译为 `IMPORT_FROM common; SWAP 2; POP_TOP` 优化器 artifact，无源码可复现，compare_bytecode 严格比较致 `<module>` 无法匹配。

## 8. 产物清单

| 产物 | 路径 |
|---|---|
| 本报告 | `.trae/specs/region-comment-multi-pyc-iteration/rounds/round_18/test_engineer/decompile_report.md` |
| 修复报告 | `.trae/specs/.../round_18/repair_engineer/fix_report.md` |
| 验证脚本 | `.trae/specs/.../round_18/test_engineer/minimal_repros/verify_repros.py` |
| 复现实例 01-11 | `.trae/specs/.../round_18/test_engineer/minimal_repros/repro_01_*.py` … `repro_11_*.py` |
| 反编译 OK.py | `site-packages/IQCommon/strategy/strategyOK.py` |

## 9. pyc_index.json 更新

`scripts/pyc_batch_verify.py single` 已自动回写 strategy.pyc 条目：
`decompile_status=failed` / `bytecode_match_rate=0.0` / `ok_py_generated=true`。
`last_tested_round` 手动补写为 18。

## 10. 约束遵守

- 修改 `core/cfg/region_analyzer.py`（ctx_expr 白名单 +1 项 KW_NAMES，+[R18 fix] 注释）。
- 修改 `core/cfg/region_ast_generator.py`（`_generate_with` docstring +[R18 fix] 段落，无代码逻辑变更）。
- 未修改任何 `+OK.py` 文件（strategyOK.py 由 single 命令生成，未手工编辑）。
- 未修改 pyc_index.json 超出 single 命令自动回写范围 + last_tested_round 补写。
- 11 个 repro 均 ≤15 行、自包含、无业务逻辑/领域知识。
- 算法约束（bottom-up / 唯一块归属 / nested=abstract / parent ref child entry）未违反。
- 无反模式前缀新增（`_fix_/_merge_/_patch_/_fallback_/_hack_/_workaround_/_temp_`）。
