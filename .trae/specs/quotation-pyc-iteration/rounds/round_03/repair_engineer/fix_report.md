# Round 3 修复工程师报告（fix_report.md）

> 目标文件：`/workspace/quotation.pyc`
> 修复工程师产物路径：`rounds/round_03/repair_engineer/`
> 关联文档：`rounds/round_03/test_engineer/decompile_report.md` + `rounds/round_02/repair_engineer/fix_report.md`
> 修复依据：R3 测试工程师 `decompile_report.md`（10 类缺陷，P0×2 / P1×3 / P2×5）
> 验证目标：minimal repro 路径 + quotation.pyc 实际路径

## 0. 总体结论

| 指标 | R3 基线 | R3 修复后 | 变化 |
|------|---------|-----------|------|
| 反编译产物总行数 | 2547 | 3035 | +488（含 P0/P1 修复恢复的函数体）|
| stderr 警告数 | 0 | **0** | 持平 ✓ |
| 编译验证 | COMPILE_OK | **COMPILE_OK** ✓ | 持平 |
| IMPORT_OK | ✓ | **✓** | 持平 |
| 反模式新增 | 0 | **0** | G3 持平 ✓ |
| P0 修复 | 0/2 | **2/2** ✓ | 完成 |
| P1 修复 | 0/3 | **3/3** ✓ | 完成 |
| P2 修复 | 0/5 | **2/5** ✓ | 完成 ≥2 项（T6c + T6e）|
| 既有测试矩阵退化 | — | **0 退化** ✓ | IF/LOOP/TRY/WITH/MATCH/BOOLOP 全部持平 |

### 0.1 R3 修复点清单（共 7 项：P0×2 + P1×3 + P2×2）

| # | 优先级 | repro | 缺陷 | 涉及方法 | 状态 |
|---|--------|-------|------|----------|------|
| 1 | P0 | repro_03_elif_chain_func_body_truncation | elif 链后函数体截断 | `_identify_conditional_regions` / `_build_elif_region` | ✓ 已验证 |
| 2 | P0 | repro_03_repro04_file_assignment_lost | try 块前顺序赋值被吞并 | `_extract_with_items` / `_generate_with` / `_if_generate_else_branch` | ✓ 已验证 |
| 3 | P1 | repro_03_match_case_none_to_wildcard | case None→case _ | `_extract_case_pattern` / `_convert_match_pattern` | ✓ 已验证 |
| 4 | P1 | repro_03_if_nested_inner_lost | 嵌套 if 内层丢失 | `_detect_boolop_conditional_chain` | ✓ 已验证 |
| 5 | P1 | repro_03_if_ifexp_arg_to_and_docstring | IfExp→and + docstring | `_detect_boolop_conditional_chain` | ✓ 已验证 |
| 6 | P2 | repro_03_if_elif_bare_name | elif 分支 RHS 丢失→裸 Name | `_loop_generate_for` / `_build_effective_stmts` / `_generate_block_statements` | ✓ 已验证 |
| 7 | P2 | repro_03_loop_bare_name_and_dup | 循环体裸 Name + 重复 | 同上 + `_generate_with` | ✓ 已验证 |

### 0.2 本阶段（第二阶段）新增工作

本阶段在第一阶段（P0×2 + P1×3）基础上完成：
1. **P2-T6e 修复**（repro_03_if_elif_bare_name）：elif 分支 `l = l.replace('.XSHE', '.SZ')` 的 Call 节点保留
2. **P2-T6c 修复**（repro_03_loop_bare_name_and_dup）：循环体无裸 `stock`/`panel.items` Expr，无重复 `exrights_data` 赋值
3. **WITH 退化修复**（test_w007/w008/w030/031/w099 等）：WithRegion 入口块前置赋值提取优化 + for_iter_setup 不标记 generated
4. **LOOP 回归修复**（test_for16_for_if）：for_iter_setup 被误判为 generated 导致前置赋值丢失

---

## 1. P2 修复详解

### 1.1 P2-T6e: repro_03_if_elif_bare_name（elif 分支 RHS 丢失→裸 Name）

**缺陷**：`check_stocks(l)` 函数 elif 分支首条 `l = l.replace('.XSHE', '.SZ')` 的 Call 节点 RHS 丢失，反编译产物出现裸 `l` Expr（孤立表达式）+ 重复 `l = l.replace(...)` 赋值。

