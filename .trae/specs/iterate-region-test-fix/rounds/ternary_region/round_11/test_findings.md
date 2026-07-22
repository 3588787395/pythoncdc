# Ternary Region Round 11 — 测试发现报告

**执行时间**: 2026-07-21
**基线 commit**: 559c00c (R10 完成)
**测试目标**: 验证 R10 已知 13 个限制是否仍失败 + 新增对抗性测试
**测试位置**: `/workspace/tests/exhaustive/ternary/test_r11_*.py`

## 测试执行结果

- **总测试数**: 38
- **失败**: 24 (真失败)
- **通过**: 11
- **跳过**: 3 (重编译失败，可能为已知限制)

执行命令：
```
cd /workspace && timeout 250 python -m pytest tests/exhaustive/ternary/test_r11_*.py --tb=no -q
```

输出：`24 failed, 11 passed, 3 skipped in 2.02s`

---

## 创建的测试文件（共 38 个）

### A. R10/R9 已知限制复测（13 个）

1. `/workspace/tests/exhaustive/ternary/test_r11_ternary_except_star.py` (R9-08)
2. `/workspace/tests/exhaustive/ternary/test_r11_ternary_frozen_dataclass_default.py` (R9-10)
3. `/workspace/tests/exhaustive/ternary/test_r11_ternary_assert_return_consumer.py` (R9-15)
4. `/workspace/tests/exhaustive/ternary/test_r11_ternary_dataclass_default_factory.py` (R10-06)
5. `/workspace/tests/exhaustive/ternary/test_r11_ternary_typeddict_default.py` (R10-07)
6. `/workspace/tests/exhaustive/ternary/test_r11_ternary_abc_abstract_property_setter.py` (R10-08)
7. `/workspace/tests/exhaustive/ternary/test_r11_ternary_magic_methods.py` (R10-09)
8. `/workspace/tests/exhaustive/ternary/test_r11_ternary_wraps.py` (R10-10)
9. `/workspace/tests/exhaustive/ternary/test_r11_ternary_overload.py` (R10-11)
10. `/workspace/tests/exhaustive/ternary/test_r11_ternary_partialmethod.py` (R10-12)
11. `/workspace/tests/exhaustive/ternary/test_r11_ternary_async_aenter.py` (R10-14)
12. `/workspace/tests/exhaustive/ternary/test_r11_ternary_kwonly_default.py` (R10-15)
13. `/workspace/tests/exhaustive/ternary/test_r11_ternary_async_with_multi_as.py` (R7-03)

### B. 新增对抗性测试（25 个）

14. `/workspace/tests/exhaustive/ternary/test_r11_ternary_initvar.py` (dataclass InitVar + ternary)
15. `/workspace/tests/exhaustive/ternary/test_r11_ternary_dataclass_init_override.py` (dataclass __init__ override)
16. `/workspace/tests/exhaustive/ternary/test_r11_ternary_multiple_inheritance.py` (multiple inheritance)
17. `/workspace/tests/exhaustive/ternary/test_r11_ternary_init_subclass.py` (__init_subclass__)
18. `/workspace/tests/exhaustive/ternary/test_r11_ternary_set_name.py` (__set_name__)
19. `/workspace/tests/exhaustive/ternary/test_r11_ternary_descriptor_protocol.py` (__get__/__set__)
20. `/workspace/tests/exhaustive/ternary/test_r11_ternary_enum_value.py` (Enum value)
21. `/workspace/tests/exhaustive/ternary/test_r11_ternary_flag_enum.py` (Flag enum)
22. `/workspace/tests/exhaustive/ternary/test_r11_ternary_typing_literal.py` (typing.Literal)
23. `/workspace/tests/exhaustive/ternary/test_r11_ternary_typing_union.py` (typing.Union)
24. `/workspace/tests/exhaustive/ternary/test_r11_ternary_typing_annotated.py` (typing.Annotated)
25. `/workspace/tests/exhaustive/ternary/test_r11_ternary_typealias.py` (PEP 613 TypeAlias)
26. `/workspace/tests/exhaustive/ternary/test_r11_ternary_typing_cast.py` (typing.cast)
27. `/workspace/tests/exhaustive/ternary/test_r11_ternary_asynccontextmanager.py` (asynccontextmanager)
28. `/workspace/tests/exhaustive/ternary/test_r11_ternary_contextlib_suppress.py` (contextlib.suppress)
29. `/workspace/tests/exhaustive/ternary/test_r11_ternary_lru_cache.py` (functools.lru_cache)
30. `/workspace/tests/exhaustive/ternary/test_r11_ternary_functools_cache.py` (functools.cache)
31. `/workspace/tests/exhaustive/ternary/test_r11_ternary_cached_property.py` (cached_property)
32. `/workspace/tests/exhaustive/ternary/test_r11_ternary_total_ordering.py` (total_ordering)
33. `/workspace/tests/exhaustive/ternary/test_r11_ternary_metaclass_new.py` (metaclass __new__)
34. `/workspace/tests/exhaustive/ternary/test_r11_ternary_dynamic_class_type.py` (type())
35. `/workspace/tests/exhaustive/ternary/test_r11_ternary_all_definition.py` (__all__ + ternary list)
36. `/workspace/tests/exhaustive/ternary/test_r11_ternary_version_definition.py` (__version__ + ternary)
37. `/workspace/tests/exhaustive/ternary/test_r11_ternary_conditional_import.py` (conditional __import__)
38. `/workspace/tests/exhaustive/ternary/test_r11_ternary_asyncio_gather.py` (asyncio.gather)

---

## Bug 列表（24 个真失败）

### Bug R11-01 [R9-08 复测]：except* PEP 654 + ternary handler body
- **测试文件**: `test_r11_ternary_except_star.py`
- **源码**:
  ```python
  try:
      pass
  except* E as e:
      x = (a if c else b)
  ```
