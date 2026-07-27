# R11 修复报告

## 基线
- R10 字节码一致性: 47.7% (71/149)
- R11 修复前: 48.3% (72/149) — R11-N1 已应用

## 本轮修复

### R11-N1: for 循环前驱块（for_iter_setup）前置语句丢失
**文件**: `core/cfg/region_ast_generator.py` (L3075)

**缺陷**: `generate()` 在入口块是 LoopRegion 的 for_iter_setup 时（L297），会预先将 entry_block 标记为已生成以防止顺序块扫描重复处理。但这导致 `_loop_generate_for` 中 L3075 的 guard `for_iter_setup not in self.generated_blocks` 为 False，错误跳过 pre_stmts 输出（如 `dict_to_dataframe` 的 `df = {}` 即 `BUILD_MAP+STORE_FAST` 被提取但未输出）。

**修复**: 添加 `_fis_is_self_setup` 判断 — 若 for_iter_setup 是本 region 的 setup 块（entry_block 是本循环的前驱），即使已被 `generate()` 标记也必须输出 pre_stmts。

**算法依据**: 区域归约算法原则 2（每块唯一归属）— setup 块虽被 generate() 标记，但其归属仍属本 LoopRegion，pre_stmts 必须由本循环输出。

### R11-N2: 模块级 STORE_NAME 被 STORE_GLOBAL 污染
**文件**: `core/cfg/region_analyzer.py` (L1654-1715，删除)

**缺陷**: `_detect_global_declarations` 中存在基于 `LOAD_GLOBAL` 推断 global 名字的逻辑（L1654-1715）。当函数仅通过 `LOAD_GLOBAL` 读取模块变量（不存储）时，错误地在函数中生成 `global X` 声明。CPython 名称解析规则下，模块内任一函数声明 `global X` 会导致模块级 `X = ...` 编译为 `STORE_GLOBAL` 而非 `STORE_NAME`，反向污染模块级字节码。

**表现**: `quotation.pyc` 模块级 `DumploadDailyFile = DUMPLOAD_DAILY_FILE`、`SIM_PATH = base_path`、`is_utc = IS_UTC` 等 7 处赋值被错误编译为 `STORE_GLOBAL`（pyc 原为 `STORE_NAME`）。

**修复**: 删除 `LOAD_GLOBAL` 推断分支，仅保留 `STORE_GLOBAL`/`DELETE_GLOBAL` 驱动的 `global_names`。

**算法依据**: Python 语义要求 `global X` 仅当函数对 X 执行 `STORE_GLOBAL` 或 `DELETE_GLOBAL` 时才需要；仅 `LOAD_GLOBAL X`（读取模块变量）不需要 `global` 声明。字节码驱动，非启发式推断。

## 验证
- 反编译耗时: 1.46s
- 反编译源码可编译: OK
- 字节码一致性: 48.3% (72/149) — R11-N2 修复了 `<module>` 的 7 处 STORE_GLOBAL 污染，但 `<module>` 仍因嵌套函数差异失败
- 失败模式分布:
  - 34 jump_target_diff（复合条件 and/or 反编译错误，主要瓶颈）
  - 11 argval_diff:LOAD_FAST
  - 7 unknown
  - 4 const_value_diff
  - 4 load_order_diff
  - 其他 17

## 后续方向（R12+）
1. **复合条件（and/or）反编译错误**（34 个函数）: 父 IfRegion 的 `then_blocks` 错误包含子 IfRegion 的块，导致子区域体被跳过（如 `_is_same_type_date` 的 `typet == 7` 分支显示 `pass`）。需修正区域归约算法原则 4（归约后父区域的 then/else 列表引用子区域的入口，而不是子区域的所有块）。
2. **LOAD_FAST 顺序错误**（11 个函数）: 变量加载顺序差异，需分析具体模式。