**根因**：
- `for_iter_setup` 块（包含 `LOAD_FAST l + LOAD_ATTR replace + LOAD_CONST '.XSHE' + LOAD_CONST '.SZ' + CALL_METHOD + STORE_FAST l + LOAD_FAST l + GET_ITER`）被 IfRegion elif body 的 `_build_effective_stmts` 处理时：
  - `STORE_FAST l`（赋值）被正确发射为 `l = l.replace(...)` 到 stmts
  - 尾部 `LOAD_FAST l + GET_ITER`（for-iterable 序列）被重建为裸 Expr `l` 泄漏
- `_loop_generate_for` 重复发射 pre_stmts（包含 `l = l.replace(...)`），导致赋值重复

**违反的算法原则**：
- 入口引用语义：父 For 应通过 for_iter_setup 入口引用迭代器表达式，不应在 elif body 中发射裸 Expr
- 每块唯一归属：pre_stmts 发射权归首次处理者，不应重复

**修复**（`core/cfg/region_ast_generator.py`）：
1. `_build_effective_stmts`（L1775-1788）：检测尾部 expr_instrs 以 GET_ITER/GET_AITER 结尾且当前块是某 LoopRegion 的 for_iter_setup 时，不发射裸 Expr，标记 `_fis_pre_stmts_emitted`
2. `_loop_generate_for`（L3133）：pre_stmts 发射守卫从 `for_iter_setup not in self.generated_blocks` 改为 `for_iter_setup not in self._fis_pre_stmts_emitted`（精确追踪）
3. `_generate_block_statements`（L27555-27579）：尾部 stmt_instrs 仅含 for-iterable 序列（无 STORE_*）且当前块是 for_iter_setup 时，抑制裸 Expr 发射，同步标记 `_fis_pre_stmts_emitted`

**验证**：
```
$ python pycdc.py repro_03_if_elif_bare_name.pyc
def check_stocks(l):
    if isinstance(l, str):
        l = l.replace('.XSHE', '.SZ')
        l = l.replace('.XSHG', '.SS')
        check_stock(l)
    elif isinstance(l, list) or isinstance(l, tuple):
        l = l.replace('.XSHE', '.SZ')    # ← Call 节点保留，无裸 l
        for s in l:
            s = s.replace('.XSHE', '.SZ')
            s = s.replace('.XSHG', '.SS')
            check_stock(s)
    else:
        raise RuntimeError('您的输入有误')
```
✓ 裸 `l` Expr 消除，重复赋值消除

### 1.2 P2-T6c: repro_03_loop_bare_name_and_dup（循环体裸 Name + 重复）

**缺陷**：`load_get_price(stocks, fq)` 函数循环体出现裸 `stock` Expr（`panel[stock] = data` 目标丢失）+ 重复 `exrights_data = get_exrights_data(stocks)` 赋值。

**根因**：与 T6e 同源。`for_iter_setup` 块（包含 `exrights_data = get_exrights_data(...)` 赋值 + `panel.items` GET_ITER 序列）被父 IfRegion body 处理时，尾部 `panel.items + GET_ITER` 被泄漏为裸 Expr，且 `_loop_generate_for` 重复发射 pre_stmts。

**修复**：同 T6e（共享修复逻辑）。

**验证**：
```
$ python pycdc.py repro_03_loop_bare_name_and_dup.pyc
def load_get_price(stocks, fq=None):
    panel = load_bars_from_hundsun(stocks)
    if fq == 'pre':
        exrights_data = get_exrights_data(stocks)    # ← 无重复
        for stock in panel.items:
            data = change_his_to_forward(stock, panel[stock], exrights_data)
            if data is not None:
                panel[stock] = data                   # ← 无裸 stock Expr
    elif fq == 'post':
        ...
```
✓ 裸 `stock`/`panel.items` Expr 消除，重复 `exrights_data` 赋值消除
（注：elif 分支残留 spurious `else: return panel` 属 repro_03_loop_spurious_for_else_double P2 范畴，非本轮修复目标）

---

## 2. 回归修复详解

### 2.1 WITH 退化修复（test_w007/w008/w030/031/w099 等）