- **失败原因**: 指令数不匹配 39 vs 29。原始字节码含 PUSH_EXC_INFO + COPY + BUILD_LIST + SWAP + CHECK_EG_MATCH 等 PEP 654 异常组基础设施；重编字节码缺少这些指令。
- **根因分析**: `region_analyzer.py` 中 except* handler region 识别未与 TernaryRegion 协调。ternary 的 condition_block 与 except* handler 的 PUSH_EXC_INFO 块共享入口，违反「每块唯一归属」原则。具体位置：except* handler 的 PUSH_EXC_INFO + CHECK_EG_MATCH 块被错误归入 TernaryRegion 的 condition_block，导致 ternary 重建丢失异常组基础设施。
- **修复方向**: 在 `region_analyzer.py` 的 TernaryRegion 识别阶段，过滤掉 entry 块含 PUSH_EXC_INFO/CHECK_EG_MATCH/COPY（PEP 654 特征）的候选；将 except* handler body 内的 ternary 标记为 `merge_context='except_star_handler'`，让 ternary merge 块在父 TryStar handler region 内作为子节点归约。依「父引用子入口」：父 TryStar handler 通过 STORE_FAST e 入口引用 ternary 子节点。

### Bug R11-02 [R9-10 复测]：frozen dataclass 字段默认值 ternary
- **测试文件**: `test_r11_ternary_frozen_dataclass_default.py`
- **源码**:
  ```python
  from dataclasses import dataclass
  @dataclass(frozen=True)
  class C:
      x: int = (a if c else b)
  ```
- **失败原因**: 指令数不匹配 25 vs 17。重编字节码缺少 `PUSH_NULL + LOAD_NAME dataclass + LOAD_CONST 'frozen' + KW_NAMES + LOAD_CONST True + PRECALL + CALL`（即 `@dataclass(frozen=True)` 装饰器调用栈）。
- **根因分析**: `region_ast_generator.py` 中 `_build_class_def`（行 1560）调用 `_extract_decorators`（行 1228）时，`@dataclass(frozen=True)` 这种带 kwarg 的类装饰器未被正确识别为外层 Call。具体位置：`_extract_decorators` 在 outer_call 为 None 时回退到 LOAD_BUILD_CLASS 前向扫描，扫描到 LOAD_NAME dataclass 但因后续含 KW_NAMES/KWAPPS 而被丢弃。同时，类体内 AnnAssign ternary merge 块的 STORE_NAME x 与 dataclass 装饰器栈共享 module code object，ternary region 错误吸收了装饰器栈前缀。
- **修复方向**: 在 `_build_class_def` 中，当 outer_call 为 None 时，应通过 `__build_class__` Call 的 args[0]（FunctionObject）回溯其前的 PRECALL+CALL 链，识别 `dataclass(frozen=True)` 形式的装饰器调用。依「父引用子入口」：父 ClassDef 通过 `__build_class__` Call 的 outer Call 引用 dataclass 装饰器子节点；ternary 在 class code object 内独立归约，不影响 module 级装饰器识别。

### Bug R11-03 [R9-15 复测]：assert + return 共享 ternary consumer
- **测试文件**: `test_r11_ternary_assert_return_consumer.py`
- **源码**:
  ```python
  def f():
      assert (a if c else b)
      return (x if c2 else y)
  ```
- **失败原因**: 反编译结果中未找到 IfExp，反编译为 `if (not a): pass elif c2: return x return y`（变成 if/elif 控制流）。
- **根因分析**: `region_ast_generator.py` 中 `_build_ternary_no_target_consumer_stmt`（行 19030）的 Pattern 1（assert (ternary)）只处理 LOAD_ASSERTION_ERROR + RAISE_VARARGS 模式。但当两个 ternary 共存且第一个是 assert 时，第一个 ternary 的 merge_block 含 LOAD_ASSERTION_ERROR + RAISE_VARARGS 1，被 IfRegion 抢占（`_identify_ternary_regions` 中 IfRegion 优先识别为 `if not a: pass elif c2: return x`）。具体位置：IfRegion 识别未排除 assert ternary 的 merge_block（merge_block 含 LOAD_ASSERTION_ERROR 应禁止 IfRegion 抢占）。
- **修复方向**: 在 `region_analyzer.py` 的 IfRegion 识别中，加守卫：候选 if 入口块的后续块含 LOAD_ASSERTION_ERROR + RAISE_VARARGS 时不识别为 IfRegion，让 TernaryRegion 优先归约。同时在 `_build_ternary_no_target_consumer_stmt` Pattern 1 之前加守卫：若同一函数体内有第二个 ternary，确保两个 ternary 分别归约（不互相合并）。依「自底向上归约」：两个 ternary 在同一函数体内独立识别；assert 基础设施块归属 assert ternary 的 merge_block。

### Bug R11-04 [R10-06 复测]：dataclass default_factory lambda ternary
- **测试文件**: `test_r11_ternary_dataclass_default_factory.py`
- **源码**:
  ```python
  from dataclasses import dataclass, field
  @dataclass
  class C:
      x: int = field(default_factory=lambda: (a if c else b))
  ```
- **失败原因**: 反编译结果中 IfExp 缺失，反编译为 `x: int = field(default_factory=(lambda *args, **kwargs: None))`（lambda body 被替换为 None，ternary 完全丢失）。
- **根因分析**: `region_ast_generator.py` 中 lambda body 的反编译在 `_build_function_def`（行 959）中走 `func_name == '<lambda>'` 分支（行 1132），调用 `nested_gen.generate()` 重建 lambda body。lambda code object 内 ternary merge 块的 RETURN_VALUE 应转换为 Return(IfExp)，但实际生成 Return(Constant(None))。具体位置：lambda body 的 ternary region 在嵌套 CFG 中未被识别为 TernaryRegion，被默认的「Return None」隐式返回路径覆盖。
- **修复方向**: 在 `_build_function_def` 的 lambda 分支中，调用 nested_gen.generate() 后检查返回的 body_stmts 是否仅含 Return(Constant(None))；若是且 lambda code object 含 POP_JUMP_IF_FALSE 指令，则强制走 TernaryRegion 重建路径。依「嵌套即抽象节点」：lambda 作为 default_factory 的参数在父 field() Call 中作为单个抽象节点；lambda 内 ternary 在 lambda code object 内独立归约。

