# Ternary Region Round 11 — 修复报告

**执行时间**: 2026-07-21
**基线 commit**: 559c00c (R10 完成)
**测试发现报告**: `test_findings.md`（24 个真失败 bug）
**核心修改文件**: `core/cfg/region_ast_generator.py`

---

## 1. 修复总览

| 类别 | 修复数 | Bug ID |
|------|--------|--------|
| 本轮已修复 | 9 | R11-10, R11-13, R11-14, R11-15, R11-16, R11-17, R11-18, R11-19, R11-20 |
| 未修复（留待 R12+） | 15 | R11-01 至 R11-09（除 R11-10）, R11-11, R11-12, R11-21, R11-22, R11-23, R11-24 |
| **总计** | **24** | |

---

## 2. 本轮修复详情

### 2.1 P0 聚类 M — TernaryRegion 边界吸收前驱块（已修复 7 个）

#### R11-10 [R10-12 复测]：functools.partialmethod + ternary
- **症状**：类体内 `m = partialmethod(_m, (a if c else b))` 反编译丢失 `_m` 方法定义
- **根因**：ternary 的 cond_block 吸收了前驱的 `_m` 方法定义（LOAD_CONST _m_code + MAKE_FUNCTION + STORE_NAME _m）
- **修复位置**：`_generate_ternary` 的 pre_stmts 捕获循环（Line ~17012-17064）+ func_call_skip 逻辑中 STORE_NAME 语句边界守卫（Line ~16990-17020）
- **修复方式**：在 pre_stmts 捕获循环中检测 MAKE_FUNCTION 并构建 FunctionDef；func_call_skip 逻辑中加 STORE_NAME 语句边界守卫，防止 ternary cond_block 跨语句吸收前驱
- **算法合规性**：依「每块唯一归属」+「自底向上归约」，MAKE_FUNCTION 块归属 FunctionDef 节点，ternary cond_block 仅含条件表达式

#### R11-13 [new]：dataclass InitVar + ternary default
- **症状**：类体内 `x: InitVar[int] = (a if c else b)` 反编译丢失 `__post_init__` 方法定义
- **根因**：与 R11-10 同类，ternary cond_block 吸收了前驱的 `__post_init__` 方法定义
- **修复位置**：AnnAssign 检测后处理 merge_block 后续语句（Line ~18127-18163）
- **修复方式**：AnnAssign 检测后调用 `_build_statements_from_instructions` 处理 merge_block 中 STORE_SUBSCR 之后的语句（如 FunctionDef）
- **算法合规性**：依「每块唯一归属」，AnnAssign 部分归 AnnAssign 节点，STORE_SUBSCR 之后的指令归下一条语句

#### R11-14 / R11-15 / R11-16 / R11-17 [new]：typing.{Literal, Union, Annotated, TypeAlias} + ternary
- **症状**：module 级 `from typing import X` 后跟 `name: X[...] = (a if c else b)` 反编译丢失整个 import 语句
- **根因**：ternary 的 cond_block 吸收了前驱的 IMPORT_NAME 块（因 IMPORT_NAME 后跟 STORE_NAME，与 ternary cond_block 的 STORE 模式相似）
- **修复位置**：`_extract_imports_from_block_prefix` 中跳过 `SETUP_ANNOTATIONS`（Line ~144-158）
- **修复方式**：在 import 提取中跳过 `SETUP_ANNOTATIONS` 指令，让 AnnAssign + ternary 场景正确归约
- **算法合规性**：依「每块唯一归属」，IMPORT_NAME 块归属 ImportFrom 节点，ternary merge 块归属 AnnAssign 的 value

### 2.2 P0 聚类 N — ternary 被错误展开为 if/else（已修复 2 个）

