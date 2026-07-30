# R25 修复报告 — fix_report.md

**轮次**: round_25
**修复工程师**: repair_engineer
**日期**: 2026-07-30
**目标文件**: `core/cfg/region_analyzer.py`, `core/cfg/code_generator.py`

---

## 一、修复点列表

### 缺陷2（必须修）— `build_future_fill_time` 5 个 JUMP_FORWARD 跳转目标错误

**现象**: `build_future_fill_time` 函数中 else 块尾部的 for 循环被错误提升到 if/elif/else 链同级，导致 5 个 `typet!=5` 分支的 JUMP_FORWARD 跳转目标从外层合并点偏移到 else 内的 for 循环入口，运行期因尾随语句依赖的变量未定义而 NameError。

**根因**: `_build_elif_region` 的内嵌 `_check_elif_chain` 在处理「外层 if 的 else 体以嵌套 if 开头 + 尾随语句」结构时，未能区分「干净 elif 链」（嵌套 if 两路分支均汇聚于外层 merge）与「else 内嵌套 if + 尾随语句」（嵌套 if 两路分支汇聚于外层 merge 之前，之后还有尾随语句）。强行识别为 elif 链后，尾随语句被 `_elif_struct_blocks` 过滤剔出 else_blocks 并外提为 if/elif/else 之后的兄弟语句，破坏了外层 then 分支 JUMP_FORWARD 的落点。

**修复点 1 — `core/cfg/region_analyzer.py` `_build_elif_region`（约 L12942-12978）**

在 `_check_elif_chain` 内嵌函数中，计算嵌套 if 两路分支的汇聚点 `inner_merge`，当满足以下全部条件时返回 `None`（阻止 elif 链构建）：
1. `inner_merge` 非 None（NCPD 求得，非 sink 终态场景）；
2. `merge_` 非 None（外层有合并点）；
3. `inner_merge ≠ merge_`（嵌套分支汇聚于外层合并点之前 → 有尾随语句；干净 elif 链中 `inner_merge==merge_`）；
4. 外层 else 不在循环内（循环内 break/continue 经 R24-A 修正可合法不等，不予干预）；
5. `inner_merge` 非终态块（RETURN/RAISE/RERAISE — 终态汇聚属共享退出，非尾随语句）。

返回 `None` 后，调用方用原 `else_blocks` 构建 `IF_THEN_ELSE`：嵌套 if 作为子 IfRegion、尾随语句作为 else 体内兄弟子节点，每块唯一归属。

**修复点 2 — `core/cfg/code_generator.py` `_generate_if`（约 L1200-1215）**

增加 `_r25_d2_has_non_if_trailing` 守卫：当 `orelse` 包含非 If 尾随节点时（如 `orelse=[If, For]`），不将嵌套 If 展平为 elif，而是作为 `else:` 块整体渲染。避免产生 `elif/else/else` 畸形语法，并保持外层 then 的 JUMP_FORWARD 跳过整个 else（含尾随语句）到合并点。

### 缺陷3（建议修）— `one_prod_to_dataframe` and 复合条件提取不一致

**评估结论**: **本轮不修，留到下一轮**。

**原因**:
- 缺陷3 语义等价（归一化口径 150/150），非真实控制流错误；
- 修复需改动 BoolOpRegion 分析与 elif 链条件提取逻辑，影响面广（repros 01-03 暴露了相关的逆问题：嵌套 if 被误合并为 and 复合条件），引入回归风险高；
- 任务允许：「如果缺陷3修复会引入风险或不稳定，可只修缺陷2（必须），把缺陷3留到下一轮」。

**现象记录**: 原始源码 `if i == 0 and len(v) == 8: ... elif i == 0 and len(v) == 10: ...`（统一复合条件），反编译器将首个分支拆分为嵌套 `if i == 0: if len(v) == 8:`，其余 elif 保持复合 `i == 0 and len(v) == N`，导致外层 `if i == 0:` false-target 跳到 END（远，+EXTENDED_ARG）而非下一 elif（近）。

---

## 二、docstring 更新清单

| 方法 | 文件 | 更新内容 |
|------|------|----------|
| `_identify_conditional_regions` | region_analyzer.py L11042 | 已有完整 6 项模板 docstring（算法依据/归约顺序/唯一归属判定/嵌套处理/入口引用语义/反编译流程），本轮无需改动，已确认包含 4 原则声明。 |
| `_build_elif_region` | region_analyzer.py L12402 | **新增** 6 项模板 docstring。重点在「唯一归属判定」项详述 R25-Defect2 五项判据（inner_merge/merge_/循环内/终态），「反编译流程」项关联 code_generator 的 `_r25_d2_has_non_if_trailing` 守卫。 |
| `_generate_if` | code_generator.py L1136 | **扩展** docstring（原仅 `"""生成if语句"""`）。新增「算法依据」「elif 展平规则（原则 3）」「反编译流程」三段，详述 R25-Defect2 的 `_r25_d2_has_non_if_trailing` 守卫与 elif 展平合法性条件。 |