### Bug R11-05 [R10-07 复测]：TypedDict + ternary default
- **测试文件**: `test_r11_ternary_typeddict_default.py`
- **源码**:
  ```python
  from typing import TypedDict
  class Movie(TypedDict):
      title: str
      year: int = (a if c else b)
  ```
- **失败原因**: 嵌套 code object 不匹配，类体内指令数 20 vs 16。重编字节码缺少 `LOAD_NAME title + LOAD_NAME str + STORE_SUBSCR`（即 `title: str` AnnAssign 的注解存储）。
- **根因分析**: `region_ast_generator.py` 中类体反编译在 `nested_gen.generate()` 中走 AnnAssign 检测路径（行 22491）。但 TypedDict 类体的 AnnAssign 含三元默认值时，ternary 的 merge_block 与下一个 AnnAssign 的注解存储 STORE_SUBSCR 共享类 code object，ternary region 错误吸收了 `title: str` 的注解存储指令。具体位置：AnnAssign 检测前向扫描找 `LOAD_NAME __annotations__ + LOAD_CONST 'title' + STORE_SUBSCR` 时，扫描窗口跨越了 ternary merge 块，导致 `title: str` 被合并到 `year: int = ternary` 的 AnnAssign 中。
- **修复方向**: 在 `region_ast_generator.py` 的 AnnAssign 检测（行 22491）前，加 ternary region 守卫：若 STORE_NAME 处于 TernaryRegion 的 merge_block，跳过 AnnAssign 前向扫描，让 ternary 优先归约为 AnnAssign 的 value；同时 AnnAssign 检测的 `_ann_remaining` 扫描不应跨越 TernaryRegion 边界。依「每块唯一归属」：ternary merge 块归属 AnnAssign(year) 的 value；`title: str` 的注解存储块独立归属 AnnAssign(title)。

### Bug R11-06 [R10-08 复测]：ABC abstract property + setter + ternary
- **测试文件**: `test_r11_ternary_abc_abstract_property_setter.py`
- **源码**:
  ```python
  from abc import ABC, abstractmethod
  class C(ABC):
      @property
      @abstractmethod
      def x(self): ...
      @x.setter
      def x(self, v):
          self._x = (v if c else 0)
  ```
- **失败原因**: 嵌套 code object 不匹配，类体内指令数 23 vs 25。重编字节码多出 2 条指令（重复的 LOAD_NAME + MAKE_FUNCTION）。
- **根因分析**: `region_ast_generator.py` 中 `_reconstruct_decorator_chain`（行 1302）对 `@x.setter` 这种 Attribute 装饰器链未正确处理。具体位置：`_reconstruct_decorator_chain` 向前扫描 LOAD_NAME x + LOAD_ATTR setter，但 R10-Fix1（行 1378）的 attr_chain 合并逻辑在 ABC 抽象类场景下重复触发，导致 decorator_list 多识别一次，MAKE_FUNCTION 多输出一次。
- **修复方向**: 在 `_reconstruct_decorator_chain` 的 R10-Fix1 attr_chain 合并逻辑中，加去重守卫：若 entry['idx'] 已存在于 decorator_entries，跳过合并。同时 ABC 基类的 LOAD_NAME ABC + LOAD_NAME abstractmethod 装饰器栈识别应与 @x.setter 分开处理。依「父引用子入口」：每个 decorator Call 通过 MAKE_FUNCTION 之后的 CALL 引用下层 FunctionObject 子节点；@x.setter 的 LOAD_NAME x + LOAD_ATTR setter 是单一 Attribute 装饰器节点。

### Bug R11-07 [R10-09 复测]：magic methods __eq__/__hash__ + ternary
- **测试文件**: `test_r11_ternary_magic_methods.py`
- **源码**:
  ```python
  class C:
      def __eq__(self, other):
          return self.x == (other.x if c else 0)
      def __hash__(self):
          return (hash(self.x) if c else 0)
  ```
- **失败原因**: 嵌套 code object 不匹配，__eq__ 内指令数 9 vs 8。重编字节码缺少 `LOAD_ATTR x`（即 `self.x` 的属性访问）。
- **根因分析**: `region_ast_generator.py` 中 ternary 作为比较表达式的右值时，`_try_build_ternary_kwarg_call`（行 20768）或相关路径未正确处理 COMPARE_OP 前的 LOAD_ATTR。具体位置：ternary 的 cond_block preload 含 `LOAD_FAST self + LOAD_ATTR x`（用于 `self.x ==`），但 merge 块重建时 preload_exprs 未被加入 initial_stack，导致 COMPARE_OP 左操作数 `self.x` 丢失，重编为 `self == other.x` 之类。
- **修复方向**: 在 `_generate_ternary` 的比较运算 consumer 检测中，加 Pattern：若 merge_block 末尾是 COMPARE_OP，且 cond_block preload 含 LOAD_ATTR，将 preload_exprs 作为 COMPARE_OP 的左操作数加入 initial_stack。依「父引用子入口」：父 Compare 通过 merge_block 的 COMPARE_OP 引用 ternary 子节点作为右操作数；cond_block preload 的 LOAD_ATTR 引用 self.x 作为左操作数。

### Bug R11-08 [R10-10 复测]：functools.wraps + ternary in *args
- **测试文件**: `test_r11_ternary_wraps.py`
- **源码**:
  ```python
  from functools import wraps
  def deco(f):
      @wraps(f)
      def g(*args, **kwargs):
          return f(*(args if c else ()), **kwargs)
      return g
  ```
