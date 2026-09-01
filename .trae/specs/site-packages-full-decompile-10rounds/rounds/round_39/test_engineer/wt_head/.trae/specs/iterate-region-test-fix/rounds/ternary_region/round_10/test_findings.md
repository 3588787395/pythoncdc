# Ternary Region Round 10 — Test Findings

## 概览

- **基线**：R9 已完成（commit fe8feab），11 个 bug 修复，7 个已知限制（R7-03, R9-08, R9-10, R9-12, R9-13, R9-14, R9-15, R9-16）尚未修复
- **测试时间**：2026-07-21
- **创建测试文件数**：28
- **R10 真失败 bug 数**：15 个（新增对抗性测试发现）
- **R9 已知限制仍失败**：7 个失败 + 1 个被跳过（async_with_multi_as，反编译输出含 `break outside loop`，是真 bug 但被测试框架 skipTest 掩盖）
- **累计确认 bug 数**：23 个（7 R9 仍失败 + 1 跳过 + 15 R10 新增）

测试统计：`15 failed, 13 passed in 1.27s`

---

## 第一部分：R9 已知限制回归验证（8 个，全部仍失败）

### Bug R9-10 [仍失败]：frozen dataclass field 默认值 ternary

- **测试文件**：`tests/exhaustive/ternary/test_r9_ternary_frozen_dataclass_default.py`
- **源码**：
  ```python
  from dataclasses import dataclass
  @dataclass(frozen=True)
  class C:
      x: int = (a if c else b)
  ```
- **期望**：`@dataclass(frozen=True)` 装饰器调用与 KW_NAMES + PRECALL + CALL 完整保留。
- **实际**：原始 25 条指令 vs 重编 17 条。重编丢失 `LOAD_NAME dataclass + LOAD_CONST True + KW_NAMES + PRECALL + CALL`（5 条），把 `@dataclass(frozen=True)` 退化为无装饰器类。`@dataclass(frozen=True)` 调用栈帧丢失。
- **根因分析**：`_build_class_def`（region_ast_generator.py:1512-1650）中 `_extract_decorators` 在识别带 KW_NAMES 的装饰器调用时未能保留整个 Call 节点。`@dataclass(frozen=True)` 的 KW_NAMES（'frozen',）+ LOAD_CONST True + PRECALL + CALL 被剥离，仅保留 LOAD_NAME dataclass 作装饰器名（甚至完全丢失）。`_extract_decorators`（line 1228-1300）未对 kwargs 进行单独处理。
- **修复方向**：在 `_extract_decorators` 中识别 `Call(func=Name('dataclass'), keywords=[keyword(arg='frozen', value=Constant(True))])` 模式，保留完整 Call 节点作为装饰器（依「父引用子入口」原则：装饰器 Call 通过 `__build_class__` Call 引用 ClassDef 子节点）。

### Bug R9-12 [仍失败]：property + setter + 双 ternary

- **测试文件**：`tests/exhaustive/ternary/test_r9_ternary_property_setter.py`
- **源码**：
  ```python
  class C:
      @property
      def x(self):
          return self._x if c else 0
      @x.setter
      def x(self, v):
          self._x = v if c2 else 0
  ```
- **期望**：`@x.setter` 装饰器中 `LOAD_NAME x + LOAD_ATTR setter` 链保留。
- **实际**：嵌套 code object 指令数 20 vs 19。重编丢失 `LOAD_NAME x; LOAD_ATTR setter`，把 `@x.setter` 退化为 `@setter` 占位符。
- **根因分析**：`_build_function_def`（line 959-1226）中 `_reconstruct_decorator_chain`（line 1302+）未识别 `x.setter` 这种 attribute decorator 模式（LOAD_NAME x + LOAD_ATTR setter）。当 decorator 调用栈帧中 FunctionObject 之前是 LOAD_ATTR 而非 LOAD_NAME，重建链断开。
- **修复方向**：扩展 `_reconstruct_decorator_chain` 识别 LOAD_NAME + LOAD_ATTR 序列作为 Attribute 装饰器（依「父引用子入口」：装饰器 Call 通过 LOAD_ATTR setter 引用 LOAD_NAME x 子节点）。

### Bug R9-13 [仍失败]：abstractmethod + ternary default arg

- **测试文件**：`tests/exhaustive/ternary/test_r9_ternary_abstractmethod.py`
- **源码**：
  ```python
  class C:
      @abstractmethod
      def m(self, x=(a if c else b)):
          pass
  ```
- **期望**：`@abstractmethod` 装饰器调用 `LOAD_NAME abstractmethod + MAKE_FUNCTION + PRECALL + CALL` 保留。
- **实际**：嵌套 code object 指令数 17 vs 14。重编丢失 `PRECALL + CALL` 两条指令，把 `@abstractmethod` 退化为无装饰器函数。
- **根因分析**：`_build_function_def` 中 decorator_list 重建（line 1191-1224）仅识别 Call 类型装饰器；`@abstractmethod`（无参）字节码为 LOAD_NAME abstractmethod + LOAD_CONST code + MAKE_FUNCTION + PRECALL + CALL，Call 重建时把无参调用识别为 Name，丢失 PRECALL+CALL。需要确认 `_reconstruct_decorator_chain`（line 1302+）是否处理无参装饰器调用。
- **修复方向**：在 `_reconstruct_decorator_chain` 中检测 MAKE_FUNCTION 后是否紧跟 PRECALL+CALL（无参装饰器调用），若是则保留 `Name('abstractmethod')` 作为装饰器（依「父引用子入口」：装饰器 Call 通过 MAKE_FUNCTION 之后的 CALL 引用 FunctionObject 子节点）。

### Bug R9-14 [仍失败]：class decorator 参数 ternary

- **测试文件**：`tests/exhaustive/ternary/test_r9_ternary_class_decorator_arg.py`
- **源码**：
  ```python
  @deco(a if c else b)
  class C:
      pass
  ```
