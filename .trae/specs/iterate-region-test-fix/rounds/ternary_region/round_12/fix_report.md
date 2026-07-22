# Ternary Region Round 12 — 修复报告

**执行时间**: 2026-07-21
**基线 commit**: 96b23e7 (R11 完成)
**测试发现报告**: `test_findings.md`（21 个真失败 bug = 15 个 R11 已知限制 + 6 个 R12 新发现）
**核心修改文件**:
- `core/cfg/region_analyzer.py`
- `core/cfg/region_ast_generator.py`
- `core/cfg/code_generator.py`

---

## 1. 修复总览

| 类别 | 修复数 | Bug ID |
|------|--------|--------|
| 本轮已修复（R12 新发现） | 6 | R12-01, R12-02, R12-03, R12-04, R12-05, R12-06 |
| 未修复（R11 已知限制） | 15 | R11-01~09（除 R11-10）, R11-11, R11-12, R11-21~24 |
| **总计** | **21** | |

---

## 2. 本轮修复详情

### 2.1 P0 聚类 R — 容器字面量 *-unpack 解包（已修复 3 个，同根因）

#### R12-02 / R12-04 / R12-06：ternary 在 dict/list/set 字面量 `**`/`*` 展开位置

- **症状**:
  - R12-02 `{**(a if c else b)}` → 反编译为 `(a if c else b)`（丢失 dict 字面量与 `**`）
  - R12-04 `[*(a if c else b)]` → 反编译为 `(a if c else b)`（丢失 list 字面量与 `*`）
  - R12-06 `{*(a if c else b)}` → 反编译为 `(a if c else b)`（丢失 set 字面量与 `*`）
- **根因**: `_detect_ternary_context` 仅识别 `BUILD_MAP/BUILD_LIST/BUILD_SET`/`MAP_ADD` 等 container 构造指令，未识别 merge_block 中的 `DICT_UPDATE 1`/`LIST_EXTEND 1`/`SET_UPDATE 1` 消费指令（`*-unpack` 路径）。导致 TernaryRegion 的 container_type 为 None，merge 块的栈输出被当作独立表达式 POP_TOP。
- **修复位置 1**: `core/cfg/region_analyzer.py` `_detect_ternary_context` (L11116-11128)
  - 新增 `DICT_UPDATE` → 返回 `container_type='dict_unpack'`
  - 新增 `LIST_EXTEND` → 返回 `container_type='list_unpack'`
  - 新增 `SET_UPDATE` → 返回 `container_type='set_unpack'`
- **修复位置 2**: `core/cfg/region_ast_generator.py` `_generate_ternary` 容器类型分支 (L18453-18479)
  - `dict_unpack` → `Dict(keys=[Starred(ternary)], values=[None])`
  - `list_unpack` → `List(elts=[Starred(ternary)], ctx='Load')`
  - `set_unpack` → `Set(elts=[Starred(ternary)])`
  - 采用代码库既有约定（`ast_generator_v2.py` L89-91）：dict 的 `**expr` 项以 `Starred(value=expr)` 作 key、`None` 作 value；list/set 的 `*expr` 项以 `Starred(value=expr)` 作 elt。
- **修复位置 3**: `core/cfg/code_generator.py` dict-based 节点渲染 (L3098-3139)
  - 新增 `Set` 分支：`{elt1, elt2, ...}` 形式渲染（与 List 镜像）
  - `Dict` 分支增强：当 `Starred.value` 是低优先级复合表达式（IfExp/BoolOp/NamedExpr/Lambda/Yield 等）时加括号，避免 `{**a if c else b}` 语法错误
- **算法合规性**:
  - 「每块唯一归属」: merge_block 的 `*_UPDATE`/`*_EXTEND` 消费指令归属 TernaryRegion；cond_block 的 `BUILD_<container> 0` preload 也归属 TernaryRegion（同根因 DICT_MERGE/LIST_EXTEND/SET_UPDATE）
  - 「嵌套即抽象节点」: Starred 是 ternary 的父节点包装，container 是 Starred 的父节点
  - 「父引用子入口」: 父 Container 通过 `*_UPDATE`/`*_EXTEND` 引用 ternary 子节点
- **验证结果**: 3 个测试 `test_r12_ternary_dict_merge_double_star.py` / `test_r12_ternary_list_extend_star.py` / `test_r12_ternary_set_update_star.py` 全部通过