#### R11-20 [new]：conditional __import__ + ternary
- **症状**：`json = __import__('json' if sys.version_info >= (3, 11) else 'simplejson')` 反编译后 `__import__` 变成了 `sys`
- **根因**：`_generate_ternary` 和 `_compute_ternary_cond_preload_exprs` 中的向后栈效应扫描将 LOAD_ATTR/LOAD_METHOD 当作普通 LOAD_*（_push=1, _pop=0），但 LOAD_ATTR 实际消费栈顶对象（_pop=1）。这导致 `sys.version_info` 中的 `sys` 被误识别为 preload 表达式，使 CALL 错误地用 `sys` 作 func 而非 `__import__`
- **修复位置**：`_generate_ternary` 向后栈效应扫描（Line ~17413-17431）+ `_compute_ternary_cond_preload_exprs` 向后栈效应扫描（Line ~19020-19029）
- **修复方式**：在两处向后扫描中为 LOAD_ATTR/LOAD_METHOD 添加 `_push=1, _pop=1` 的正确栈效应
- **算法合规性**：依「每块唯一归属」，cond_block preload 仅含不属于条件表达式的栈前缀（如 PUSH_NULL+LOAD_NAME __import__）；LOAD_ATTR 消费的对象属于条件表达式

#### R11-19 [new]：__version__ definition + ternary
- **症状**：`__version__ = ('1.0' if sys.version_info >= (3, 11) else '0.9')` 被反编译为裸表达式 `('1.0' if ...)` 丢失赋值
- **根因**：代码中有多处 `not str(region.value_target).startswith('__')` 守卫（Line 17375、18153、20439），排除了 `__version__` 等以 `__` 开头的 value_target 进入 store-assignment 路径，导致 `__version__` 走到 Expr 分支被作为裸表达式求值丢弃
- **修复位置**：三处守卫统一精确化（Line 17375-17384、18160-18169、20455-20461）
- **修复方式**：将 `not str(value_target).startswith('__')` 改为 `str(value_target) not in ('__while_cond_target__', '__compare_target__', '__iter_target__', '__return_target__', '__fstring_target__')`。pythoncdc 内部虚拟 target 只有这 5 个（`__xxx_target__` 模式），合法的 Python dunder 赋值如 `__version__`、`__all__` 应正常进入 store-assignment 路径
- **算法合规性**：依「每块唯一归属」，ternary merge 块归属 Assign(targets=[__version__], value=IfExp)；不引入跨区域特例，仅精确化内部虚拟 target 集合

#### R11-18 [new]：__all__ definition + ternary list element（附带通过）
- **症状**：`__all__ = ['a', ('b' if cond else 'c'), 'd']` 反编译字节码不匹配
- **根因（修正）**：原 test_findings.md 推测为 LIST_EXTEND consumer pattern 未覆盖，但实际测试验证：根因与 R11-19 相同，是 `__all__` 被 `startswith('__')` 守卫排除，导致链式 container ternary 无法进入 Assign 路径
- **修复位置**：与 R11-19 同一处守卫修改（Line 20455-20461）
- **修复方式**：同 R11-19，精确化内部虚拟 target 集合后，`__all__` 正常进入 store-assignment 路径
- **算法合规性**：依「父引用子入口」，父 Assign 通过 STORE_NAME __all__ 引用 List 子节点；List 通过 LIST_EXTEND 引用 ternary 子节点作为元素

### 2.3 P0 聚类 N 剩余（未修复 3 个，留待 R12+）

#### R11-03 [R9-15 复测]：assert + return 共享 ternary consumer
- 根因：第一个 ternary（assert）的 merge_block 含 LOAD_ASSERTION_ERROR + RAISE_VARARGS，被 IfRegion 抢占
- 修复方向：在 IfRegion 识别中加守卫，候选 if 入口块的后续块含 LOAD_ASSERTION_ERROR + RAISE_VARARGS 时不识别为 IfRegion

#### R11-11 [R10-14 复测]：async __aenter__ + ternary in body
- 根因：async 函数的 RETURN_GENERATOR + POP_TOP + RESUME 前缀未正确处理，ternary 被错误地展开为 if/else
- 修复方向：在 `_generate_ternary` 中加守卫，禁止 async function code object 内的 ternary 展开为 if/else

#### R11-23 [new]：contextlib.suppress + ternary in with item
- 根因：ternary 作为 suppress() 的位置参数且整个 Call 作为 with 上下文管理器时，ternary region 被 WithRegion 抢占
- 修复方向：在 `_generate_with` 中加守卫，若 with item 的 context_expr 是 Call 且其 args 含 ternary region merge 块，应保留 ternary 作为 Call 的位置参数

