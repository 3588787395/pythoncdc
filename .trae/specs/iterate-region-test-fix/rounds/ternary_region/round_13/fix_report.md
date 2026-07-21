# Ternary Region Round 13 — 修复报告

**执行时间**: 2026-07-21
**基线 commit**: R12 完成（ternary 全量 86 failed / 335 passed / 8 skipped）
**测试发现报告**: `test_findings.md`（11 个真失败 bug）
**核心修改文件**:
- `core/cfg/region_analyzer.py`
- `core/cfg/region_ast_generator.py`

---

## 1. 修复总览

| 类别 | 修复数 | Bug ID |
|------|--------|--------|
| 本轮已修复 | 9 | R13-01, R13-02, R13-03, R13-04, R13-07, R13-08, R13-09, R13-10, R13-11 |
| 未修复（R14+ 已知限制） | 2 | R13-05, R13-06 |
| **总计** | **11** | |

修复分两阶段完成：
- 前一综合工程师完成 8 个 bug 修复（R13-02/03/04/07/08/09/10/11）
- 本修复工程师完成 R13-01（method chain LOAD_METHOD+PRECALL+CALL+LOAD_METHOD 模式识别）

---

## 2. 本轮修复详情

### 2.1 R13-01 — string method chain arg ternary（本轮修复）

- **症状**: `s.upper().split((a if c else b))` 反编译为 `s.upper(a if c else b)` — 丢失 `.split` 方法链，且把 ternary 错误地当作 `upper()` 的参数
- **根因**: `_detect_ternary_context` 中 LOAD_METHOD 检测只识别**第一个** LOAD_METHOD（upper）作为 func.attr，未处理后续的 `PRECALL + CALL + LOAD_METHOD` 链式模式。cond_block 含 `LOAD_NAME s, LOAD_METHOD upper, PRECALL, CALL 0, LOAD_METHOD split, LOAD_NAME c, POP_JUMP_...`，第一个 LOAD_METHOD (upper) 实际是 receiver chain 的一部分，第二个 LOAD_METHOD (split) 才是真正消费 ternary 的函数
- **修复位置**: `core/cfg/region_analyzer.py` `_detect_ternary_context`（L11226-11285）
- **修复方式**: 在原 LOAD_METHOD 检测逻辑构建 `_cur_func_expr = Attribute(_obj_expr, _method_name)` 之后，新增前向链式检测循环：
  - 从 `_method_idx + 1` 起向前扫描，跳过 NOISE_OPS
  - 期望模式：`PRECALL, CALL n, LOAD_METHOD method2`（method chain 推进）
  - 命中则将当前 `_cur_func_expr` 包装为 `Call(_cur_func_expr, args=[], keywords=[])`，再用新 method 作为 attr 构造 `Attribute(Call(...), method2)`
  - 循环直到不再匹配（支持任意长链 `s.a().b().c(ternary)`）
- **保守性**: 仅处理 0-arg 中间方法调用（PRECALL 紧跟 LOAD_METHOD，无 args 插入）。带 args 的中间方法调用（如 `s.method(x).split(ternary)`）会因 PRECALL 前有 LOAD_* args 而在 `if _ci.opname != 'PRECALL': break` 处中断，回退到原有行为（不引入新退化）
- **算法合规性**:
  - 「自底向上归约」: ternary 是内层抽象节点，外层 `s.upper().split(...)` 通过 cond_block method chain 归约为父 Call 表达式
  - 「父引用子入口」: 父 Call 通过 cond_block 的 `LOAD_NAME s + LOAD_METHOD upper + PRECALL + CALL 0 + LOAD_METHOD split` 引用 ternary 子节点
  - 「每块唯一归属」: cond_block 的 method chain 前缀归属 TernaryRegion 父 Call 表达式
  - 「嵌套即抽象节点」: `s.upper()` 作为 `split` 的 receiver 子节点
- **验证结果**: `test_r13_ternary_string_method_chain_arg.py` 通过；额外验证 `s.upper().strip().split((a if c else b))` 三层链也正确反编译；R13-11 `(a if c else b).method()` 与 R1 `obj.method(a if a > 0 else 0)` 无退化

### 2.2 R13-02 — del slice 双界 ternary（前阶段修复）