### 2.2 P0 R12-05 — kwarg + preload 位置参数（已修复 1 个）

- **症状**: `max(x, default=(a if c else b))` 反编译为 `max(default=a if c else b)` — 丢失位置参数 `x`
- **根因**: `_try_build_ternary_kwarg_call` 中 preload 逻辑假设 preload args 在 PUSH_NULL 之前（Pre-3.11 布局），但 Python 3.11+ 的 `LOAD_GLOBAL` 隐式 PUSH_NULL，func setup 在 idx 0，preload args 在 func 之后。原有逻辑只检查 PUSH_NULL 之前的部分，导致 `LOAD_NAME x` 被丢失。
- **修复位置**: `core/cfg/region_ast_generator.py` `_try_build_ternary_kwarg_call` (L21003-21028)
- **修复方式**: 使用 `_compute_ternary_cond_preload_exprs(region)` 获取所有 cond_block preload 表达式列表，跳过函数本身（第一个元素），取接下来的 `preload_count` 个作为位置参数
- **算法合规性**:
  - 「每块唯一归属」: cond_block 的 preload（含函数与位置参数 x）归属 TernaryRegion 父表达式（Call）；preload_args 数量 = total_args - kwarg_count - num_positional_from_ternary
  - 「父引用子入口」: 父 Call 通过 KW_NAMES + PRECALL + CALL 引用 ternary 子节点作为 kwarg value；preload_args 提供 Call 的位置参数
- **验证结果**: `test_r12_ternary_max_default.py` 通过

### 2.3 P0 R12-01 — bool or short circuit + ternary（已修复 1 个）

- **症状**: `r = x or (a if c else b)` 反编译为 `r = (x or (a if c else b) and a)` — 多出 `and a` 后缀
- **根因**: `BoolOpRegion.op_chain` 包含 `[(block@0, 'or'), (block@6, 'and')]`，其中 block@6 是嵌套 ternary 的 cond_block。fall-through 块检测逻辑把 ternary 的 true_block (LOAD_NAME a) 当作 `and a` 的额外操作数。
- **修复位置**: `core/cfg/region_ast_generator.py` `_build_boolop_expression` (L15782-15792)
- **修复方式**: 在 fall-through 块检测条件中添加 `nested_ternary is None` 守卫：当 chain_block 自身是嵌套 ternary 的 cond_block 时，其 true/false 分支已纳入 IfExp，不应再作为「fall-through 块附加操作数」重复求值
- **算法合规性**:
  - 「每块唯一归属」: ternary 的 true/false 块归属 TernaryRegion（由 nested_ternary 表达），不归属 BoolOpRegion 的操作数链
  - 「嵌套即抽象节点」: 嵌套 ternary 在父 BoolOp 中作为单个抽象节点（操作数）
- **验证结果**: `test_r12_ternary_bool_or_short_circuit.py` 通过

### 2.4 P0 R12-03 — extended slice + ternary（已修复 1 个）

- **症状**: `r = x[a:b, c if d else e]` 反编译为 `r = a[b, c if d else e]` — 第一个 `x` 被替换为 `a`，切片 `a:b` 完全丢失
- **根因**: cond_block preload 中的 `BUILD_SLICE 2` 指令在 `_preload_instrs` 收集逻辑中无任何分支匹配（既不在 LOAD_* / STORE_* / BUILD_LIST/TUPLE/SET/MAP/CONST_KEY_MAP 列表，也不在 FORMAT_VALUE 分支），被默默忽略。结果切片边界 `a, b` 作为独立栈项留在 preload_stack 中，merge 块的 `BUILD_TUPLE 2 + BINARY_SUBSCR` 错误地以 `a` 作下标对象、`b` 与 ternary 作元组元素。
- **修复位置**: `core/cfg/region_ast_generator.py` `_generate_ternary` preload 收集循环 (L17576-17606)
- **修复方式**: 新增 `BUILD_SLICE` elif 分支：
  - `_slice_arity = _ki.arg or 2`（2 或 3，对应 `a:b` 与 `a:b:c`）
  - 若 preload_instrs 中有足够前驱项，取出最后 `_slice_arity` 项与 BUILD_SLICE 一起打包成 list（沿用 LOAD_ATTR 与前驱 LOAD_* 的分组约定）
  - 后续 _preload_stack 构建时，`isinstance(pi, list)` 分支会调用 `expr_reconstructor.reconstruct([LOAD_a, LOAD_b, BUILD_SLICE 2])`，由现有 BUILD_SLICE 处理逻辑 (L8849) 弹 2 项压 `Slice(a, b, None)`