- **期望**：`@deco(a if c else b)` 装饰器调用栈帧 `PUSH_NULL + LOAD_NAME deco + ternary merge + PRECALL + CALL` 完整保留，包裹 `__build_class__` Call。
- **实际**：原始 20 条 vs 重编 15 条。重编丢失 5 条：`PRECALL + CALL`（deco(ternary) 调用）+ `PRECALL + CALL`（deco(ternary)(C) 调用）。
- **根因分析**：`_build_class_def`（line 1512-1650）的 `_extract_decorators` 在 `outer_call` 是 `Call(func=__build_class__, args=[FunctionObject, 'C'])` 且最外层 `outer_call` 是 `Call(func=Call(deco, [ternary]), args=[__build_class__ Call])` 时，未识别两层嵌套 Call 的装饰器链。`_extract_decorators`（line 1268-1294）虽处理 Call func，但在 class def 场景下 outer_call 的 args 第一个是 __build_class__ Call（不是 FunctionObject），导致提前返回。
- **修复方向**：在 `_build_class_def` 中专门处理 `outer_call.func` 是 Call（带参装饰器）的情况，提取完整 `Call(deco, [ternary_expr])` 作为装饰器节点（依「父引用子入口」：装饰器 Call 通过 cond_block 的 deco 入口 + merge_block 的 CALL 引用 ternary 子节点）。

### Bug R9-15 [仍失败]：assert + return 共享 ternary consumer

- **测试文件**：`tests/exhaustive/ternary/test_r9_ternary_assert_return_consumer.py`
- **源码**：
  ```python
  def f():
      assert (a if c else b)
      return x if c2 else y
  ```
- **期望**：`assert (ternary)` + `return (ternary)` 两段保留。
- **实际**：反编译结果完全错误：
  ```python
  def f():
      if (not a):
          pass
      elif c2:
          return x
      return y
  ```
  ternary 表达式（IfExp）丢失，被退化为 if/elif/return 链。`assert (ternary)` 未识别为 Assert(test=IfExp)，`return ternary` 未识别为 Return(IfExp)。
- **根因分析**：`_build_ternary_no_target_consumer_stmt`（line 18734+）的 Pattern 1（assert (ternary)）通过 `has_assert_err` 检测 LOAD_ASSERTION_ERROR，但 merge_block 可能未含 LOAD_ASSERTION_ERROR（assert 的 RAISE_VARARGS 路径在 value 块的 jump target，不在 merge_block）。`_generate_assert`（line 1822+）也未把 ternary 作为 test 表达式。第二个 ternary 的 return 包装依赖 `is_return` 检测（line 18108+），但与第一个 ternary 共享同一函数体时，第二个 ternary 的 merge_block 末尾 RETURN_VALUE 被识别为外层 return 而非 Return(ternary)。
- **修复方向**：在 `_generate_assert` 中识别 `assert (ternary)` 模式时通过 `cond_block` 的 POP_JUMP_IF_FALSE 跳转目标检测 assert 抛错路径，把 ternary 作为 test。在 `_build_ternary_no_target_consumer_stmt` 的 return 包装路径中确保 `merge_block` 末尾 RETURN_VALUE 之前只有 ternary 表达式（无其他副作用指令），生成 Return(IfExp)（依「父引用子入口」：父 Assert 通过 condition_block 入口引用 ternary 子节点作为 test；父 Return 通过 merge_block 的 RETURN_VALUE 引用 ternary 子节点作为返回值）。

### Bug R9-16 [仍失败]：partial(g, ternary)

- **测试文件**：`tests/exhaustive/ternary/test_r9_ternary_partial_application.py`
- **源码**：
  ```python
  from functools import partial
  f = partial(g, (a if c else b))
  ```
- **期望**：`f = partial(g, (a if c else b))` 的 `LOAD_NAME partial + LOAD_NAME g + ternary merge + PRECALL + CALL` 完整保留。
- **实际**：原始 18 条 vs 重编 17 条。重编丢失 1 条 LOAD_NAME，把 `partial(g, ternary)` 退化为 `partial(g)`（ternary 参数丢失）。
- **根因分析**：ternary 的 merge_block 后跟 PRECALL + CALL，`func_call_info` 识别时 `_compute_ternary_cond_preload_exprs`（参考 region_ast_generator.py:18230+）只取 cond_block 的 preload（PUSH_NULL + LOAD_NAME partial + LOAD_NAME g），但 cond_block 的 preload 第一个元素 PUSH_NULL 被剥离后，剩下的 [LOAD_NAME partial, LOAD_NAME g] 中第二个 LOAD_NAME g 应作为 partial 的第一个位置参数而非 func。当前实现把 partial 当 func、ternary 当唯一参数，丢失 g。
- **修复方向**：在 `_compute_ternary_cond_preload_exprs` 中识别 `PUSH_NULL + LOAD_NAME X + LOAD_NAME Y` 模式，X 是 func、Y 是第一个位置参数。修正 `call_args` 计算（line 18234+）让 `_preloaded_args` 包含 Y（依「父引用子入口」：父 Call 通过 cond_block 的 partial+g 入口 + merge_block 的 CALL 引用 ternary 子节点作为第二个位置参数）。

### Bug R9-08 [仍失败]：except* PEP 654

- **测试文件**：`tests/exhaustive/ternary/test_r9_ternary_exception_group.py`
- **源码**：
  ```python
  try:
      pass
  except* E as e:
      x = a if c else b
  ```