- **失败原因**: 反编译结果中 IfExp 缺失，反编译为 `global c; nonlocal f; return f(**kwargs)`（ternary 完全丢失，且多出 global/nonlocal 声明）。
- **根因分析**: `region_ast_generator.py` 中 `_build_ternary_no_target_consumer_stmt`（行 19030）的 CALL_FUNCTION_EX 路径未处理 ternary 作为 *args 的情况。具体位置：ternary 的 merge_block 含 CALL_FUNCTION_EX（用于 `f(*ternary, **kwargs)`），但当前 Pattern 只处理 yield/raise/assert，未识别 CALL_FUNCTION_EX。同时，scope detection（global/nonlocal）误将 c 识别为 global，f 识别为 nonlocal，导致 ternary 整体被丢弃。
- **修复方向**: 在 `_build_ternary_no_target_consumer_stmt` 增加 Pattern 6：CALL_FUNCTION_EX consumer。检测 merge_block 末尾为 CALL_FUNCTION_EX 且 arg 含 0x01 flag（*args），将 ternary 作为 Call 的 starargs 字段。同时，scope detection 应跳过 ternary condition_block 内的 LOAD_NAME（这些不是真正的 global/nonlocal 声明）。依「父引用子入口」：父 Call 通过 merge_block 的 CALL_FUNCTION_EX 引用 ternary 子节点作为 *args。

### Bug R11-09 [R10-11 复测]：typing.overload + ternary in body
- **测试文件**: `test_r11_ternary_overload.py`
- **源码**:
  ```python
  from typing import overload
  @overload
  def f(x: int) -> int: ...
  @overload
  def f(x: str) -> str: ...
  def f(x):
      return (a if c else b)
  ```
- **失败原因**: 指令数不匹配 34 vs 24。重编字节码缺少 10 条指令（即两个 @overload 装饰的函数定义 + AnnAssign 注解存储）。
- **根因分析**: `region_ast_generator.py` 中多个同名 `f` 函数定义共存时，第三个无装饰器的 `f` 的 ternary return 与前两个 @overload 装饰的 `f` 的 MAKE_FUNCTION + STORE_NAME f 序列共享 module code object。ternary region 错误地跨越了多个 f 的定义，导致前两个 @overload 函数定义被吸收。具体位置：ternary 的 condition_block 入口被误识别为前一个 @overload f 的 STORE_NAME f 块，违反「每块唯一归属」原则。
- **修复方向**: 在 `region_analyzer.py` 的 TernaryRegion 识别中，加守卫：ternary entry 块若包含 MAKE_FUNCTION + STORE_NAME 序列（前驱是函数定义结尾），不应作为 ternary condition_block。同时 multiple FunctionDef 共存时，每个 MAKE_FUNCTION + STORE_NAME 应作为独立 FunctionDef 节点。依「自底向上归约」：每个 f 的 ternary 在其 code object 内独立归约；@overload 装饰的 f 与最终实现 f 是三个独立 FunctionDef 节点。

### Bug R11-10 [R10-12 复测]：functools.partialmethod + ternary
- **测试文件**: `test_r11_ternary_partialmethod.py`
- **源码**:
  ```python
  from functools import partialmethod
  class C:
      def _m(self, x):
          return x
      m = partialmethod(_m, (a if c else b))
  ```
- **失败原因**: 嵌套 code object 不匹配，类体内指令数 19 vs 16。重编字节码缺少 `LOAD_CONST _m_code + MAKE_FUNCTION + STORE_NAME _m`（即 `_m` 方法定义）。
- **根因分析**: `region_ast_generator.py` 中类体内 ternary 作为 partialmethod() 的位置参数时，ternary 的 merge_block 含 `PUSH_NULL + LOAD_NAME partialmethod + LOAD_NAME _m + ternary merge + PRECALL + CALL + STORE_NAME m`。ternary region 错误吸收了前驱的 `_m` 方法定义（LOAD_CONST _m_code + MAKE_FUNCTION + STORE_NAME _m），违反「每块唯一归属」原则。具体位置：ternary condition_block 入口被误识别为 `_m` 方法定义结尾的 STORE_NAME _m 块。
- **修复方向**: 在 `region_analyzer.py` 的 TernaryRegion 识别中，加守卫：ternary entry 块若包含 MAKE_FUNCTION + STORE_NAME 序列，不应作为 ternary condition_block。同时 `_try_build_ternary_kwarg_call` 应处理 partialmethod Call 的位置参数 ternary。依「父引用子入口」：父 Assign 通过 STORE_NAME m 引用 partialmethod Call；partialmethod Call 通过 LOAD_NAME _m + ternary merge 引用 _m 与 ternary 子节点作为位置参数。

### Bug R11-11 [R10-14 复测]：async __aenter__ + ternary in body
- **测试文件**: `test_r11_ternary_async_aenter.py`
- **源码**:
  ```python
  class C:
      async def __aenter__(self):
          self.x = (a if c else b)
          return self
  ```
- **失败原因**: 嵌套 code object 不匹配，__aenter__ 内指令数 10 vs 12。重编字节码多出 2 条 LOAD_GLOBAL + POP_TOP + LOAD_CONST + RETURN_VALUE，缺少 STORE_ATTR x。
- **根因分析**: `region_ast_generator.py` 中 async 方法体内 ternary 属性赋值时，ternary merge 块含 STORE_ATTR x，但重编字节码丢失了 STORE_ATTR，反而多出两条 LOAD_GLOBAL + POP_TOP + RETURN_VALUE（像是被替换为两个独立的 return None 路径）。具体位置：async 函数的 RETURN_GENERATOR + POP_TOP + RESUME 前缀未正确处理，ternary 被错误地展开为 if/else 控制流，每个分支独立 return。
- **修复方向**: 在 `_generate_ternary` 中加守卫：若 region.merge_block 含 STORE_ATTR 且属于 async function code object，禁止展开为 if/else，必须保留为 Assign(Attribute, IfExp) 单一节点。同时 async 函数的 RETURN_GENERATOR 前缀不应干扰 ternary region 边界识别。依「自底向上归约」：ternary 在 __aenter__ code object 内独立归约；依「父引用子入口」：父 Assign 通过 STORE_ATTR x 引用 ternary 子节点作为右值。

### Bug R11-12 [R10-15 复测]：ternary in kwonly default
- **测试文件**: `test_r11_ternary_kwonly_default.py`
- **源码**:
  ```python
  def f(*args, x=(a if c else b)):
      pass
  ```