- **算法合规性**:
  - 「父引用子入口」: 父 Subscript 通过 cond preload (x, Slice(a, b)) + merge (BUILD_TUPLE, BINARY_SUBSCR) 引用 ternary 子节点
  - 「每块唯一归属」: cond_block 的 BUILD_SLICE preload 归属 TernaryRegion 父表达式（Subscript）；与 R5-15 Pattern 8 (`x[1:(ternary)]` 单维切片) 的镜像场景 — R5-15 中 BUILD_SLICE 在 merge_block，R12-03 中 BUILD_SLICE 在 cond preload，两者通过 BUILD_SLICE 的统一栈效应归约
- **验证结果**: `test_r12_ternary_extended_slice.py` 通过；输出为 `r = x[a:b, c if d else e]`

---

## 3. R11 已知限制评估与标记（15 个未修复）

R11 已知限制全部仍失败，根因保持不变，留待 R13+ 修复。按修复成本/影响面分类：

### 3.1 P1（中优先级，根因较清晰，R13 可考虑）

| Bug ID | 症状简述 | 根因简述 | 修复方向 |
|--------|----------|----------|----------|
| R11-03 | assert + return 共享 ternary consumer | 第一个 ternary（assert）的 merge_block 含 LOAD_ASSERTION_ERROR + RAISE_VARARGS，被 IfRegion 抢占 | IfRegion 识别加守卫：候选 if 入口块后续块含 LOAD_ASSERTION_ERROR + RAISE_VARARGS 时不识别为 IfRegion |
| R11-08 | functools.wraps + ternary in `*args` | ternary `args if c else ()` 在 `*args` 展开位置完全丢失；反编译器误把 c 当作 global、f 当作 nonlocal | 加 CALL_FUNCTION_EX consumer pattern，正确归并 ternary 到 *args 位置 |
| R11-23 | contextlib.suppress + ternary in with item | ternary 作为 suppress() 参数且整个 Call 作为 with 上下文管理器，ternary region 被 WithRegion 抢占 | `_generate_with` 加守卫：with item 的 context_expr 是 Call 且 args 含 ternary region merge 块时保留 ternary 作为 Call 参数 |
| R11-12 | ternary in kwonly default | ternary 作为 kwonly 参数 x 默认值，反编译器把 `*args` 与 `x` 调换位置 | 处理 BUILD_CONST_KEY_MAP + KW_NAMES + ternary merge 的栈输出关系 |
| R11-24 | asyncio.gather + ternary arg | ternary 作为 gather 第一个位置参数 + gather(ternary, h()) 被 await | ternary condition_block preload 含 CALL 未保留，需扩展 ternary + 多位置参数 Call 重建 |

### 3.2 P2（低优先级，根因涉及多重特性交互）

| Bug ID | 症状简述 | 根因简述 |
|--------|----------|----------|
| R11-02 | frozen dataclass 字段默认值 ternary | dataclass 装饰器 + KW_APPS + CALL 栈帧与 AnnAssign ternary merge 块 STORE_NAME x 归属冲突 |
| R11-04 | dataclass default_factory lambda ternary | lambda code object 内 ternary 完全丢失；func_call_info 中 lambda 的 ternary 子区域未被引用 |
| R11-05 | TypedDict + ternary default | TypedDict 类体内 AnnAssign + ternary merge STORE_NAME year 与 TypedDict 基类 __total__ 注解 STORE_SUBSCR 路径冲突 |
| R11-06 | ABC abstract property + setter + ternary | 双层装饰器链 (@property + @abstractmethod) + @x.setter + ternary 赋值；`_reconstruct_decorator_chain` 对 `@x.setter` 重复识别 |
| R11-22 | cached_property + ternary | @cached_property 装饰器链 + ternary return；`_reconstruct_decorator_chain` 对无参装饰器在 class body 内场景重复识别 |
| R11-21 | asynccontextmanager + ternary in body | @asynccontextmanager + async generator + ternary + yield 四重路径交互 |
| R11-09 | typing.overload + ternary | 3 个同名 f 定义 + @overload 装饰器；@overload 装饰器重建时丢失 BUILD_TUPLE (类型注解元组) |