- **期望**：`except* E as e:` handler body 含 `x = (a if c else b)` ternary 赋值。
- **实际**：原始 39 条 vs 重编 29 条。重编完全打乱了 except* handler 结构，丢失 PUSH_EXC_INFO + CHECK_EG_MATCH + COPY + POP_JUMP_FORWARD_IF_NONE 序列，把 except* handler body 直接平铺到 try 块之前。
- **根因分析**：`except*` (PEP 654) 是 Python 3.11+ 新语法，CFG builder 与 region analyzer 未识别 `PUSH_EXC_INFO + CHECK_EG_MATCH + COPY + POP_JUMP_FORWARD_IF_NONE` 序列作为 except* handler region。当前 `_generate_region` 路径未把 except* handler 作为独立 region 处理，handler body 的 ternary 也未正确归约。
- **修复方向**：在 `region_analyzer.py` 中新增 `ExceptStarRegion` 类型，识别 `CHECK_EG_MATCH + POP_JUMP_FORWARD_IF_NONE` 作为 region entry。在 `region_ast_generator.py` 中新增 `_generate_except_star` 生成 `ExceptHandler` 节点（type=E, name=e, body 含 ternary assign）（依「自底向上归约」：ternary 在 handler body 内先归约；依「父引用子入口」：父 Try 通过 CHECK_EG_MATCH 引用 ExceptStarRegion 入口）。

### Bug R7-03 [仍失败（被 skipTest 掩盖）]：async with multi-as + body ternary

- **测试文件**：`tests/exhaustive/ternary/test_r9_ternary_async_with_multi_as.py`
- **源码**：
  ```python
  async def f():
      async with a as x, b as y:
          z = c if cond else d
  ```
- **期望**：`async with a as x, b as y:` 完整保留 + body `z = (c if cond else d)`。
- **实际**：反编译输出完全破损：
  ```python
  async def f():
      async with a as y:
          break
          z = (c if cond else d)
          async with b as x: pass
  ```
  `break` 出现在 with body 内（语法错误），第二个 `async with b as x` 嵌套在 body 末尾，as_target 顺序倒置（x/y 互换），`b` 应在外层 with 列表内。测试框架因重编译失败 `SyntaxError: 'break' outside loop` 而 skipTest。
- **根因分析**：`region_analyzer.py` 中 WITH 区域识别未处理 `async with` 多个 as_target 的 `BEFORE_ASYNC_WITH + GET_AWAITABLE + SEND polling` 嵌套序列。多个 as_target 的 STORE_FAST x/y 与 ternary merge 块的 STORE_FAST z 在同一 with body 路径，as_target 顺序推断错误，错误插入 break 占位符。
- **修复方向**：在 `region_analyzer.py` 中扩展 AsyncWithRegion 识别多个 `BEFORE_ASYNC_WITH + GET_AWAITABLE + SEND` 序列，按顺序收集 as_target。在 `region_ast_generator.py` 的 `_generate_async_with` 中按 cond_block → polling → STORE_FAST 顺序重建 with items 列表（依「父引用子入口」：父 AsyncWith 通过每个 BEFORE_ASYNC_WITH 入口引用对应 polling+STORE_FAST 子节点）。

---

## 第二部分：R10 新增对抗性测试发现（15 个真失败）

### Bug R10-01：decorator chain + ternary arg

- **测试文件**：`tests/exhaustive/ternary/test_r10_ternary_decorator_chain_arg.py`
- **源码**：
  ```python
  @deco1
  @deco2(a if c else b)
  def f():
      pass
  ```
- **期望**：两层装饰器 `@deco1` + `@deco2(a if c else b)` 完整保留。
- **实际**：原始 18 条 vs 重编 15 条。重编丢失 3 条 `PRECALL + CALL`，把 `@deco2(a if c else b)` 退化为无参调用，丢失 `@deco1` 的 CALL 链。
- **根因分析**：与 R9-14 同根因。`_build_function_def`（line 959+）的 `_reconstruct_decorator_chain`（line 1302+）未识别 `deco2(ternary)` 调用后跟 `deco1(...)(f)` 调用的链式装饰器模式。decorator_list 中应包含 `[deco1, Call(deco2, [ternary])]`，但实际仅含部分。
- **修复方向**：扩展 `_reconstruct_decorator_chain` 处理 LOAD_NAME deco1 + LOAD_NAME deco2 + ternary merge + PRECALL + CALL + LOAD_CONST code + MAKE_FUNCTION + PRECALL + CALL + PRECALL + CALL 模式，识别 deco2(ternary)(f) + deco1(.(.)) 三段 CALL 链（依「父引用子入口」：每段 CALL 通过 MAKE_FUNCTION 之后的 CALL 引用下层装饰器或 FunctionObject 子节点）。

### Bug R10-02：decorator arg 是 subscript ternary

- **测试文件**：`tests/exhaustive/ternary/test_r10_ternary_decorator_subscr_arg.py`
- **源码**：
  ```python
  @deco(a[b if c else d])
  def f():
      pass
  ```
- **期望**：`@deco(a[b if c else d])` 装饰器调用含嵌套 Subscript(a, ternary) 完整保留。
- **实际**：原始 17 条 vs 重编 15 条。重编丢失 2 条 `LOAD_NAME + BINARY_SUBSCR`，把 `@deco(a[ternary])` 退化为 `@deco()`（参数丢失）。
- **根因分析**：与 R9-14 同根因。ternary merge_block 后跟 BINARY_SUBSCR（计算 `a[ternary]`），再 PRECALL + CALL（deco(subscript) 调用）。当前 `_extract_decorators` 仅识别 Call(deco, [ternary]) 模式，未识别 Call(deco, [Subscript(a, ternary)])。
- **修复方向**：在 `_extract_decorators` 中识别 merge_block 末尾的 `PRECALL + CALL` 之前的指令序列（如 BINARY_SUBSCR），通过 expr_reconstructor 重建完整表达式作为装饰器 Call 的 args（依「父引用子入口」：装饰器 Call 通过 merge_block 的 CALL 引用 ternary 子节点作为 BINARY_SUBSCR 的下标）。

### Bug R10-03：classmethod + ternary default arg