**6 项统一模板合规性**: ①算法依据 ②归约顺序 ③唯一归属判定 ④嵌套处理 ⑤入口引用语义 ⑥反编译流程 — `_identify_conditional_regions` 与 `_build_elif_region` 均完整覆盖；`_generate_if` 作为渲染侧方法覆盖 ①③⑥（②④⑤为区域分析侧概念，在「反编译流程」段关联引用）。

---

## 三、回归结果

### 3.1 导入与编译
```
$ python -c "import core.cfg.region_analyzer; import core.cfg.region_ast_generator; print('IMPORT_OK')"
IMPORT_OK
$ python pycdc.py /workspace/quotation.pyc > /tmp/r25_decompiled.py 2>/tmp/r25_err.txt
$ python -c "compile(open('/tmp/r25_decompiled.py').read(),'<d>','exec'); print('COMPILE_OK')"
COMPILE_OK
```

### 3.2 严格口径验证（保留 NOP/EXTENDED_ARG，仅跳 CACHE）
```
exact=147/150 (98.00%) diff=3

差异函数:
  <module>: len_diff len 1082->1023 (-59)              ← 缺陷1（可豁免，PEP 626 行号追踪 NOP）
  build_future_fill_time: instr_diff len 677->677 (+0)  ← 缺陷2已修：0 JUMP_FORWARD 错误
  one_prod_to_dataframe: len_diff len 452->453 (+1)     ← 缺陷3（本轮不修）
```

**缺陷2验证（build_future_fill_time 字节码差异明细）**:
- JUMP_FORWARD 跳转目标错误: **0**（修复前 5 个，全部消除 ✓）
- 剩余 5 个差异: 全部为 `LOAD_CONST` 常量类型差异（orig=tuple `('15:15:00',...)` vs new=frozenset `{'15:15:00',...}`），源于原始源码 `x in {...}`（集合字面量）经 CPython 常量折叠为 frozenset 常量，反编译器渲染为 frozenset 而非 set 字面量。属**预存在的常量渲染问题**，与缺陷2（控制流）无关，不在本轮修复范围。

### 3.3 归一化口径验证（不退化）
```
[stats] total=150 matched=150 mismatched=0 missing=0 success_rate=100.00%
```
**150/150 (100%)** — 无退化。归一化口径下 build_future_fill_time 的 tuple/frozenset 与 one_prod_to_dataframe 的 EXTENDED_ARG 差异均被归一化消除（语义等价）。

### 3.4 既有区域测试矩阵（无退化）
```
$ python -m pytest tests/control_flow_matrix/ -q
9 failed, 318 passed, 11 skipped in 2.03s
```
**318 pass / 9 fail / 11 skip** — 与基线一致，无退化。9 个 fail 均为预存在的 `test_l3_deep.py::TestDEEP16ParallelTaskCoordinator` 等深层嵌套用例，与本轮修复无关。

### 3.5 最小复现实例（repro）验证

5 个 repro 反编译后结构验证：

| repro | 缺陷2（for-loop 提升） | 剩余 DIFF 来源 |
|-------|------------------------|----------------|
| repro_01 | **已消除** ✓ for-loop 在 else 内 | 嵌套 if 误合并为 and（缺陷3相关）+ return 拉入 else（渲染） |
| repro_02 | **已消除** ✓ for-loop 在 else 内 | 同上 |
| repro_03 | **已消除** ✓ for-loop 在 else 内 | 同上 |
| repro_04 | N/A（无 for-loop） | 缺陷3（and 提取不一致） |
| repro_05 | **已消除** ✓ for-loop 在 else 内 | return 拉入 else（渲染，独立问题） |

**缺陷2核心验证**: 5 个 repro 的 for-loop 均正确位于 else 块内（修复前被提升到 if/elif/else 同级）。repro_05 反编译输出:
```python
def f(typet, suffix):
    days = [1, 2, 3]
    out = []
    if not typet == 5:
        for d in days:
            out.append(d)
    else:
        if suffix == 'A':
            m = [1]
        else:
            m = [2]
        for d in days:          # ← 正确在 else 内（修复前被提升到同级）
            for v in m:
                out.append(d + v)
    if out:
        out.sort()
    return out
```