### 3.3 P3（最低优先级，涉及 Python 3.11+ 新特性或边缘场景）

| Bug ID | 症状简述 | 根因简述 |
|--------|----------|----------|
| R11-01 | except* PEP 654 + ternary handler body | except* handler 内 PUSH_EXC_INFO + CHECK_EG_MATCH + COPY 路径与 ternary merge 块 STORE_NAME x 在同一 handler body，归约冲突 |
| R11-11 | async __aenter__ + ternary | async 方法 + RETURN_GENERATOR + ternary merge STORE_ATTR x + RETURN_VALUE |
| R11-07 | __eq__/__hash__ + ternary | __eq__ 内 `self.x == (other.x if c else 0)` 比较表达式 + ternary；ternary consumer pattern 没覆盖 COMPARE_OP 的左操作数 self.x 属性访问 |

---

## 4. 最终测试结果

### 4.1 ternary 全量测试

```
$ cd /workspace && timeout 300 python -m pytest tests/exhaustive/ternary/ --tb=no -q
86 failed, 335 passed, 8 skipped in 3.82s
```

- **基线**（R11 commit 96b23e7）：86 failed / 320 passed / 8 skipped
- **本轮 R12 修复后**：86 failed / 335 passed / 8 skipped
- **变化**: 失败数 -0（无退化），通过数 +15（6 个 R12 修复 + 9 个 R12 测试本已通过）
- **结论**: 无任何基线退化，6 个 R12 新 bug 全部修复

### 4.2 R12 子集测试

```
$ cd /workspace && python -m pytest tests/exhaustive/ternary/test_r12_ternary_*.py --tb=no -q
15 passed in 0.37s
```

- 6 个原 FAIL 测试全部转为 PASS（R12-01/02/03/04/05/06）
- 9 个原 PASS 测试保持 PASS（R12 内置函数/binop/slice/fstring 等对抗性测试）

### 4.3 跨区域回归（git stash 验证）

| 区域 | 基线（R11） | R12 修复后 | 退化 |
|------|-------------|------------|------|
| boolop + bool_op | 9 failed | 9 failed | 无 |
| match_region + basic + structured | 4 failed | 4 failed | 无 |
| **合计** | **13 failed / 470 passed / 3 skipped** | **13 failed / 470 passed / 3 skipped** | **无** |

**验证方式**: 通过 `git stash` 暂存所有 3 个修改文件，跑跨区域测试得到基线 13 failed / 470 passed；`git stash pop` 恢复后再次跑得到相同 13 failed / 470 passed。两个数字完全一致证明无任何跨区域回归。

---

## 5. 算法合规性自检

### 5.1 区域归约 4 原则符合性

| 原则 | 本轮修复符合性 |
|------|----------------|
| 1. 自底向上归约（最内层先识别） | ✅ 所有修复均在 TernaryRegion 已归约后由父表达式（Subscript/Dict/List/Set/Call/BoolOp）消费 ternary 子节点 |
| 2. 每块在任意层级只属于一个区域 | ✅ R12-01 守卫确保 ternary 的 true/false 块归属 TernaryRegion 不被 BoolOp 抢占；R12-02/04/06 merge 块的 `*_UPDATE/_EXTEND` 归属 TernaryRegion；R12-03 BUILD_SLICE preload 归属 TernaryRegion 父表达式 |
| 3. 嵌套区域在父区域中作为单个抽象节点 | ✅ R12-01 ternary 在父 BoolOp 中作单操作数；R12-03 ternary 在父 Subscript 中作单维度；R12-05 ternary 在父 Call 中作单 kwarg value |
| 4. 父区域 then/else 列表引用子区域入口 | ✅ R12-02/04/06 父 Container 通过 `*_UPDATE/_EXTEND` 引用 ternary；R12-03 父 Subscript 通过 BUILD_TUPLE+BINARY_SUBSCR 引用 ternary |

### 5.2 禁止事项自检