- **症状**: `del x[a if c else b : b if d else e]` 反编译丢失 `BUILD_SLICE 2`，slice 边界错误
- **根因**: chained ternary 的 innermost_merge 含 `BUILD_SLICE 2 + DELETE_SUBSCR`，但 Pattern D（`_build_chained_ternary_del`）的 `_has_delete_subscr` 分支不处理 BUILD_SLICE 包装的 slice
- **修复位置**: `core/cfg/region_ast_generator.py` `_build_chained_ternary_del`（L21208-21405）
- **修复方式**:
  - Pattern D 分支加 `_has_build_slice_d` 守卫：当 innermost_merge 含 BUILD_SLICE 时不走 Pattern D
  - 新增 Pattern E：定位 outer.cond_block preload 中的 `LOAD obj`，构造 `Delete(targets=[Subscript(obj, Slice(t1, t2, None), Del)])`
- **算法合规性**: 「父引用子入口」+「嵌套即抽象节点」+「自底向上归约」 — 父 Delete 通过 outer.cond preload + innermost_merge 的 BUILD_SLICE 2 + DELETE_SUBSCR 引用 chained ternary 子节点作为 Slice 的 lower/upper
- **验证结果**: `test_r13_ternary_del_slice.py` 通过

### 2.3 R13-03 — aug assign subscr + call arg ternary（前阶段修复）

- **症状**: `x[0] += f(a if c else b)` 反编译丢失 `f()` 调用，仅保留 ternary 作为 rhs
- **根因**: AugAssign 重构中 `before_store` 含 `PRECALL + CALL`（包装 ternary 的 f() 调用），但原逻辑直接把 `ternary_expr` 作为 AugAssign.value，未重建外层 Call
- **修复位置**: `core/cfg/region_ast_generator.py` AugAssign 分支（L19885-19920）
- **修复方式**: 检测 `before_store[:_aug_op_idx]` 中是否含 CALL。若有，使用 `expr_reconstructor` 以 `initial_stack = [callable, ternary_expr]`（callable 来自 `func_call_info['func']`）重建 Call 表达式作为 AugAssign.value
- **算法合规性**: 「自底向上归约」+「父引用子入口」 — ternary 是内层节点，外层 CALL 通过 reconstruct 归约为父 Call 表达式；父 Call 通过 func_call_info.func 引用 callable
- **验证结果**: `test_r13_ternary_aug_assign_subscr_call.py` 通过

### 2.4 R13-04 — 嵌套 Call 链 ternary（前阶段修复）

- **症状**: `f(g(h(a if c else b)))` 反编译为 `f(ternary)` — 中间 g()/h() 调用链丢失
- **根因**: ternary 在三层嵌套 Call 最内层，merge_block 含 3 个 `PRECALL + CALL 1` 消费链，但原逻辑未保留外层 g()/h() 的消费链
- **修复位置**: `core/cfg/region_ast_generator.py` 新增 `_try_build_ternary_merge_consumer_expr`（L20388+）
- **修复方式**: 检测 merge_block 含多个 CALL（`_has_call_chain = _call_count > 1`），使用 `expr_reconstructor.reconstruct(merge_all, initial_stack=preload_exprs + [ternary_expr])` 重建完整嵌套 Call 表达式
- **算法合规性**: 「自底向上归约」+「父引用子入口」+「每块唯一归属」 — ternary 是内层抽象节点，外层 BUILD_*/CALL/MAKE_FUNCTION 通过 reconstruct 归约为单一表达式节点；父容器/Call 通过 merge_block 的 PRECALL+CALL 引用 ternary 子节点
- **验证结果**: `test_r13_ternary_chained_call.py` 通过

### 2.5 R13-07 — del 多目标 subscript ternary（前阶段修复）