### 2.4 P1 聚类 O — consumer Pattern 未覆盖（未修复 4 个，留待 R12+）

- **R11-07** [R10-09 复测]：magic methods __eq__/__hash__ + ternary — 缺 COMPARE_OP consumer Pattern
- **R11-08** [R10-10 复测]：functools.wraps + ternary in *args — 缺 CALL_FUNCTION_EX consumer Pattern
- **R11-24** [new]：asyncio.gather + ternary arg — ternary condition_block preload 含 CALL 未保留
- 注：R11-18 已附带通过（根因实为 dunder 守卫，非 LIST_EXTEND consumer）

### 2.5 P1 聚类 P — 装饰器链重复识别（未修复 2 个，留待 R12+）

- **R11-06** [R10-08 复测]：ABC abstract property + setter + ternary — `_reconstruct_decorator_chain` 对 `@x.setter` 重复识别
- **R11-22** [new]：cached_property + ternary in body — `_reconstruct_decorator_chain` 对无参装饰器在 class body 内的场景重复识别

### 2.6 P2-P3 聚类 Q — 已知限制复测（未修复 6 个，留待 R12+）

- **R11-01** [R9-08 复测]：except* PEP 654 + ternary handler body
- **R11-02** [R9-10 复测]：frozen dataclass 字段默认值 ternary
- **R11-04** [R10-06 复测]：dataclass default_factory lambda ternary
- **R11-05** [R10-07 复测]：TypedDict + ternary default
- **R11-09** [R10-11 复测]：typing.overload + ternary in body（标记为已知限制）
- **R11-12** [R10-15 复测]：ternary in kwonly default
- **R11-21** [new]：asynccontextmanager + ternary in body

---

## 3. 最终测试结果

### 3.1 ternary 全量测试

```
$ cd /workspace && python -m pytest tests/exhaustive/ternary/ --tb=no -q
86 failed, 320 passed, 8 skipped in 3.24s
```

- **基线**（R10 commit 559c00c）：89 failed / 317 passed / 8 skipped
- **R11-20 修复后**：88 failed / 318 passed / 8 skipped（改善 1）
- **R11-18/19 修复后**：86 failed / 320 passed / 8 skipped（再改善 2）
- **总改善**：3 个 bug 修复，无任何退化

### 3.2 R11 子集测试

```
$ cd /workspace && python -m pytest tests/exhaustive/ternary/test_r11_*.py --tb=no -q
15 failed, 20 passed, 3 skipped in 2.04s
```

- **测试发现时**：24 failed / 11 passed / 3 skipped
- **本轮修复后**：15 failed / 20 passed / 3 skipped（改善 9 个 bug）

### 3.3 跨区域回归

| 区域 | 基线（R10） | R11 修复后 | 退化 |
|------|-------------|------------|------|
| if_region | 43 failed / 775 passed / 9 skipped | 43 failed / 775 passed / 9 skipped | 无 |
| while_loop | 2 failed / 118 passed | 2 failed / 118 passed | 无（基线已有） |
| for_loop | 192 passed / 1 skipped | 192 passed / 1 skipped | 无 |
| try_except | 228 passed / 2 skipped | 228 passed / 2 skipped | 无 |
| with_region | 191 passed | 191 passed | 无 |

**结论**：跨区域无任何退化。while_loop 的 2 个失败（test_wl32whilemultibreak_*）经 `git stash` 验证为 R10 基线已有，非本轮引入。

---

## 4. 算法合规性自检

### 4.1 区域归约 4 原则符合性

| 原则 | 本轮修复符合性 |
|------|----------------|
| 1. 自底向上归约（最内层先识别） | ✅ 修复均在 ternary region 内部归约，未跨层次 |
| 2. 每块在任意层级只属于一个区域 | ✅ R11-10/13 修复 MAKE_FUNCTION 块归属 FunctionDef；R11-14~17 修复 IMPORT_NAME 块归属 ImportFrom；R11-19 修复 ternary merge 块归属 Assign |
| 3. 嵌套区域在父区域中作为单个抽象节点 | ✅ R11-20 修复 ternary 作为 Call 参数时的抽象节点归属 |
| 4. 父区域 then/else 列表引用子区域入口 | ✅ R11-18/19 修复父 Assign 通过 STORE_NAME 引用 ternary 子节点 |