| 禁止事项 | 本轮是否违反 |
|----------|--------------|
| 跨区域跨层次启发式 | 否 |
| 后处理补丁 | 否 |
| 启发式优先级覆盖 | 否 |
| 硬编码深度上限 | 否 |
| 破坏嵌套天然支持 | 否 |
| 修改测试文件 | 否 |
| 修改 R11 已通过测试 | 否 |
| 引入跨区域特例 | 否（R12-03 仅新增 BUILD_SLICE 到 preload 收集列表，与 BUILD_LIST/TUPLE/SET/MAP 同模式；R12-02/04/06 仅扩展 container_type 枚举值，沿用既有 dict/list/set 容器构造路径） |
| 修改 R11 已知限制 | 否（15 个 R11 已知限制测试全部仍失败，未触动） |
| 基线退化（86 failed → 87+） | 否（86 failed 保持不变） |

### 5.3 清理工作

- 临时调试脚本：本轮无创建任何临时调试脚本，无需清理
- round_12 目录仅含 `test_findings.md` + `fix_report.md`，无 `_debug_*.py` 残留

---

## 6. 修改文件清单

### 6.1 `core/cfg/region_analyzer.py`（+13 行）

**修改 1**（L11116-11128）— R12-02/04/06
`_detect_ternary_context` 中新增 `DICT_UPDATE`/`LIST_EXTEND`/`SET_UPDATE` 指令识别，分别返回 `dict_unpack`/`list_unpack`/`set_unpack` container_type。

### 6.2 `core/cfg/region_ast_generator.py`（+114 行 / -27 行）

**修改 1**（L18453-18479）— R12-02/04/06
`_generate_ternary` 容器类型分支新增 `dict_unpack`/`list_unpack`/`set_unpack` 三种 container_type 处理，按代码库约定以 `Starred(value=ternary_expr)` 包装 ternary 作 dict 的 key（value=None）/ list 的 elt / set 的 elt。

**修改 2**（L21003-21028）— R12-05
`_try_build_ternary_kwarg_call` 改用 `_compute_ternary_cond_preload_exprs` 正确识别 Python 3.11+ 隐式 PUSH_NULL 布局下的 preload 位置参数（跳过函数本身，取后续 preload_count 项）。

**修改 3**（L15782-15792）— R12-01
`_build_boolop_expression` fall-through 块检测条件中加 `nested_ternary is None` 守卫，防止 ternary 的 true/false 块被误识别为 boolop 的附加操作数。

**修改 4**（L17576-17606）— R12-03
`_generate_ternary` preload 收集循环新增 `BUILD_SLICE` elif 分支：将前 N（2 或 3）项 LOAD_* 与 BUILD_SLICE 一起打包成 list，沿用 LOAD_ATTR 的分组约定，由后续 `isinstance(pi, list)` 分支调用 `expr_reconstructor.reconstruct` 重建为 `Slice(lower, upper, step)` AST 节点。

### 6.3 `core/cfg/code_generator.py`（+24 行 / -3 行）

**修改 1**（L3098-3139）— R12-02/06
- dict-based 节点渲染新增 `Set` 分支：`{elt1, elt2, ...}` 形式渲染（与 List 镜像）
- `Dict` 分支增强：当 `Starred.value` 是低优先级复合表达式（IfExp/BoolOp/NamedExpr/Lambda/Yield/YieldFrom/Await/BinOp/UnaryOp/Compare/Starred）时加括号，避免 `{**(a if c else b)}` 被渲染为语法错误的 `{**a if c else b}`

---

## 7. 总结

R12 共修复 **6 个新发现 P0 bug**，覆盖 4 类常见 Python 代码模式：

1. **容器字面量 `*`-unpack**（R12-02/04/06，3 个同根因）：dict/list/set 解包 `**expr`/`*expr`
2. **kwarg + preload 位置参数**（R12-05）：`f(positional, kwarg=ternary)` 模式
3. **bool op 短路 + ternary**（R12-01）：`x or (ternary)` / `x and (ternary)` 模式
4. **extended slice + ternary**（R12-03）：多维下标含 ternary，如 numpy/pandas 索引

所有 6 个修复均符合区域归约 4 原则，未引入跨区域特例，未触动 R11 已通过测试与 R11 已知限制测试。ternary 全量基线 86 failed 保持不变（无退化），跨区域 13 failed 保持不变（无退化）。

R11 已知限制 15 个全部仍失败，按修复成本/影响面分为 P1（5 个）/P2（7 个）/P3（3 个）三级，留待 R13+ 修复。