- **症状**: `del obj.attr, lst[a if c else b]` 反编译丢失第一个目标 `obj.attr`
- **根因**: 多目标 del 场景，cond_block preload 含 `LOAD obj + DELETE_ATTR attr`（第一个目标），但原 ternary 识别未保留前置目标
- **修复位置**: `core/cfg/region_ast_generator.py` 新增 `_build_multi_target_del_targets`（L20172+）
- **修复方式**: 检测 cond preload 含 DELETE_* 时，前向遍历 preload，在每个 DELETE_ATTR/DELETE_SUBSCR/DELETE_NAME 处构造对应 Del target 并弹出栈项；最后剩余栈顶作为当前 ternary subscript 的 obj
- **算法合规性**: 「每块唯一归属」+「父引用子入口」 — 每个 DELETE_* 独占一个 target slot；当前 ternary 的 DELETE_SUBSCR 独占最后一个 target slot
- **验证结果**: `test_r13_ternary_del_multi_target.py` 通过

### 2.6 R13-08 — list literal 中间元素 ternary（前阶段修复）

- **症状**: `[1, (a if c else b), 2]` 反编译为 `[ternary]` — 丢失前后 LOAD_CONST 元素，BUILD_LIST arity 3 被误识别为 1
- **根因**: BUILD_LIST 3 消费 3 个栈项（LOAD_CONST 1, ternary, LOAD_CONST 2），但原识别未保留前后元素
- **修复位置**: `core/cfg/region_ast_generator.py` `_try_build_ternary_merge_consumer_expr`（L20388+）
- **修复方式**: `_has_multi_elem = _build_instr is not None and (_build_arity > 1 or bool(preload_exprs))`，触发 `reconstruct(merge_all, initial_stack=preload_exprs + [ternary_expr])` 重建完整 List 表达式
- **算法合规性**: 同 2.4
- **验证结果**: `test_r13_ternary_list_middle_elem.py` 通过

### 2.7 R13-09 — Call 中间参数 ternary + 兄弟 Call（前阶段修复）

- **症状**: `f(g(0), (a if c else b), h(1))` 反编译为 `f(ternary, 1)` — 丢失 g(0) 与 h(1) 子 Call
- **根因**: cond preload 含 `LOAD_NAME f + LOAD_NAME g + LOAD_CONST 0 + PRECALL + CALL 1`（多个兄弟表达式），但原 `_compute_ternary_cond_preload_exprs` 的 compound fallback 只返回栈顶表达式（g(0)），丢失 f
- **修复位置**: `core/cfg/region_ast_generator.py` 新增 `_split_preload_into_siblings` + `_stack_effect`（L19207+）
- **修复方式**: 当 preload 含 compound 指令时，按栈深度反向切分为多个 sibling sub-slice，每个 sub-slice 独立 reconstruct。算法：从 preload 末尾反向走，跟踪 `needed` 栈深度，slice 起点是 `needed` 首次降到 0 的位置
- **算法合规性**: 「每块唯一归属」 — 每个 sibling 独占一个外层 Call 参数 slot，独立 reconstruct
- **验证结果**: `test_r13_ternary_call_with_args_before_and_after.py` 通过

### 2.8 R13-10 — dict literal 中间 value ternary（前阶段修复）

- **症状**: `{1: x, 2: (a if c else b), 3: y}` 反编译为多条独立语句，dict 结构完全破坏
- **根因**: BUILD_CONST_KEY_MAP 3 消费 3 个 value 栈项 + 1 个 keys tuple，但原识别未保留前后 LOAD x/LOAD y 元素
- **修复位置**: `core/cfg/region_ast_generator.py` `_try_build_ternary_merge_consumer_expr`（L20388+）
- **修复方式**: 同 2.6，`_has_multi_elem` 触发 reconstruct，将 BUILD_CONST_KEY_MAP 与 preload + ternary + merge 后续元素一起重建为 Dict 表达式
- **算法合规性**: 同 2.4
- **验证结果**: `test_r13_ternary_dict_middle_value.py` 通过

### 2.9 R13-11 — receiver method call ternary（前阶段修复）

- **症状**: `(a if c else b).method()` 反编译结构完全错误
- **根因**: ternary 作为 method call 的 receiver，LOAD_METHOD 指令消费 ternary 栈顶作为 receiver，但原识别未保留 LOAD_METHOD + PRECALL + CALL 消费链
- **修复位置**: `core/cfg/region_ast_generator.py` `_try_build_ternary_merge_consumer_expr`（L20388+）
- **修复方式**: `_has_receiver_method = (not region.func_call_info and any(i.opname == 'LOAD_METHOD' for i in merge_all))`，触发 reconstruct 重建 `Call(Attribute(ternary, method), args=[])`
- **算法合规性**: 同 2.4
- **验证结果**: `test_r13_ternary_receiver_method_call.py` 通过