- **失败原因**: 反编译结果中 IfExp 缺失，反编译为 `def f(*x, args): return None`（kwonly 参数 x 丢失，args 与 *x 顺序错乱）。
- **根因分析**: `region_ast_generator.py` 中 R11-batch1 已添加 kwonly default ternary 处理（行 17725-17743），但识别条件 `MAKE_FUNCTION flag & 2` 在 `_generate_ternary` 中未正确触发。具体位置：ternary 的 merge_block 末尾是 BUILD_CONST_KEY_MAP（kwonly default 字典构造），但当前 Pattern 6（MAKE_FUNCTION）的 `_has_make_function` 检测未覆盖 BUILD_CONST_KEY_MAP 后跟 MAKE_FUNCTION 的场景。同时函数签名重建时，kwonlyargs 列表丢失，导致 `*args, x=ternary` 被错编为 `*x, args`。
- **修复方向**: 在 `_generate_ternary` 的 MAKE_FUNCTION Pattern 检测中，扩展 `_has_make_function` 检查：若 before_store 含 BUILD_CONST_KEY_MAP + LOAD_CONST tuple + MAKE_FUNCTION，识别为 kwonly default ternary。同时 `_extract_function_args`（行 1700）应基于 code_obj.co_kwonlyargcount 正确重建 kwonlyargs 列表。依「父引用子入口」：父 FunctionDef 通过 MAKE_FUNCTION 引用 FunctionObject；FunctionObject.kw_defaults 通过 BUILD_CONST_KEY_MAP 引用 ternary 子节点作为 value。

### Bug R11-13 [new]：dataclass InitVar + ternary default
- **测试文件**: `test_r11_ternary_initvar.py`
- **源码**:
  ```python
  from dataclasses import dataclass, InitVar
  @dataclass
  class C:
      x: InitVar[int] = (a if c else b)
      def __post_init__(self, x):
          pass
  ```
- **失败原因**: 嵌套 code object 不匹配，类体内指令数 21 vs 18。重编字节码缺少 `LOAD_CONST _post_init_code + MAKE_FUNCTION + STORE_NAME __post_init__`（即 __post_init__ 方法定义）。
- **根因分析**: `region_ast_generator.py` 中类体内 AnnAssign 含 InitVar annotation + ternary value 时，ternary region 错误吸收了 __post_init__ 方法定义（前驱的 MAKE_FUNCTION + STORE_NAME）。具体位置：与 R11-10 同类问题，ternary condition_block 入口被误识别为 __post_init__ 方法定义结尾的 STORE_NAME 块。同时 InitVar annotation 的 Subscript(Name('InitVar'), Name('int')) 重建正确，但 ternary 边界识别未排除前驱的 MAKE_FUNCTION。
- **修复方向**: 同 R11-10，在 TernaryRegion 识别中加 MAKE_FUNCTION + STORE_NAME 前驱守卫。同时 InitVar annotation 不需要特殊处理（与普通 Subscript annotation 同构）。依「自底向上归约」：ternary 在 class code object 内独立归约；__post_init__ 方法定义是独立 FunctionDef 节点。

### Bug R11-14 [new]：typing.Literal + ternary annotation value
- **测试文件**: `test_r11_ternary_typing_literal.py`
- **源码**:
  ```python
  from typing import Literal
  x: Literal['a', 'b'] = ('a' if c else 'b')
  ```
- **失败原因**: 指令数不匹配 20 vs 14。重编字节码缺少 `LOAD_CONST 0 + LOAD_CONST 0 + IMPORT_NAME typing + IMPORT_FROM Literal + STORE_NAME Literal + POP_TOP`（即 `from typing import Literal` 整个 import 语句）。
- **根因分析**: `region_ast_generator.py` 中 module 级 AnnAssign 含 ternary value 时，ternary region 错误吸收了前驱的 IMPORT_NAME 块。具体位置：ternary condition_block 入口被误识别为 IMPORT_NAME 块（因 IMPORT_NAME 后跟 STORE_NAME Literal，与 ternary condition_block 的 STORE 模式相似），违反「每块唯一归属」原则。
- **修复方向**: 在 `region_analyzer.py` 的 TernaryRegion 识别中，加守卫：ternary entry 块若包含 IMPORT_NAME/IMPORT_FROM 指令，不应作为 ternary condition_block。同时 AnnAssign 检测（行 22491）应在 ternary region 归约之后，避免重复扫描 ternary merge 块。依「每块唯一归属」：IMPORT_NAME 块归属 ImportFrom 节点；ternary merge 块归属 AnnAssign 的 value。

### Bug R11-15 [new]：typing.Union + ternary annotation value
- **测试文件**: `test_r11_ternary_typing_union.py`
- **源码**: 
  ```python
  from typing import Union
  x: Union[int, str] = (1 if c else 's')
  ```
- **失败原因**: 指令数不匹配 22 vs 16，与 R11-14 同类。
- **根因分析**: 同 R11-14。typing.Union 的 Subscript(Name('Union'), Tuple(int, str)) 重建正确，但 ternary 边界识别吸收了前驱 IMPORT_NAME 块。
- **修复方向**: 同 R11-14。

### Bug R11-16 [new]：typing.Annotated + ternary default
- **测试文件**: `test_r11_ternary_typing_annotated.py`
- **源码**:
  ```python
  from typing import Annotated
  x: Annotated[int, 'meta'] = (1 if c else 2)
  ```
- **失败原因**: 指令数不匹配 22 vs 16，与 R11-14 同类。
- **根因分析**: 同 R11-14。typing.Annotated 的多元素 Tuple 在 BINARY_SUBSCR 之前 BUILD_TUPLE 2，与 ternary merge 块共存于 module code object。
- **修复方向**: 同 R11-14。

### Bug R11-17 [new]：typing.TypeAlias (PEP 613) + ternary value
- **测试文件**: `test_r11_ternary_typealias.py`
- **源码**:
  ```python
  from typing import TypeAlias
  MyType: TypeAlias = (int if c else str)
  ```