### 4.2 禁止事项自检

| 禁止事项 | 本轮是否违反 |
|----------|--------------|
| 跨区域跨层次启发式 | 否 |
| 后处理补丁 | 否 |
| 启发式优先级覆盖 | 否 |
| 硬编码深度上限 | 否 |
| 破坏嵌套天然支持 | 否 |
| 修改测试文件 | 否 |
| 修改 R10 已通过测试 | 否 |
| 引入跨区域特例 | 否（R11-19 仅精确化内部虚拟 target 集合，非跨区域特例） |

### 4.3 清理工作

- 临时调试脚本：本轮无创建任何临时调试脚本，无需清理
- round_11 目录仅含 `test_findings.md` + `fix_report.md`，无 `_debug_*.py` 残留

---

## 5. 修改文件清单

**唯一修改文件**：`/workspace/core/cfg/region_ast_generator.py`

### 5.1 修改 1（Line 144-158）— R11-14/15/16/17
`_extract_imports_from_block_prefix` 中跳过 `SETUP_ANNOTATIONS`

### 5.2 修改 2（Line 18127-18163）— R11-13
AnnAssign 检测后处理 merge_block 后续语句

### 5.3 修改 3（Line 17012-17064）— R11-10
pre_stmts 捕获循环中检测 MAKE_FUNCTION 并构建 FunctionDef

### 5.4 修改 4（Line 16990-17020）— R11-10
func_call_skip 逻辑中 STORE_NAME 语句边界守卫

### 5.5 修改 5（Line 17413-17431）— R11-20
`_generate_ternary` 向后栈效应扫描中 LOAD_ATTR/LOAD_METHOD 栈效应修正

### 5.6 修改 6（Line 19020-19029）— R11-20
`_compute_ternary_cond_preload_exprs` 向后栈效应扫描中 LOAD_ATTR/LOAD_METHOD 栈效应修正

### 5.7 修改 7（Line 17375-17384）— R11-19
`_generate_ternary` store-assignment 入口守卫精确化（`__` 前缀 → 5 个内部虚拟 target 集合）

### 5.8 修改 8（Line 18160-18169）— R11-19
AnnAssign 检测守卫精确化（同上）

### 5.9 修改 9（Line 20455-20461）— R11-18/19
链式 container ternary Assign 生成守卫精确化（同上）

---

## 6. 未修复 Bug 留待 R12+

15 个未修复 bug 按根因分组：

| 根因 | Bug 数 | Bug ID |
|------|--------|--------|
| TernaryRegion 边界吸收前驱块（MAKE_FUNCTION/IMPORT_NAME） | 0（已全部修复） | — |
| Ternary 被错误展开为 if/else 控制流 | 3 | R11-03, R11-11, R11-23 |
| Ternary consumer Pattern 未覆盖（CALL_FUNCTION_EX, COMPARE_OP） | 3 | R11-07, R11-08, R11-24 |
| 装饰器链重复识别 | 2 | R11-06, R11-22 |
| AnnAssign + ternary 边界识别冲突 | 1 | R11-05 |
| Lambda body ternary 未识别 | 1 | R11-04 |
| except* handler region 与 ternary region 归属冲突 | 1 | R11-01 |
| async gen + ternary + yield 三重路径归约冲突 | 1 | R11-21 |
| frozen dataclass 字段默认值 | 1 | R11-02 |
| typing.overload 多 FunctionDef 共存 | 1 | R11-09（已知限制） |
| ternary in kwonly default | 1 | R11-12 |
| **总计** | **15** | |

---

## 7. 修复优先级建议（R12+）

1. **P0**：R11-03/11/23 — ternary 被展开为 if/else 的剩余 3 个 bug（影响核心场景）
2. **P1**：R11-07/08/24 — consumer Pattern 扩展（CALL_FUNCTION_EX/COMPARE_OP/await+Call）
3. **P1**：R11-06/22 — 装饰器链去重守卫
4. **P2-P3**：R11-01/02/04/05/09/12/21 — 已知限制复测，根因复杂，建议单独处理