- **测试文件**：`tests/exhaustive/ternary/test_r10_ternary_classmethod_default.py`
- **源码**：
  ```python
  class C:
      @classmethod
      def m(cls, x=(a if c else b)):
          pass
  ```
- **期望**：`@classmethod` 装饰器调用保留，default tuple 含 ternary。
- **实际**：嵌套 code object 指令数 17 vs 14。重编丢失 3 条 `PRECALL + CALL`，把 `@classmethod` 退化为无装饰器函数（与 R9-13 同症状）。
- **根因分析**：与 R9-13 同根因。`_build_function_def` 中 `_reconstruct_decorator_chain`（line 1302+）未处理 `@classmethod` 这种无参装饰器调用的字节码模式（LOAD_NAME classmethod + LOAD_CONST code + MAKE_FUNCTION + PRECALL + CALL + STORE_NAME m）。
- **修复方向**：扩展 `_reconstruct_decorator_chain` 识别 `@classmethod`/`@staticmethod`/`@abstractmethod`/`@property` 等内置无参装饰器的 CALL 链（依「父引用子入口」：装饰器 Call 通过 MAKE_FUNCTION 之后的 CALL 引用 FunctionObject 子节点）。

### Bug R10-04：staticmethod + ternary default arg

- **测试文件**：`tests/exhaustive/ternary/test_r10_ternary_staticmethod_default.py`
- **源码**：与 R10-03 类似（`@staticmethod` 替换 `@classmethod`）
- **期望**：`@staticmethod` 装饰器调用保留。
- **实际**：嵌套 code object 指令数 17 vs 14，与 R10-03 同症状。
- **根因分析**：与 R10-03 同根因。
- **修复方向**：与 R10-03 同。

### Bug R10-05：多个 abstractmethod + ternary default

- **测试文件**：`tests/exhaustive/ternary/test_r10_ternary_multi_abstractmethod.py`
- **源码**：
  ```python
  class C:
      @abstractmethod
      def m1(self, x=(a if c else b)):
          pass
      @abstractmethod
      def m2(self, y=(d if e else f)):
          pass
  ```
- **期望**：两个 `@abstractmethod` 装饰器调用 + 两个 ternary default 完整保留。
- **实际**：嵌套 code object 指令数 27 vs 18，重编丢失 9 条指令（含 `POP_TOP` 等噪声），把两个 `@abstractmethod` 都退化为无装饰器函数，第二个 ternary 完全丢失。
- **根因分析**：与 R9-13 同根因，扩展到多个 abstractmethod 场景。`_build_function_def` 在处理 class body 第二个 `@abstractmethod` 时，因 `MAKE_FUNCTION + PRECALL + CALL + STORE_NAME m2` 序列紧接前一个 `@abstractmethod m1` 之后，重建链断裂。第二个 ternary 的 cond_block/merge_block 跨越前一个装饰器调用栈帧时归属错误。
- **修复方向**：扩展 `_reconstruct_decorator_chain` 处理多个连续 `MAKE_FUNCTION + PRECALL + CALL + STORE_NAME` 模式，按 STORE_NAME 边界切分装饰器链（依「父引用子入口」：每个 decorator Call 通过其 MAKE_FUNCTION + STORE_NAME 边界引用对应 FunctionObject 子节点）。

### Bug R10-06：dataclass field default_factory lambda ternary

- **测试文件**：`tests/exhaustive/ternary/test_r10_ternary_dataclass_default_factory.py`
- **源码**：
  ```python
  from dataclasses import dataclass, field
  @dataclass
  class C:
      x: int = field(default_factory=lambda: (a if c else b))
  ```
- **期望**：`field(default_factory=lambda: (a if c else b))` 调用保留，lambda body 含 ternary。
- **实际**：反编译结果中 ternary 完全丢失，lambda body 退化为占位符：
  ```python
  from dataclasses import dataclass, field
  @dataclass
  class C:
      x: int = field(default_factory=(lambda *args, **kwargs: None))
  ```
  lambda code object 未递归反编译，被替换为 `lambda *args, **kwargs: None`。
- **根因分析**：`_convert_lambda_function_objects`（region_ast_generator.py 中相关 lambda 处理路径）未递归反编译嵌套在 field() Call 的 kwargs 中的 lambda FunctionObject。CodeGenerator 把未识别的 FunctionObject 渲染为占位符。lambda body 内的 ternary（独立 code object 内的 TernaryRegion）也未归约。
- **修复方向**：在 CodeGenerator 中调用 `_convert_lambda_function_objects` 递归处理 Call.args 与 Call.keywords 中的 FunctionObject（依「自底向上归约」+「嵌套即抽象节点」：lambda 在 field() Call 中作为单个抽象节点，其 body 内 ternary 先归约后整体作为 default_factory 关键字参数值）。

### Bug R10-07：TypedDict + ternary default

- **测试文件**：`tests/exhaustive/ternary/test_r10_ternary_typeddict_default.py`
- **源码**：
  ```python
  from typing import TypedDict
  class Movie(TypedDict):
      title: str
      year: int = (a if c else b)
  ```
- **期望**：`year: int = (a if c else b)` AnnAssign 保留 ternary。
- **实际**：嵌套 code object 指令数 20 vs 16，重编丢失 4 条指令：`LOAD_NAME a + LOAD_NAME c + LOAD_NAME b`（ternary merge 块的 LOAD_ 指令），把 `year: int = (a if c else b)` 退化为 `year: int`（无 value）。
- **根因分析**：`_generate_region` 处理 AnnAssign（`x: int = ternary`）时未识别 ternary merge 块作为 value 表达式。`region_ast_generator.py` 中 AnnAssign 的 value 提取路径（如 `_generate_ann_assign` 或类似）未把 TernaryRegion 作为 value 子节点引用。
- **修复方向**：扩展 AnnAssign 生成路径，检测 `STORE_NAME year` 之前的 cond_block/merge_block 是否构成 TernaryRegion，若是则把 IfExp 作为 AnnAssign.value（依「父引用子入口」：父 AnnAssign 通过 STORE_NAME year 引用 ternary 子节点作为 value）。