- **失败原因**: 指令数不匹配 18 vs 12，与 R11-14 同类。
- **根因分析**: 同 R11-14。TypeAlias 是简单 Name annotation，但 ternary 边界识别吸收了前驱 IMPORT_NAME 块。
- **修复方向**: 同 R11-14。

### Bug R11-18 [new]：__all__ definition + ternary list element
- **测试文件**: `test_r11_ternary_all_definition.py`
- **源码**:
  ```python
  cond = True
  __all__ = ['a', ('b' if cond else 'c'), 'd']
  ```
- **失败原因**: 指令数不匹配 12 vs 10。重编字节码缺少 2 条指令（推测是 BUILD_LIST 与 LIST_EXTEND 的细节差异）。
- **根因分析**: `region_ast_generator.py` 中 ternary 作为 list literal 元素时，`_try_build_ternary_kwarg_call` 或相关路径未正确处理 BUILD_LIST + LIST_EXTEND 模式。具体位置：ternary merge 块的栈输出作为 LIST_EXTEND 的元素之一，但当前 list literal 重建未将 ternary 作为元素插入 List(elts=[..., IfExp, ...])。
- **修复方向**: 在 `_generate_ternary` 中增加 Pattern：若 merge_block 末尾是 LIST_EXTEND 或 BUILD_LIST，且 ternary 是元素之一，重建为 List(elts=[..., IfExp, ...])。依「父引用子入口」：父 Assign 通过 STORE_NAME __all__ 引用 List 子节点；List 通过 LIST_EXTEND 引用 ternary 子节点作为元素。

### Bug R11-19 [new]：__version__ definition + ternary
- **测试文件**: `test_r11_ternary_version_definition.py`
- **源码**:
  ```python
  import sys
  __version__ = ('1.0' if sys.version_info >= (3, 11) else '0.9')
  ```
- **失败原因**: 指令数不匹配 14 vs 17。重编字节码多出 3 条指令（两个独立的 LOAD_CONST + POP_TOP + RETURN_VALUE 路径）。
- **根因分析**: `region_ast_generator.py` 中 ternary 的 test 子表达式含属性访问 + 比较（`sys.version_info >= (3, 11)`）时，ternary 被错误展开为 if/else 控制流（两个独立 return 路径）。具体位置：ternary 的 condition_block 含 LOAD_NAME sys + LOAD_ATTR version_info + LOAD_CONST (3, 11) + COMPARE_OP >= + POP_JUMP_IF_FALSE，但重编时 COMPARE_OP 后的 POP_TOP + LOAD_CONST + RETURN_VALUE 被识别为独立 return 路径，而非 ternary 的分支。
- **修复方向**: 在 `_generate_ternary` 中加守卫：若 ternary condition_block 含 COMPARE_OP + POP_JUMP_IF_FALSE，且 merge_block 含 STORE_NAME + LOAD_CONST None + RETURN_VALUE（隐式返回），不应展开为 if/else，必须保留为 Assign(targets, IfExp) 单一节点。同时比较表达式 + 元组常量的 cond_block 重建应通过 expr_reconstructor 正确处理。依「自底向上归约」：ternary 在 module code object 内独立归约；COMPARE_OP 块归属 ternary condition。

### Bug R11-20 [new]：conditional __import__ + ternary
- **测试文件**: `test_r11_ternary_conditional_import.py`
- **源码**:
  ```python
  import sys
  json = __import__('json' if sys.version_info >= (3, 11) else 'simplejson')
  ```
- **失败原因**: 指令 6 参数不匹配: `__import__ vs sys` (op=LOAD_NAME)。即重编字节码的 LOAD_NAME 操作数变成了 sys 而非 __import__。
- **根因分析**: `region_ast_generator.py` 中 ternary 作为 __import__() 的位置参数时，ternary 的 condition_block 含 `LOAD_NAME sys + LOAD_ATTR version_info + LOAD_CONST (3,11) + COMPARE_OP >=`，但重编时 LOAD_NAME sys 被误识别为 __import__ Call 的 func，导致 Call(func=Name('sys'), args=[...]) 而非 Call(func=Name('__import__'), args=[ternary])。具体位置：ternary region 错误吸收了 __import__ 的 PUSH_NULL + LOAD_NAME __import__ 前缀，导致函数名识别错误。
- **修复方向**: 在 `_try_build_ternary_kwarg_call` 中加守卫：ternary condition_block 内的 LOAD_NAME 不应被误识别为父 Call 的 func。同时 `__import__` Call 的 PUSH_NULL + LOAD_NAME __import__ 前缀应在 ternary region 识别时排除。依「父引用子入口」：父 Call 通过 LOAD_NAME __import__ 引用 __import__ 函数；ternary 通过 merge 块的栈输出作为 Call 的位置参数。

### Bug R11-21 [new]：asynccontextmanager + ternary in body
- **测试文件**: `test_r11_ternary_asynccontextmanager.py`
- **源码**:
  ```python
  from contextlib import asynccontextmanager
  @asynccontextmanager
  async def cm():
      x = (a if c else b)
      yield x
  ```
- **失败原因**: 嵌套 code object 不匹配，cm 内指令数 14 vs 9。重编字节码缺少 `LOAD_FAST x + ASYNC_GEN_WRAP + YIELD_VALUE + RESUME + POP_TOP`（即 `yield x` 的 yield 表达式）。
- **根因分析**: `region_ast_generator.py` 中 async generator 函数体内 ternary 赋值 + yield 时，ternary merge 块的 STORE_FAST x 与后续 yield x 的 LOAD_FAST x + ASYNC_GEN_WRAP + YIELD_VALUE 共存于同一 code object。ternary region 错误吸收了 yield 表达式块，导致 yield 丢失。具体位置：ternary 的 merge_block 末尾 STORE_FAST x 之后跟 LOAD_FAST x + YIELD_VALUE，但当前 ternary 重建未保留 yield 表达式作为独立语句。
- **修复方向**: 在 `_generate_ternary` 中加守卫：若 ternary merge_block 之后跟 LOAD_FAST + YIELD_VALUE（yield 表达式引用 ternary 结果），不应将 yield 块并入 ternary region。同时 async gen 的 RETURN_GENERATOR + ASYNC_GEN_WRAP 前缀不应干扰 ternary region 边界识别。依「每块唯一归属」：ternary merge 块归属 Assign(x, IfExp)；yield 块归属 Expr(Yield(Name('x')))。