---

## 3. R14+ 已知限制（2 个未修复）

### 3.1 R13-05 — lambda default arg ternary

- **源码**: `lambda x=(a if c else b): x`
- **当前反编译**: `(lambda *args, **kwargs: None)` — 占位符 lambda，丢失 ternary 与默认值
- **根因**: merge_block 含 `BUILD_TUPLE 1 + LOAD_CONST (code) + MAKE_FUNCTION 1`。`_try_build_ternary_merge_consumer_expr` 的 `_has_make_function` 触发了 reconstruct，但 `expr_reconstructor` 不理解 MAKE_FUNCTION 的语义（需要从 code object 的 co_varnames 重建 lambda 签名，将 ternary 作为 default value，再生成 lambda body）
- **修复方向**: 在 `_try_build_ternary_merge_consumer_expr` 中新增 MAKE_FUNCTION 专用分支：
  1. 从 LOAD_CONST 提取 code object
  2. 从 code object 的 co_varnames + co_flags 推断参数列表
  3. BUILD_TUPLE 1 的栈顶（ternary）作为最后一个位置参数的 default
  4. 生成 `Lambda(args=..., body=...)` AST 节点，body 由 code object 反编译递归生成
- **复杂度**: 中-高（需递归反编译 code object 作 lambda body，且需正确处理默认参数位置）
- **优先级**: P2

### 3.2 R13-06 — nested lambda body ternary

- **源码**: `lambda: lambda: (a if c else b)`
- **当前反编译**: `(lambda *args, **kwargs: None)` — 占位符 lambda
- **根因**: ternary 在**内层 lambda 的 code object** 中（不在外层 code object）。外层 code object 仅含 `LOAD_CONST (outer lambda code) + MAKE_FUNCTION 0`。RegionAnalyzer 不递归进入嵌套 code object 寻找 ternary
- **修复方向**: 
  1. 在 `_build_function_def` / lambda 处理路径中，递归进入嵌套 code object 的 CFG
  2. 在内层 CFG 中识别 ternary region
  3. 生成嵌套 lambda body 包含 ternary
- **复杂度**: 高（涉及跨 code object 递归 + 嵌套 lambda 上下文映射）
- **优先级**: P3

---

## 4. 最终测试结果

### 4.1 ternary 全量测试

```
$ cd /workspace && timeout 250 python -m pytest tests/exhaustive/ternary/ --tb=no -q
88 failed, 365 passed, 8 skipped in 3.65s
```

- **基线**（R12 完成）：86 failed / 335 passed / 8 skipped
- **R13 测试加入后（未修复）**：97 failed / 356 passed / 8 skipped（+11 R13 新 bug）
- **本轮 R13 修复后**：88 failed / 365 passed / 8 skipped
- **变化**: 失败数 -9（11 个 R13 bug 中 9 个修复），通过数 +9（无退化）

### 4.2 R13 子集测试

```
$ cd /workspace && python -m pytest tests/exhaustive/ternary/test_r13_ternary_*.py --tb=no -q
2 failed, 30 passed in 1.58s
```

- 9 个原 FAIL 测试全部转为 PASS（R13-01/02/03/04/07/08/09/10/11）
- 2 个仍 FAIL（R13-05 lambda_default, R13-06 nested_lambda — 已知限制）
- 21 个原 PASS 测试保持 PASS（共 32 个 R13 测试文件）

### 4.3 跨区域回归（ternary + if_region）

```
$ cd /workspace && timeout 250 python -m pytest tests/exhaustive/ternary/ tests/exhaustive/if_region/ --tb=no -q
131 failed, 1140 passed, 17 skipped, 1 warning in 11.19s
```

分项验证：

| 区域 | 测试结果 | 与基线对比 |
|------|----------|------------|
| ternary | 88 failed / 365 passed / 8 skipped | -9 failed（R13 修复），+9 passed，无退化 |
| if_region | 43 failed / 775 passed / 9 skipped | 与 R12 基线一致（pre-existing 失败均与 ternary 无关，涉及 nested code object / walrus / generator 等） |
| **合计** | **131 failed / 1140 passed / 17 skipped** | **无任何基线退化** |