**问题**：P2 修复引入 WITH 测试退化（80→71，+9 fail）。WithRegion 入口块中 `STORE_NAME i + LOAD_NAME ctx + BEFORE_WITH` 序列被错误提取为前置语句，导致 `LOAD_NAME ctx` 作为裸 Expr 发射；WithRegion 批量将 for_iter_setup 加入 `generated_blocks`，导致 `_loop_generate_for` 误判前置赋值语句已发射，造成 `x = 0` 等语句丢失。

**修复**（`core/cfg/region_ast_generator.py`）：
1. 新增 `_fis_pre_stmts_emitted` 集合（L184）：专门追踪 for_iter_setup 块的前置赋值语句发射状态，避免误用 `generated_blocks`（WithRegion 会批量加入其全部 blocks）
2. `_generate_with`（L14751-14779）：检测 block 是 descendant LoopRegion 的 for_iter_setup 时不标记为 generated
3. `_generate_with`（L15588-15645）：优化 `_pre_bw_instrs` 提取逻辑，要求指令段必须以 STORE_* 结尾且首条非 STORE_* 才发射前置语句，避免误吞 WITH 上下文表达式

**验证**：WITH 80/0 ✓（恢复 R2 基线）

### 2.2 LOOP 回归修复（test_for16_for_if）

**问题**：P2 修复引入 LOOP 测试退化（79→77，+2 fail in bounded subset）。`test_for16_for_if` 中 `for_iter_setup` 块（包含 `even = []` + `odd = []` + `range(10)` GET_ITER 序列）被 `_generate_region` 批量加入 `generated_blocks`（因 for_iter_setup ∈ region.blocks），导致 `_loop_generate_for` 误判 "pre_stmts 已发射" 而跳过，使模块级赋值 `even = []` / `odd = []` 丢失。

**根因分析**（通过猴子补丁追踪确认）：
- `_loop_generate_for` 入口时 `FIS@0 in_generated_blocks=True, in_emitted=False`
- `_generate_block_statements` 从未被调用 for for_iter_setup（它在 region.blocks 中，被父生成器跳过）
- `generated_blocks` 被 `_generate_region` 批量填充（for_iter_setup ∈ region.blocks）

**修复**（`core/cfg/region_ast_generator.py` L3119-3134）：
- pre_stmts 发射守卫从 `for_iter_setup not in self.generated_blocks` 改为 `for_iter_setup not in self._fis_pre_stmts_emitted`
- `_fis_pre_stmts_emitted` 仅由真正发射了 pre_stmts 的 `_build_effective_stmts` / `_generate_block_statements` 标记，语义精确
- `_generate_block_statements`（L27572-27579）：`_gs_trailing_for_iter` 触发时同步标记 `_fis_pre_stmts_emitted`，避免重复发射

**验证**：
- `test_for16_for_if` PASS ✓
- LOOP bounded subset 79/1 ✓（恢复 R2 基线，仅 test_for20_complex_body 为 pre-existing fail）
- test_while15_nested_while / test_while16_for_in_while 仍 fail，但经 `git stash` 验证为 **pre-existing**（R2 基线即失败），且不在 bounded subset 内

---

## 3. 回归测试结果

### 3.1 既有测试矩阵（bounded subset）

执行 `python .trae/specs/analysis-fix-iteration/run_region_tests.py <region>`：

| 区域 | R2 基线 | R3 修复后 | 状态 |
|------|---------|-----------|------|
| IF | 79/1 | 79/1 | ✓ 持平 |
| LOOP | 79/1 | **79/1** | ✓ 持平（回归已修复）|
| TRY | 80/0 | 80/0 | ✓ 持平 |
| WITH | 80/0 | **80/0** | ✓ 持平（WITH 退化已修复）|
| MATCH | 79/0 | 79/0 | ✓ 持平 |
| BOOLOP | 79/0 | 79/0 | ✓ 持平 |

**结论**：IF/LOOP/TRY/WITH/MATCH/BOOLOP 全部持平，**0 退化** ✓

### 3.2 R3 repro 验证（10 个 minimal repro）