### Bug R10-08：ABC abstract property + ternary

- **测试文件**：`tests/exhaustive/ternary/test_r10_ternary_abc_abstract_property.py`
- **源码**：
  ```python
  from abc import ABC, abstractmethod
  class C(ABC):
      @property
      @abstractmethod
      def x(self):
          ...
      @x.setter
      def x(self, v):
          self._x = v if c else 0
  ```
- **期望**：`@property + @abstractmethod` 双层装饰器 + `@x.setter` 装饰器 + setter body `self._x = v if c else 0` ternary 保留。
- **实际**：反编译结果中 ternary 完全丢失：
  ```python
  from abc import ABC, abstractmethod
  class C(ABC):
      @property
      @abstractmethod
      def x(self):
          return None
      x = (lambda *args, **kwargs: False)()
  ```
  setter 的 ternary assign 退化为 `x = (lambda *args, **kwargs: False)()`。
- **根因分析**：与 R9-12 同根因 + lambda FunctionObject 占位符问题。`@x.setter` 装饰器（LOAD_NAME x + LOAD_ATTR setter + LOAD_CONST code + MAKE_FUNCTION + PRECALL + CALL + STORE_NAME x）未识别为 attribute decorator，setter FunctionObject 被替换为占位 lambda。
- **修复方向**：扩展 `_reconstruct_decorator_chain` 处理 `@x.setter` 模式（依「父引用子入口」：装饰器 Call 通过 LOAD_ATTR setter 引用 LOAD_NAME x 子节点）。

### Bug R10-09：magic methods __eq__/__hash__ + ternary

- **测试文件**：`tests/exhaustive/ternary/test_r10_ternary_magic_methods.py`
- **源码**：
  ```python
  class C:
      def __eq__(self, other):
          return self.x == (other.x if c else 0)
      def __hash__(self):
          return hash(self.x) if c else 0
  ```
- **期望**：两个 magic method 内的 ternary（Compare + Return(IfExp)）保留。
- **实际**：嵌套 code object 指令数 9 vs 8。`__eq__` 的 body `return self.x == (other.x if c else 0)` 中 ternary 表达式作为 Compare 的右操作数，重编丢失 1 条 `LOAD_ATTR x`（把 `other.x` 退化为 `other`）。具体：
  ```
  原始: LOAD_FAST other; LOAD_ATTR x; LOAD_CONST 0; COMPARE_OP
  重编: LOAD_FAST other; LOAD_CONST 0; COMPARE_OP
  ```
- **根因分析**：ternary 表达式 `other.x if c else 0` 的 false_block 是 LOAD_CONST 0，true_block 是 LOAD_FAST other + LOAD_ATTR x。当 ternary 作为 Compare 的右操作数时，true_block 的 LOAD_ATTR x 指令被错误剥离。可能 `_build_ternary_expr`（ternary 表达式构建路径）在处理 Compare 操作数时未正确收集 true_block 的所有 LOAD_* 指令。
- **修复方向**：在 ternary 表达式构建中确保 true_block 的所有 LOAD_* + LOAD_ATTR 指令完整收集（依「父引用子入口」：父 Compare 通过 true_block 引用 LOAD_FAST other + LOAD_ATTR x 子节点序列）。

### Bug R10-10：functools.wraps + ternary in body

- **测试文件**：`tests/exhaustive/ternary/test_r10_ternary_wraps.py`
- **源码**：
  ```python
  from functools import wraps
  def deco(f):
      @wraps(f)
      def g(*args, **kwargs):
          return f(*(args if c else ()), **kwargs)
      return g
  ```
- **期望**：`@wraps(f)` 装饰器 + return `f(*(args if c else ()), **kwargs)` 完整保留。
- **实际**：反编译结果中 ternary 与 *args 完全丢失，且引入了非法的 `global c` 与 `nonlocal f`：
  ```python
  from functools import wraps
  def deco(f):
      @wraps(f)
      def g(*args, **kwargs):
          global c
          nonlocal f
          return f(**kwargs)
      return g
  ```
  ternary `(args if c else ())` 丢失，`f(*args, **kwargs)` 退化为 `f(**kwargs)`。`global c` 与 `nonlocal f` 是反编译器误插入的伪语句（来自变量解析失败时的兜底）。
- **根因分析**：ternary 在 `f(*ternary, **kwargs)` 这种 CALL_FUNCTION_EX + DICT_MERGE 复合调用模式下未正确归约。`_try_build_ternary_kwarg_call`（line 20472+）与 `_is_star_call` 路径（line 18184+）协同处理 *args ternary，但当同时存在 *args 和 **kwargs 时，ternary 的归属被识别为 *args，但 *args 解包后又被 DICT_MERGE 与 **kwargs 合并，导致 ternary 完全丢失。`global c` 和 `nonlocal f` 是变量未在 g 体内定义时的兜底（应识别为自由变量）。
- **修复方向**：在 `_try_build_ternary_kwarg_call` 与 CALL_FUNCTION_EX 路径协同处理 `f(*ternary, **kwargs)` 模式（依「父引用子入口」：父 Call 通过 cond_block 的 f 入口 + merge_block 的 CALL_FUNCTION_EX 引用 ternary 子节点作为 *args 元组）。同时修复 `global`/`nonlocal` 兜底逻辑，避免误插入。

### Bug R10-11：typing.overload + ternary in body

- **测试文件**：`tests/exhaustive/ternary/test_r10_ternary_overload.py`
- **源码**：
  ```python
  from typing import overload
  @overload
  def f(x: int) -> int: ...
  @overload
  def f(x: str) -> str: ...
  def f(x):
      return (a if c else b)
  ```