---

## 5. 算法 4 原则合规性

### 5.1 区域归约 4 原则符合性

| 原则 | 本轮修复符合性 |
|------|----------------|
| 1. 自底向上归约（最内层先识别） | ✅ 所有修复均在 TernaryRegion 已归约后由父表达式（Call/Subscript/Delete/AugAssign/List/Dict）消费 ternary 子节点。R13-01 的 method chain 通过 cond_block 的 LOAD_METHOD+PRECALL+CALL 序列识别父 Call；R13-04/09/11 的 Call 链/receiver 通过 merge_block 的 PRECALL+CALL 序列识别父 Call |
| 2. 每块在任意层级只属于一个区域 | ✅ R13-01 的 cond_block method chain 前缀归属 TernaryRegion 父 Call；R13-02 的 BUILD_SLICE + DELETE_SUBSCR 归属 TernaryRegion 父 Delete；R13-07 每个 DELETE_* 独占一个 target slot；R13-08/10 的 BUILD_* + sibling 元素归属 TernaryRegion 父容器 |
| 3. 嵌套区域在父区域中作为单个抽象节点 | ✅ R13-01 的 `s.upper()` 作为 `split` 的 receiver 子节点；R13-04 的 `h(ternary)` 作为 `g(...)` 的 arg 子节点；R13-11 的 ternary 作为 `method()` 的 receiver 子节点 |
| 4. 父区域 then/else 列表引用子区域入口 | ✅ R13-01 父 Call 通过 cond_block 的 LOAD_METHOD chain 引用 ternary 子节点；R13-04/09 父 Call 通过 merge_block 的 PRECALL+CALL chain 引用 ternary 子节点；R13-08/10 父容器通过 BUILD_* + sibling preload 引用 ternary 子节点 |

### 5.2 禁止事项自检

| 禁止事项 | 本轮是否违反 |
|----------|--------------|
| 跨区域跨层次启发式 | 否 |
| 后处理补丁 | 否 |
| 启发式优先级覆盖 | 否 |
| 硬编码深度上限 | 否 |
| 破坏嵌套天然支持 | 否（R13-01 的 while 循环天然支持任意长度 method chain） |
| 修改测试文件 | 否 |
| 修改 R12 已通过测试 | 否 |
| 引入跨区域特例 | 否（R13-01 仅扩展 LOAD_METHOD 检测的前向链式识别，与既有 LOAD_METHOD+obj_chain 反向识别同模式） |
| 修改 R12 已知限制 | 否（15 个 R11 已知限制 + 2 个 R13 已知限制全部仍失败，未触动） |
| 基线退化（88 failed → 89+） | 否（88 failed ≤ 89 failed 基线，且实际 -1） |

### 5.3 清理工作

- 临时调试脚本：删除 `/workspace/_debug_r13.py`（前阶段调试脚本）
- 项目根目录无 `_debug_*.py` 残留（已用 Glob 验证）
- round_13 目录仅含 `test_findings.md` + `fix_report.md`

---

## 6. 修改文件清单

### 6.1 `core/cfg/region_analyzer.py`（+52 行 / -3 行）

**修改 1**（L11226-11285）— R13-01
`_detect_ternary_context` 中 LOAD_METHOD 检测新增 method chain 前向识别循环。原逻辑只识别第一个 LOAD_METHOD 作为 func.attr；新增循环检测 `PRECALL + CALL + LOAD_METHOD` 链式模式，将前一个 method call 包装为 Call 作为 receiver，用新 LOAD_METHOD 作为 func.attr。仅处理 0-arg 中间方法调用（PRECALL 紧跟 LOAD_METHOD），保守不退化。

### 6.2 `core/cfg/region_ast_generator.py`（+467 行 / -11 行）

**修改 1**（L18468-18491）— R13-08/10/04/09/11/05
`_generate_ternary` else 分支新增 `_try_build_ternary_merge_consumer_expr` 调用入口。当 merge_block 含 consumer ops（BUILD_* N>1 / 多 PRECALL+CALL / LOAD_METHOD receiver / MAKE_FUNCTION）时，优先用 expr_reconstructor 重建完整表达式。