| repro | 优先级 | 核心缺陷消除 | 状态 |
|-------|--------|-------------|------|
| repro_03_elif_chain_func_body_truncation | P0 | ✓ 函数体不再截断 | ✓ |
| repro_03_repro04_file_assignment_lost | P0 | ✓ `file = ...` 赋值恢复 | ✓ |
| repro_03_match_case_none_to_wildcard | P1 | ✓ `case None` 正确输出 | ✓ |
| repro_03_if_nested_inner_lost | P1 | ✓ 嵌套 if 保留 | ✓ |
| repro_03_if_ifexp_arg_to_and_docstring | P1 | ✓ IfExp 保留为 Call 实参 | ✓ |
| repro_03_if_elif_bare_name | P2 | ✓ 无裸 `l`，无重复赋值 | ✓ |
| repro_03_loop_bare_name_and_dup | P2 | ✓ 无裸 `stock`/`panel.items`，无重复 | ✓ |
| repro_03_try_except_handler_if_cond_lost | P2 | — | 未修复（P2 择优）|
| repro_03_loop_store_subscr_to_annotation | P2 | — | 未修复（P2 择优）|
| repro_03_loop_spurious_for_else_double | P2 | — | 未修复（P2 择优）|

### 3.3 quotation.pyc 验证

- `python pycdc.py /workspace/quotation.pyc` → 3035 行，exit=0
- stderr 警告数：0 ✓
- `compile()` → COMPILE_OK ✓
- IMPORT_OK ✓

---

## 4. 反模式自检（G3）

```
$ grep -nE "^\s*def (_fix_|_merge_|_patch_|_fallback_|_hack_|_workaround_|_temp_)" \
    core/cfg/region_ast_generator.py core/cfg/region_analyzer.py \
    core/cfg/ast_converter.py core/cfg/pattern_parser.py
core/cfg/region_ast_generator.py:18880:    def _merge_block_is_loop_back_edge(self, region: TernaryRegion) -> bool:
```

- **0 新增**反模式前缀方法 ✓
- `_merge_block_is_loop_back_edge`（region_ast_generator.py L18880）为 **pre-existing**，按 spec 留待后续轮次重命名

---

## 5. docstring 更新清单

### 5.1 P2 修复涉及方法（本阶段新增 docstring）

| 方法 | 文件 | 6 项模板覆盖 | 状态 |
|------|------|-------------|------|
| `_loop_generate_for` | region_ast_generator.py L3028 | 算法依据 / 归约顺序 / 唯一归属判定 / 入口引用语义 / 反编译流程 / 已知限制 | ✓ 新增 docstring |

### 5.2 P2 修复涉及方法（已有详细内联注释）

| 方法 | 文件 | 说明 |
|------|------|------|
| `_build_effective_stmts` | region_ast_generator.py L1706 | L1765-1788 详细内联注释（R3-P2 修复依据 + 4 原则对应）|
| `_generate_block_statements` | region_ast_generator.py L25564 | L27536-27579 详细内联注释（R3-P2 修复 + LOOP 回归修复依据）|
| `_generate_with` | region_ast_generator.py | L14751-14779 / L15588-15645 详细内联注释（WITH 退化修复依据）|

### 5.3 P0/P1 修复涉及方法（第一阶段已更新）

| 方法 | 文件 | 6 项模板覆盖 | 状态 |
|------|------|-------------|------|
| `_identify_conditional_regions` | region_analyzer.py | 6 节结构（算法描述/字节码模式/边界条件/归约语义/AST映射/已知失败模式）| ✓ |
| `_extract_with_items` / `_generate_with` | region_analyzer.py / region_ast_generator.py | 内联注释覆盖 6 项 | ✓ |
| `_detect_boolop_conditional_chain` | region_analyzer.py | 内联注释覆盖 6 项 | ✓ |
| `_extract_case_pattern` | pattern_parser.py | 内联注释覆盖 6 项 | ✓ |

---

## 6. 算法 4 原则合规性自检

| 原则 | 合规性 | 证据 |
|------|--------|------|
| 自底向上归约 | ✓ FULLY COMPLIANT | P2 修复在 `_build_effective_stmts` / `_generate_block_statements`（底层块处理）抑制裸 Expr，`_loop_generate_for`（LoopRegion 生成阶段）统一提取 iter_expr；for_iter_setup 作为 LoopRegion 子节点归约 |
| 每块唯一归属 | ✓ FULLY COMPLIANT | pre_stmts 发射权归首次处理该块的语句生成器（`_fis_pre_stmts_emitted` 精确追踪），`_loop_generate_for` 仅作 fallback；for_iter_setup 不被多个生成器重复处理 |
| 嵌套即抽象节点 | ✓ FULLY COMPLIANT | for_iter_setup 作为 LoopRegion 的子节点，在父 IfRegion/WithRegion 中作为单个抽象节点引用；无展平嵌套 |
| 入口引用语义 | ✓ FULLY COMPLIANT | 父 For 通过 `_loop_extract_for_iter_pre_stmts` 提取 iter_expr，引用 for_iter_setup 入口；父 IfRegion/WithRegion 通过 `_fis_pre_stmts_emitted` 标记避免重复 |