- **期望**：三个 f 定义 + `@overload` 装饰器 + return (ternary) 完整保留。
- **实际**：原始 34 条 vs 重编 24 条。重编丢失 10 条指令，前两个 `@overload` 装饰器调用 `PRECALL + CALL` 全部丢失，退化为无装饰器函数。
- **根因分析**：与 R9-13 同根因。`@overload` 是无参装饰器，MAKE_FUNCTION + PRECALL + CALL + STORE_NAME f 三次重复出现。`_reconstruct_decorator_chain` 仅识别第一个 `@overload`，后续两个装饰器调用被剥离。第三个 f（真正实现）的 return (ternary) 应保留，但因装饰器链错乱被影响。
- **修复方向**：与 R10-03/R10-05 同。

### Bug R10-12：partialmethod + ternary

- **测试文件**：`tests/exhaustive/ternary/test_r10_ternary_partialmethod.py`
- **源码**：
  ```python
  from functools import partialmethod
  class C:
      def _m(self, x):
          return x
      m = partialmethod(_m, (a if c else b))
  ```
- **期望**：`m = partialmethod(_m, (a if c else b))` 调用 + ternary 第二个参数保留。
- **实际**：嵌套 code object 指令数 19 vs 15，重编丢失 4 条指令：`LOAD_CONST code + MAKE_FUNCTION + STORE_NAME _m` 与 `LOAD_NAME _m` 部分，把 `partialmethod(_m, ternary)` 退化为 `partialmethod(ternary)` 或更糟。
- **根因分析**：与 R9-16 同根因（partial(g, ternary) 模式）。`partialmethod(_m, ternary)` 的 cond_block preload 是 `PUSH_NULL + LOAD_NAME partialmethod + LOAD_NAME _m`，ternary merge 是第二个位置参数。当前 `_compute_ternary_cond_preload_exprs` 把 partialmethod 当 func、ternary 当唯一参数，丢失 `_m`。
- **修复方向**：与 R9-16 同（识别 PUSH_NULL + LOAD_NAME X + LOAD_NAME Y 模式，X 是 func、Y 是第一个位置参数）。

### Bug R10-13：TypeVar + ternary bound

- **测试文件**：`tests/exhaustive/ternary/test_r10_ternary_typevar_bound.py`
- **源码**：
  ```python
  from typing import TypeVar
  T = TypeVar('T', bound=(A if c else B))
  ```
- **期望**：`TypeVar('T', bound=(A if c else B))` 调用保留 ternary 作为 bound 关键字参数值。
- **实际**：原始 19 条 vs 重编 17 条。重编丢失 2 条指令：`LOAD_CONST 'T'` 与 `KW_NAMES`，把 `TypeVar('T', bound=ternary)` 退化为 `TypeVar(ternary)`（丢失位置参数 'T' 与关键字名 bound）。
- **根因分析**：`_try_build_ternary_kwarg_call`（line 20472+）处理 KW_NAMES 时未识别 cond_block 中 preload 的位置参数 `'T'`。当前实现把 ternary 当作唯一位置参数，丢失 `'T'` 与 `bound=` 关键字名。
- **修复方向**：在 `_try_build_ternary_kwarg_call` 中通过 `_compute_ternary_cond_preload_exprs` 收集 cond_block 中 preload 的位置参数（如 `LOAD_CONST 'T'`），并保留 KW_NAMES 提供的关键字名（依「父引用子入口」：父 Call 通过 cond_block 的 TypeVar+'T' 入口 + merge_block 的 KW_NAMES 引用 ternary 子节点作为 bound 关键字参数值）。

### Bug R10-14：async context manager + ternary in __aenter__

- **测试文件**：`tests/exhaustive/ternary/test_r10_ternary_async_aenter.py`
- **源码**：
  ```python
  class C:
      async def __aenter__(self):
          self.x = (a if c else b)
          return self
  ```
- **期望**：`__aenter__` 方法体内 `self.x = (a if c else b)` ternary 赋值 + `return self` 保留。
- **实际**：嵌套 code object 指令数 10 vs 12。重编多出 2 条指令，ternary merge 块被打乱：
  ```
  原始: RESUME, LOAD_GLOBAL a, LOAD_GLOBAL c, LOAD_GLOBAL b, LOAD_FAST self, STORE_ATTR x, LOAD_FAST self, RETURN_VALUE
  重编: RESUME, LOAD_GLOBAL a, LOAD_GLOBAL c, POP_TOP, LOAD_CONST None, RETURN_VALUE, LOAD_GLOBAL b, POP_TOP, LOAD_CONST None, RETURN_VALUE
  ```
  ternary 的 false_block 被分离为独立 code path，STORE_ATTR x 与 RETURN_VALUE 被错误归入 else 分支。
- **根因分析**：async 函数的 RETURN_GENERATOR + POP_TOP 前缀与 ternary merge 块的归属冲突。`_generate_function_def` 在 async 函数路径下未正确处理 ternary merge 块与 RETURN_VALUE 的关系，把 ternary 的 false_block 与 return self 当作独立路径。
- **修复方向**：在 async 函数路径下确保 ternary merge 块的 STORE_ATTR 与后续 RETURN_VALUE 在同一基本块内，不要因 RETURN_GENERATOR 前缀错误切分（依「每块唯一归属」+「自底向上归约」：ternary 在 __aenter__ 内先归约，return self 在父 FunctionDef body 中作为独立语句）。

### Bug R10-15：ternary in default of kwonly arg

- **测试文件**：`tests/exhaustive/ternary/test_r10_ternary_kwonly_default.py`
- **源码**：
  ```python
  def f(*args, x=(a if c else b)):
      pass
  ```
- **期望**：`def f(*args, x=(a if c else b))` 保留，kwonly 参数 x 的默认值是 ternary。
- **实际**：反编译结果中 ternary 完全丢失，且参数列表破损：
  ```python
  def f(*x, args):
      return None
  ```
  `*args` 与 `x` 互换位置，ternary 默认值丢失，函数 body 退化为 `return None`。