**修改 2**（L19170-19207）— R13-09
`_compute_ternary_cond_preload_exprs` 的 compound fallback 改用 `_split_preload_into_siblings` 切分多兄弟 preload，每个 sub-slice 独立 reconstruct。

**修改 3**（L19209-19292）— R13-09
新增 `_split_preload_into_siblings` + `_stack_effect`。按栈深度反向切分 preload 前缀为 per-sibling sub-slice，每个 sub-slice 留恰好 1 个净栈项。

**修改 4**（L19885-19920）— R13-03
AugAssign 分支检测 `before_store` 中 CALL，若有则用 `expr_reconstructor` 以 `[callable, ternary_expr]` 为 initial_stack 重建 Call 表达式作为 AugAssign.value。

**修改 5**（L20126-20149）— R13-07
`_build_chained_ternary_del` Pattern D 之前新增 multi-target del 检测：cond preload 含 DELETE_* 时调用 `_build_multi_target_del_targets` 构造多目标 Delete。

**修改 6**（L20172-20265）— R13-07
新增 `_build_multi_target_del_targets`。前向遍历 preload，在每个 DELETE_ATTR/DELETE_SUBSCR/DELETE_NAME 处构造 Del target 并弹栈，最后剩余栈顶作为当前 ternary subscript 的 obj。

**修改 7**（L20388-20506）— R13-08/10/04/09/11/05
新增 `_try_build_ternary_merge_consumer_expr`。统一处理 merge_block 含 consumer ops 的场景：
- `_has_multi_elem`（BUILD_* N>1 或有 preload siblings）→ 多元素容器
- `_has_call_chain`（多个 CALL）→ 嵌套 Call 链
- `_has_receiver_method`（LOAD_METHOD 且无 func_call_info）→ ternary 作 receiver
- `_has_make_function`（MAKE_FUNCTION）→ lambda with default（R13-05 已触发但 reconstruct 不完全，留作已知限制）

**修改 8**（L21208-21405）— R13-02
`_build_chained_ternary_del` 新增 Pattern E（`del x[t1:t2]`）：innermost_merge 含 BUILD_SLICE 2 + DELETE_SUBSCR 时，从 outer.cond preload 提取 obj，构造 `Delete(targets=[Subscript(obj, Slice(t1, t2, None), Del)])`。Pattern D 加 `_has_build_slice_d` 守卫避免误走。

---

## 7. 总结

R13 共修复 **9 个新发现 bug**，覆盖 5 类常见 Python 代码模式：

1. **string method chain + ternary arg**（R13-01）：`s.upper().split(ternary)` 等 method chain 中间环节 + ternary arg
2. **del slice 双界 ternary**（R13-02）：`del x[t1:t2]` 双 ternary slice
3. **aug assign + call + ternary**（R13-03）：`x[k] += f(ternary)` 复合赋值 + call
4. **嵌套 Call 链 ternary**（R13-04）：`f(g(h(ternary)))` 多层嵌套 Call
5. **多目标 del + ternary subscript**（R13-07）：`del t1, obj[ternary]` 多目标 del
6. **container literal 中间元素 ternary**（R13-08/10）：`[a, ternary, b]` / `{k1:v1, k2:ternary, k3:v3}` 多元素容器
7. **Call 中间参数 + 兄弟 Call**（R13-09）：`f(g(0), ternary, h(1))` 多参数 Call + 兄弟是 Call
8. **receiver method call ternary**（R13-11）：`(ternary).method()` ternary 作 receiver

所有 9 个修复均符合区域归约 4 原则，未引入跨区域特例，未触动 R12 已通过测试与 R11/R12 已知限制测试。ternary 全量基线 88 failed（较 R12 基线 86 + R13 新增 11 = 97 减少 9），跨区域 131 failed 与基线一致（无退化）。

R13-05（lambda default）与 R13-06（nested lambda）作为 R14+ 已知限制，分别涉及 MAKE_FUNCTION + code object 递归与跨 code object 嵌套 lambda 反编译，复杂度中-高，留待 R14+ 修复。