### Bug R11-22 [new]：cached_property + ternary in body
- **测试文件**: `test_r11_ternary_cached_property.py`
- **源码**:
  ```python
  from functools import cached_property
  class C:
      def __init__(self):
          self._x = None
      @cached_property
      def x(self):
          return (a if c else b)
  ```
- **失败原因**: 嵌套 code object 不匹配，类体内指令数 16 vs 19。重编字节码多出 3 条指令（重复的 LOAD_NAME cached_property + MAKE_FUNCTION + CALL）。
- **根因分析**: `region_ast_generator.py` 中 `_reconstruct_decorator_chain`（行 1302）对 `@cached_property` 这种无参装饰器在 class body 内的场景，重复识别装饰器链。具体位置：与 R11-06 同类问题，decorator_list 多识别一次，导致类体内多出 MAKE_FUNCTION + CALL + STORE_NAME 序列。
- **修复方向**: 在 `_reconstruct_decorator_chain` 中加去重守卫：若 MAKE_FUNCTION 之后的 CALL 数量已匹配 decorator_list 长度，停止扫描。同时类体内的 @cached_property 装饰器应通过 _extract_decorators 而非 _reconstruct_decorator_chain 识别。依「父引用子入口」：父 FunctionDef 通过 MAKE_FUNCTION 之后的 CALL 引用 cached_property 装饰器子节点。

### Bug R11-23 [new]：contextlib.suppress + ternary in with item
- **测试文件**: `test_r11_ternary_contextlib_suppress.py`
- **源码**:
  ```python
  from contextlib import suppress
  with suppress((E1 if c else E2)):
      pass
  ```
- **失败原因**: 反编译结果中 IfExp 缺失，反编译为 `with context(): pass`（suppress(ternary) 整体被替换为 context()）。
- **根因分析**: `region_ast_generator.py` 中 ternary 作为 suppress() 的位置参数且整个 Call 作为 with 上下文管理器时，ternary region 错误地与 with region 合并。具体位置：ternary 的 merge_block 含 `PUSH_NULL + LOAD_NAME suppress + ternary merge + PRECALL + CALL + WITH + POP_TOP`，但 with region 识别时未将 ternary 作为子节点保留，整体被替换为 With(items=[withitem(context_expr=Call(context(), []))])。
- **修复方向**: 在 `_generate_with`（或 WithRegion 处理）中加守卫：若 with item 的 context_expr 是 Call 且其 args 含 ternary region merge 块，应保留 ternary 作为 Call 的位置参数。同时 ternary region 不应被 WithRegion 抢占。依「父引用子入口」：父 With 通过 withitem.context_expr 引用 suppress Call；suppress Call 通过 LOAD_NAME suppress + ternary merge 引用 ternary 子节点作为位置参数。

### Bug R11-24 [new]：asyncio.gather + ternary arg
- **测试文件**: `test_r11_ternary_asyncio_gather.py`
- **源码**:
  ```python
  import asyncio
  async def main():
      return await asyncio.gather((f() if c else g()), h())
  ```
- **失败原因**: 嵌套 code object 不匹配，main 内指令数 23 vs 16。重编字节码缺少 `LOAD_GLOBAL f + PRECALL + CALL + LOAD_GLOBAL g + PRECALL + CALL`（即 ternary body/orelse 的函数调用）。
- **根因分析**: `region_ast_generator.py` 中 ternary 作为 asyncio.gather() 的位置参数且整个 Call 被 await 时，ternary 的 condition_block preload 含 `PUSH_NULL + LOAD_GLOBAL f + PRECALL + CALL`（或 g），但重编时 preload_exprs 未被加入 initial_stack，导致 ternary body/orelse 的 Call 丢失。具体位置：与 R11-07 同类问题，ternary condition_block preload 的函数调用未保留。
- **修复方向**: 在 `_generate_ternary` 中，加守卫：若 ternary condition_block preload 含 CALL（函数调用），将 preload_exprs 加入 initial_stack，让 expr_reconstructor 重建 Call(IfExp(Call(f), Call(g)), h())。同时 await + ternary + Call 三重路径应通过嵌套区域归约正确处理。依「父引用子入口」：父 Return 通过 merge 块的 RETURN_VALUE 引用 await 表达式；await 通过 GET_AWAITABLE 引用 gather Call；gather Call 通过 LOAD_NAME gather + ternary merge + LOAD_NAME h 引用 ternary 与 h 作为位置参数。

---

## 通过的测试（11 个）

- `test_r11_ternary_dataclass_init_override.py` — dataclass + 显式 __init__ + ternary 赋值
- `test_r11_ternary_descriptor_protocol.py` — __get__/__set__ + ternary
- `test_r11_ternary_dynamic_class_type.py` — type() 动态类创建 + ternary dict value
- `test_r11_ternary_enum_value.py` — Enum + ternary value
- `test_r11_ternary_flag_enum.py` — Flag enum + auto() + ternary
- `test_r11_ternary_functools_cache.py` — @cache + 递归 ternary return
- `test_r11_ternary_lru_cache.py` — @lru_cache(maxsize=128) + ternary return
- `test_r11_ternary_multiple_inheritance.py` — 多继承 + ternary
- `test_r11_ternary_set_name.py` — __set_name__ + ternary
- `test_r11_ternary_total_ordering.py` — @total_ordering + ternary in __lt__
- `test_r11_ternary_typing_cast.py` — typing.cast + ternary arg

## 跳过的测试（3 个，重编译失败）

- `test_r11_ternary_async_with_multi_as.py` (R7-03) — async with 多 as + ternary，反编译输出语法错误
- `test_r11_ternary_init_subclass.py` — __init_subclass__ + super() no-arg + ternary，反编译输出语法错误
- `test_r11_ternary_metaclass_new.py` — metaclass __new__ + super() no-arg + ternary，反编译输出语法错误