**repro 剩余 DIFF 说明**: repros 01-03/05 的剩余字节码差异源于两个**独立于缺陷2**的问题:
1. **嵌套 if 误合并为 and 复合条件**（repros 01-03）: 原始 `if A: if B: <then>` 被渲染为 `if A and B: <then> else: <else>`，else 绑定从外层 if 偏移到复合条件。此为缺陷3 的逆问题（BoolOpRegion 误合并），与 for-loop 提升无关。
2. **return 拉入 else**（repros 01-05）: 原始 `if cond: <then>\nreturn X` 被渲染为 `if cond: <then> else: return X`，产生额外隐式 `return None`。此为独立的 if/return 渲染问题。

以上两个问题均不影响 quotation.pyc 的 build_future_fill_time（该函数 0 JUMP_FORWARD 错误），属 repro 最小化暴露的独立问题，不在缺陷2修复范围。

---

## 四、残留不一致数

| 口径 | 不一致数 | 明细 |
|------|----------|------|
| 严格口径 | 3/150 | 缺陷1 `<module>` NOP（可豁免）+ build_future_fill_time tuple/frozenset 常量（预存在）+ 缺陷3 one_prod_to_dataframe EXTENDED_ARG（本轮不修） |
| 归一化口径 | 0/150 | 150/150 全匹配 |
| 测试矩阵 | 9 fail | 预存在深层嵌套用例，无退化 |

**缺陷2残留**: 0（JUMP_FORWARD 跳转目标错误全部消除）。

---

## 五、算法 4 原则合规性自检

| 原则 | 合规 | 说明 |
|------|------|------|
| ① 自底向上归约 | ✓ | `_build_elif_region` 在 `_identify_conditional_regions` Step 5 调用，先归约内层 elif（`_check_elif_chain` 递归），再组装 IF_ELIF_CHAIN。R25-Defect2 修复不改变归约顺序，仅在 elif 链判定时增加尾随语句守卫。 |
| ② 每块唯一归属 | ✓ | R25-Defect2 核心判据：`inner_merge ≠ merge_` 时返回 None，阻止尾随语句被 `_elif_struct_blocks` 剔出 else_blocks 外提（违反归属）。返回 None 后尾随语句作为 else 体内兄弟子节点，嵌套 if 作为子 IfRegion，每块唯一归属一个区域。 |
| ③ 嵌套即抽象节点 | ✓ | code_generator `_r25_d2_has_non_if_trailing` 守卫：orelse 含非 If 尾随节点时不展平为 elif，保持嵌套 If 作为 else 体内的抽象节点。`_build_elif_region` docstring 明确「嵌套即抽象节点」原则。 |
| ④ 入口引用语义 | ✓ | IF_ELIF_CHAIN 通过 elif_conditions / elif_bodies / elif_final_else 引用各 elif 入口块，不展开内部嵌套 IfRegion。R25-Defect2 修复不影响入口引用语义。 |

**反模式检查**:
- ✓ 未引入任何 `_fix_/_merge_/_patch_/_fallback_/_hack_/_workaround_/_temp_` 前缀的新方法；
- ✓ 未引入硬编码深度上限；
- ✓ 未引入跨区域启发式（R25-Defect2 判据基于同一 IfRegion 内 inner_merge vs merge_ 的结构关系，非跨区域）。

---

## 六、修复文件清单

| 文件 | 修改类型 | 行号（约） |
|------|----------|------------|
| `core/cfg/region_analyzer.py` | 新增 docstring + R25-Defect2 判据 | L12402-12465（docstring）, L12942-12978（判据） |
| `core/cfg/code_generator.py` | 扩展 docstring + R25-Defect2 守卫 | L1136-1164（docstring）, L1200-1215（守卫） |

**未修改**: `core/cfg/region_ast_generator.py`（R25-Defect2 修复不涉及 AST 生成逻辑，区域归约阶段已正确阻止 elif 链构建）。

---

## 七、结论

- **缺陷2（必须修）**: 已修复。quotation.pyc `build_future_fill_time` 的 5 个 JUMP_FORWARD 跳转目标错误全部消除，for-loop 正确位于 else 块内。严格口径下该函数仅剩 tuple/frozenset 常量渲染差异（预存在，非控制流）。
- **缺陷3（建议修）**: 本轮不修（风险可控评估后决定留到下一轮），归一化口径 150/150 无退化。
- **回归**: 严格口径 147/150（与基线一致，缺陷2 JUMP_FORWARD 已消除）、归一化口径 150/150、测试矩阵 318 pass/9 fail/11 skip 均无退化。