- **根因分析**：kwonly 参数的默认值通过 BUILD_CONST_KEY_MAP（line 1006-1045 处理路径）构建，ternary merge 块的栈输出作为 BUILD_CONST_KEY_MAP 的 value。但 ternary 在外层 code object 计算（默认参数在函数定义时求值），与 MAKE_FUNCTION 的栈帧顺序冲突。`_extract_function_args`（line 1652+）未把 ternary 识别为 kw_defaults，且 *args 与 x 的顺序在 varnames 解析中错乱。
- **修复方向**：在 `_build_function_def` 中识别 MAKE_FUNCTION 之前的 BUILD_CONST_KEY_MAP 模式，把 ternary 表达式作为对应 kwonly 参数的默认值（依「父引用子入口」：父 FunctionDef 通过 MAKE_FUNCTION 引用 FunctionObject；FunctionObject.kw_defaults 通过 BUILD_CONST_KEY_MAP 引用 ternary 子节点作为 value）。

---

## 累计 bug 统计

| 类别 | bug 数 | 详情 |
|------|--------|------|
| R9 已知限制仍失败 | 7 | R9-08, R9-10, R9-12, R9-13, R9-14, R9-15, R9-16 |
| R9 已知限制被 skipTest 掩盖 | 1 | R7-03 async with multi-as（反编译输出含 `break outside loop`，真 bug） |
| R10 新增对抗性测试 | 15 | R10-01 ~ R10-15 |
| **累计** | **23** | 超出 10 个停止条件 |

---

## 测试统计

- **测试文件数**：28（R10 新增）+ 8（R9 已知限制回归验证）
- **R10 新增测试**：15 failed / 13 passed（68% pass rate，需要修复）
- **R9 回归**：7 failed / 1 skipped（仍存在问题）
- **总执行时间**：约 1.3 秒（28 个 R10 测试）+ 0.5 秒（8 个 R9 回归测试）

---

## 修复优先级建议

按"修复一个能解决多个 bug"的原则，建议优先修复以下根因：

### 优先级 P0（影响 6+ 个 bug）

1. **无参装饰器 CALL 链识别**（影响 R9-13, R10-03, R10-04, R10-05, R10-11，5 个 bug）
   - 修复点：`_reconstruct_decorator_chain`（region_ast_generator.py:1302+）
   - 修复方向：识别 `LOAD_NAME X + LOAD_CONST code + MAKE_FUNCTION + PRECALL + CALL + STORE_NAME` 模式，保留 `Name(X)` 作为装饰器（@classmethod, @staticmethod, @abstractmethod, @overload, @property）

2. **带参装饰器 Call 节点保留**（影响 R9-14, R10-01, R10-02, R10-08，4 个 bug）
   - 修复点：`_extract_decorators`（region_ast_generator.py:1228-1300）
   - 修复方向：识别 merge_block 末尾的 `PRECALL + CALL` 之前的指令序列，通过 expr_reconstructor 重建完整 Call(deco, [ternary_or_subscript_expr])

### 优先级 P1（影响 2-3 个 bug）

3. **partial/partialmethod 的多位置参数识别**（影响 R9-16, R10-12，2 个 bug）
   - 修复点：`_compute_ternary_cond_preload_exprs`（region_ast_generator.py:18230+）
   - 修复方向：识别 `PUSH_NULL + LOAD_NAME X + LOAD_NAME Y` 模式，X 是 func、Y 是第一个位置参数

4. **KW_NAMES 与 cond_block preload 协同**（影响 R10-13，1 个 bug；与 R9-06/10/12 相关）
   - 修复点：`_try_build_ternary_kwarg_call`（region_ast_generator.py:20472+）
   - 修复方向：通过 `_compute_ternary_cond_preload_exprs` 收集 cond_block 中 preload 的位置参数

5. **AnnAssign ternary value 识别**（影响 R10-07，1 个 bug；与 R9-10 相关）
   - 修复点：AnnAssign 生成路径
   - 修复方向：检测 `STORE_NAME year` 之前的 cond_block/merge_block 是否构成 TernaryRegion

### 优先级 P2（影响 1 个 bug，需要新区域类型）

6. **except* PEP 654 region 识别**（影响 R9-08，1 个 bug）
   - 修复点：新增 `ExceptStarRegion` 类型
   - 修复方向：识别 `CHECK_EG_MATCH + POP_JUMP_FORWARD_IF_NONE` 作为 region entry

7. **async with multi-as region 识别**（影响 R7-03，1 个 bug）
   - 修复点：扩展 `AsyncWithRegion` 识别多个 BEFORE_ASYNC_WITH + GET_AWAITABLE + SEND 序列

8. **async 函数 ternary + RETURN_GENERATOR 前缀**（影响 R10-14，1 个 bug）
   - 修复点：async 函数路径下的 ternary merge 块归属

9. **CALL_FUNCTION_EX + DICT_MERGE 复合调用 ternary**（影响 R10-10，1 个 bug）
   - 修复点：`_try_build_ternary_kwarg_call` 与 CALL_FUNCTION_EX 路径协同

10. **FunctionObject 占位符递归反编译**（影响 R10-06, R10-08，2 个 bug）
    - 修复点：CodeGenerator 中 `_convert_lambda_function_objects` 递归处理

11. **kwonly BUILD_CONST_KEY_MAP ternary**（影响 R10-15，1 个 bug）
    - 修复点：`_build_function_def` 中 kw_defaults 识别

12. **ternary 作为 Compare 右操作数**（影响 R10-09，1 个 bug）
    - 修复点：ternary 表达式构建中 true_block 指令完整收集

13. **assert (ternary) 识别**（影响 R9-15，1 个 bug）
    - 修复点：`_generate_assert` 中通过 cond_block POP_JUMP_IF_FALSE 跳转目标检测