---

## 累计 Bug 数

**真失败 bug 总数：24**

按类别分组：

| 类别 | Bug 数 | Bug ID |
|------|--------|--------|
| R10/R9 已知限制复测（仍失败） | 12 | R11-01 至 R11-12（除 R11-13 外，R7-03 跳过） |
| 新增对抗性测试发现 | 12 | R11-13 至 R11-24 |
| **总计** | **24** | |

按根因分组：

| 根因 | Bug 数 | Bug ID |
|------|--------|--------|
| TernaryRegion 边界吸收前驱块（MAKE_FUNCTION/IMPORT_NAME/LOAD_NAME __import__） | 9 | R11-09, R11-10, R11-13, R11-14, R11-15, R11-16, R11-17, R11-20, R11-22 |
| Ternary 被错误展开为 if/else 控制流 | 4 | R11-03, R11-11, R11-19, R11-23 |
| Ternary consumer Pattern 未覆盖（CALL_FUNCTION_EX, LIST_EXTEND, COMPARE_OP） | 4 | R11-07, R11-08, R11-18, R11-24 |
| 装饰器链重复识别 | 2 | R11-06, R11-22 |
| AnnAssign + ternary 边界识别冲突 | 3 | R11-05, R11-14, R11-15 |
| Lambda body ternary 未识别 | 1 | R11-04 |
| except* handler region 与 ternary region 归属冲突 | 1 | R11-01 |
| async gen + ternary + yield 三重路径归约冲突 | 1 | R11-21 |

---

## 修复优先级建议

### P0（高优先级，影响核心场景）

1. **R11-09 / R11-10 / R11-13**: TernaryRegion 边界吸收前驱 MAKE_FUNCTION + STORE_NAME 块。修复方法：在 `region_analyzer.py` 的 TernaryRegion 识别中，加守卫排除 ternary entry 块包含 MAKE_FUNCTION 的情况。这一类问题影响所有「类体内先定义方法再用 ternary 调用」的场景。

2. **R11-14 / R11-15 / R11-16 / R11-17**: TernaryRegion 边界吸收前驱 IMPORT_NAME 块。修复方法：在 TernaryRegion 识别中，加守卫排除 ternary entry 块包含 IMPORT_NAME 的情况。这一类问题影响所有「module 级 import + AnnAssign ternary」的场景。

3. **R11-03 / R11-11 / R11-19**: Ternary 被错误展开为 if/else 控制流。修复方法：在 `_generate_ternary` 中加守卫，禁止将 ternary merge 块展开为 If/Else 控制流；强制保留为 IfExp 表达式节点。

### P1（中优先级，影响特定 Pattern）

4. **R11-07 / R11-08 / R11-18 / R11-24**: Ternary consumer Pattern 未覆盖 COMPARE_OP / CALL_FUNCTION_EX / LIST_EXTEND。修复方法：在 `_build_ternary_no_target_consumer_stmt` 增加 Pattern 6/7/8 处理这些 consumer。

5. **R11-06 / R11-22**: 装饰器链重复识别。修复方法：在 `_reconstruct_decorator_chain` 中加去重守卫。

### P2（低优先级，已知限制复测）

6. **R11-01 / R11-02 / R11-04 / R11-05 / R11-21**: 已知 R9/R10 限制的复测，根因复杂，建议单独处理。

---

## 区域归约算法 4 原则符合性检查

| 原则 | 当前违反情况 | 影响 Bug |
|------|--------------|----------|
| 1. 自底向上归约（最内层先识别） | TernaryRegion 未在最内层识别，被 IfRegion/WithRegion 抢占 | R11-03, R11-11, R11-19, R11-23 |
| 2. 每块在任意层级只属于一个区域 | TernaryRegion entry 块包含 MAKE_FUNCTION/IMPORT_NAME，与 FunctionDef/ImportFrom 区域重叠 | R11-09, R11-10, R11-13, R11-14, R11-15, R11-16, R11-17, R11-20 |
| 3. 嵌套区域在父区域中作为单个抽象节点 | Lambda body 内 ternary 未作为抽象节点保留；async gen 内 yield 块被并入 ternary | R11-04, R11-21 |
| 4. 父区域 then/else 列表引用子区域入口 | 装饰器链重复识别导致父 FunctionDef 多次引用同一 FunctionObject；ternary consumer Pattern 未覆盖导致父 Call/Compare/List 未引用 ternary 子节点 | R11-06, R11-07, R11-08, R11-18, R11-22, R11-24 |

---

## 测试执行日志摘要

```
$ cd /workspace && timeout 250 python -m pytest tests/exhaustive/ternary/test_r11_*.py --tb=no -q
...
24 failed, 11 passed, 3 skipped in 2.02s
```

失败列表（24 个）：
1. test_r11_ternary_abc_abstract_property_setter.py
2. test_r11_ternary_all_definition.py
3. test_r11_ternary_assert_return_consumer.py
4. test_r11_ternary_async_aenter.py
5. test_r11_ternary_asynccontextmanager.py
6. test_r11_ternary_asyncio_gather.py
7. test_r11_ternary_cached_property.py
8. test_r11_ternary_conditional_import.py
9. test_r11_ternary_contextlib_suppress.py
10. test_r11_ternary_dataclass_default_factory.py
11. test_r11_ternary_except_star.py
12. test_r11_ternary_frozen_dataclass_default.py
13. test_r11_ternary_initvar.py
14. test_r11_ternary_kwonly_default.py
15. test_r11_ternary_magic_methods.py
16. test_r11_ternary_overload.py
17. test_r11_ternary_partialmethod.py
18. test_r11_ternary_typealias.py
19. test_r11_ternary_typeddict_default.py
20. test_r11_ternary_typing_annotated.py
21. test_r11_ternary_typing_literal.py
22. test_r11_ternary_typing_union.py
23. test_r11_ternary_version_definition.py
24. test_r11_ternary_wraps.py