**无跨区域启发式 / 后处理补丁 / 硬编码深度上限 / 展平嵌套** ✓

---

## 7. 残留不一致数

### 7.1 R3 修复后残留

- **P2 未修复**（3 项，按 spec 时间预算择优）：
  - repro_03_try_except_handler_if_cond_lost（except handler 内 isinstance 丢失）
  - repro_03_loop_store_subscr_to_annotation（STORE_SUBSCR→变量注解 + spurious break）
  - repro_03_loop_spurious_for_else_double（双层 spurious for-else）

- **已知限制**：
  - walrus `(x := foo()) and bar` 会误中断 boolop chain（罕见，留待后续）
  - 嵌套 if then-body 末尾 JUMP_FORWARD 由 P1-2 的 STORE_* 检测覆盖
  - repro_03_loop_bare_name_and_dup elif 分支残留 spurious `else: return panel`（属 repro_09 P2 范畴）

### 7.2 与 R3 基线对比

- quotation.pyc 字节码不一致函数数：81（R3 基线）→ 待 R4 测试工程师复测
- 截断函数：18（R3 基线）→ P0 修复后应大幅下降（9 个财务函数 + api_get 等）
- 目标降幅：≤ 50 函数不一致 / ≤ 5 截断函数（R4 测试工程师验证）

---

## 8. 涉及文件清单

| 文件 | 修改类型 | 说明 |
|------|----------|------|
| `core/cfg/region_ast_generator.py` | 修改 | P2 修复 + LOOP/WITH 回归修复 + docstring |
| `core/cfg/region_analyzer.py` | 修改 | P0/P1 修复（第一阶段）|
| `core/cfg/ast_converter.py` | 修改 | P1 修复（第一阶段）|
| `core/cfg/pattern_parser.py` | 修改 | P1 修复（第一阶段）|
| `rounds/round_03/repair_engineer/fix_report.md` | 新增 | 本报告 |
| `rounds/round_03/test_engineer/` | 新增 | 测试工程师产物（decompile_report.md + 10 repro）|

---

## 9. 验证补充检查点

- [x] R3-V1: `python -c "import core.cfg.region_analyzer; import core.cfg.region_ast_generator; import core.cfg.ast_converter; import core.cfg.pattern_parser"` 编译通过 ✓（IMPORT_OK）
- [x] R3-V2: 反模式 grep 验证 0 新增 ✓
- [x] R3-V3: quotation.pyc 反编译 stderr 维持 0 ✓
- [x] R3-V4: quotation.pyc 反编译产物 `compile()` 通过（COMPILE_OK）✓
- [x] R3-V5: P2-T6e repro_03_if_elif_bare_name 核心缺陷消除 ✓
- [x] R3-V6: P2-T6c repro_03_loop_bare_name_and_dup 核心缺陷消除 ✓
- [x] R3-V7: 既有测试矩阵 0 退化（IF/LOOP/TRY/WITH/MATCH/BOOLOP 全部持平）✓
- [x] R3-V8: LOOP 回归修复（test_for16_for_if PASS，bounded subset 79/1）✓
- [x] R3-V9: WITH 退化修复（80/0，恢复 R2 基线）✓

---

## 10. 算法合规性强制检查

1. ✓ 无 `_fix_` / `_merge_` / `_patch_` / `_fallback_` / `_hack_` / `_workaround_` / `_temp_` 前缀方法新增（`_merge_block_is_loop_back_edge` 为 pre-existing）
2. ✓ 无跨区域启发式
3. ✓ 无后处理补丁
4. ✓ 无硬编码深度上限
5. ✓ 无展平嵌套

R3 修复工程师阶段完成，移交 R4 测试工程师阶段。