---

## 区域归约算法 4 原则遵循情况

所有修复建议均遵循区域归约算法 4 原则：

1. **自底向上归约**：嵌套 ternary（如 R10-06 的 lambda body ternary、R10-08 的 setter body ternary）在内层 code object 内先归约
2. **每块唯一归属**：ternary merge 块归 TernaryRegion，不被外层 AssertRegion/AssignRegion 重复消费
3. **嵌套区域作为抽象节点**：装饰器 Call 中的 FunctionObject（含 ternary body）作为单个抽象节点，不展开
4. **父区域 then/else 引用子区域入口**：父 Call 通过 cond_block 的 func 入口 + merge_block 的 CALL 引用 ternary 子节点；父 Assign 通过 STORE_NAME 引用 ternary 子节点作为 value；父 AnnAssign 通过 STORE_NAME 引用 ternary 子节点作为 value

---

## 测试文件清单

R10 新增 28 个测试文件：

```
tests/exhaustive/ternary/test_r10_ternary_abc_abstract_property.py        [FAIL R10-08]
tests/exhaustive/ternary/test_r10_ternary_async_aenter.py                  [FAIL R10-14]
tests/exhaustive/ternary/test_r10_ternary_async_anext.py                   [PASS]
tests/exhaustive/ternary/test_r10_ternary_cached_property.py               [PASS]
tests/exhaustive/ternary/test_r10_ternary_classmethod_default.py           [FAIL R10-03]
tests/exhaustive/ternary/test_r10_ternary_contextmanager.py                 [PASS]
tests/exhaustive/ternary/test_r10_ternary_dataclass_default_factory.py      [FAIL R10-06]
tests/exhaustive/ternary/test_r10_ternary_dataclass_post_init.py           [PASS]
tests/exhaustive/ternary/test_r10_ternary_decorator_attr_arg.py             [PASS]
tests/exhaustive/ternary/test_r10_ternary_decorator_chain_arg.py            [FAIL R10-01]
tests/exhaustive/ternary/test_r10_ternary_decorator_subscr_arg.py          [FAIL R10-02]
tests/exhaustive/ternary/test_r10_ternary_enum_class.py                    [PASS]
tests/exhaustive/ternary/test_r10_ternary_exitstack.py                     [PASS]
tests/exhaustive/ternary/test_r10_ternary_generic_class.py                 [PASS]
tests/exhaustive/ternary/test_r10_ternary_kwonly_default.py                 [FAIL R10-15]
tests/exhaustive/ternary/test_r10_ternary_lambda_nested_default.py         [PASS]
tests/exhaustive/ternary/test_r10_ternary_magic_methods.py                 [FAIL R10-09]
tests/exhaustive/ternary/test_r10_ternary_multi_abstractmethod.py          [FAIL R10-05]
tests/exhaustive/ternary/test_r10_ternary_nested_class.py                   [PASS]
tests/exhaustive/ternary/test_r10_ternary_overload.py                      [FAIL R10-11]
tests/exhaustive/ternary/test_r10_ternary_partialmethod.py                 [FAIL R10-12]
tests/exhaustive/ternary/test_r10_ternary_protocol_class.py                [PASS]
tests/exhaustive/ternary/test_r10_ternary_staticmethod_default.py          [FAIL R10-04]
tests/exhaustive/ternary/test_r10_ternary_typeddict_default.py              [FAIL R10-07]
tests/exhaustive/ternary/test_r10_ternary_typevar_bound.py                 [FAIL R10-13]
tests/exhaustive/ternary/test_r10_ternary_typing_final.py                  [PASS]
tests/exhaustive/ternary/test_r10_ternary_typing_override.py                [PASS]
tests/exhaustive/ternary/test_r10_ternary_wraps.py                        [FAIL R10-10]
```

R9 已知限制回归验证 8 个测试文件：

```
tests/exhaustive/ternary/test_r9_ternary_async_with_multi_as.py            [SKIP R7-03, 真失败被 skipTest 掩盖]
tests/exhaustive/ternary/test_r9_ternary_assert_return_consumer.py         [FAIL R9-15]
tests/exhaustive/ternary/test_r9_ternary_abstractmethod.py                [FAIL R9-13]
tests/exhaustive/ternary/test_r9_ternary_class_decorator_arg.py           [FAIL R9-14]
tests/exhaustive/ternary/test_r9_ternary_exception_group.py               [FAIL R9-08]
tests/exhaustive/ternary/test_r9_ternary_frozen_dataclass_default.py      [FAIL R9-10]
tests/exhaustive/ternary/test_r9_ternary_partial_application.py           [FAIL R9-16]
tests/exhaustive/ternary/test_r9_ternary_property_setter.py                [FAIL R9-12]
```

---

## 测试执行命令

```bash
cd /workspace && timeout 250 python -m pytest tests/exhaustive/ternary/test_r10_*.py --tb=no -q
# 输出: 15 failed, 13 passed in 1.27s

cd /workspace && timeout 60 python -m pytest \
  tests/exhaustive/ternary/test_r9_ternary_async_with_multi_as.py \
  tests/exhaustive/ternary/test_r9_ternary_assert_return_consumer.py \
  tests/exhaustive/ternary/test_r9_ternary_abstractmethod.py \
  tests/exhaustive/ternary/test_r9_ternary_class_decorator_arg.py \
  tests/exhaustive/ternary/test_r9_ternary_exception_group.py \
  tests/exhaustive/ternary/test_r9_ternary_frozen_dataclass_default.py \
  tests/exhaustive/ternary/test_r9_ternary_partial_application.py \
  tests/exhaustive/ternary/test_r9_ternary_property_setter.py \
  --tb=no -q
# 输出: 7 failed, 1 skipped in 0.44s
```

测试停止条件已满足（10+ 真失败 bug，实际 23 个）。
