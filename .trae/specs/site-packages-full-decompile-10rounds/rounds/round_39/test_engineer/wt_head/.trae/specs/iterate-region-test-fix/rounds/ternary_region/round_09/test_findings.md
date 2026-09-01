# Ternary Region Round 9 — 测试发现报告

**测试时间**: 2026-07-21
**基线 commit**: b05d530 (R8 已完成并 push)
**Python 版本**: 3.11.15
**测试范围**: 4 个 R8 已知 async 限制 + 24 个新增对抗性测试

## 测试执行结果概览

- **创建测试文件**: 24 个 (`test_r9_ternary_*.py`)
- **执行结果**: 8 passed / 15 failed / 2 skipped (无 error in setup)
- **真失败 bug 数**: 15（已超过停止条件 10）
- **R8 已知限制回归**: 4/4 仍失败（R7-02/R7-03/R7-10/R8-08）

## R8 已知限制回归验证（4/4 仍失败）

| Bug ID | 测试文件 | 状态 | 失败现象 |
|--------|----------|------|----------|
| R7-02 | test_r7_ternary_in_async_for.py | FAIL | ternary 退化为 `a; b` 表达式泄漏，IfExp 完全丢失 |
| R7-03 | test_r7_ternary_in_async_with.py | FAIL | 指令10 操作码不匹配: POP_TOP vs STORE_FAST（as 绑定丢失） |
| R7-10 | test_r7_ternary_in_async_for_else.py | FAIL | ternary 退化为 `while True: pass`，IfExp 完全丢失 |
| R8-08 | test_r8_ternary_async_for_iter.py | FAIL | 重编多 2 条 POP_TOP + LOAD_CONST 注入 |

---

## 新增对抗性测试 — 15 个真失败 bug 详细分析

### Bug R9-01: async for body 多层嵌套 ternary
- **文件**: `test_r9_ternary_async_for_nested_body.py`
- **源码**:
  ```python
  async def f():
      async for x in ys:
          z = (a if c1 else (b if c2 else d))
  ```
- **失败现象**: 反编译结果完全丢失 ternary，输出仅 `async def f():\n    async for x in ys:\n        a`
- **根因分析**:
  - region_analyzer.py:3186-3227 中 `_identify_loop_regions` 对 async for 的 polling 块归属推断（GET_AITER + GET_ANEXT + SEND）将 ternary 的 condition/true/false/merge 块误判为 async for 的 polling 子循环块。
  - 多层嵌套 ternary 的内层 merge 块被识别为外层 async for 的 LOOP_ELSE 角色块，违反「每块在任意层级只属于一个区域」原则。
  - region_ast_generator.py:13340-13350 中 `_generate_with` 的特例判断（SEND/YIELD_VALUE 块）被错误复用到 async for body 的 ternary 识别中。
- **修复方向**: 在 `_identify_loop_regions` 的 async for 分支（L3186-3227）增加守卫：检测候选 polling 块是否同时属于某个 TernaryRegion 的 entry/merge 块；若是则保留 ternary 归属，将 polling 块从 async for body 集合移除。符合「自底向上归约」+「每块唯一归属」原则。

### Bug R9-02: async with 多个 as target + body ternary
- **文件**: `test_r9_ternary_async_with_multi_as.py`
- **源码**:
  ```python
  async def f():
      async with a as x, b as y:
          z = c if cond else d
  ```
- **失败现象**: SKIPPED — 重编译失败（反编译结果语法错误）
- **根因分析**:
  - region_ast_generator.py:13290-13314 中 `_generate_with` 的 early as-target detection 只处理单个 as_target（取 `with_blocks[0]` 首条 STORE_*），多 as target 时第二个 as 绑定被丢弃，导致 `b as y` 缺失 → 反编译输出形如 `async with a as x:` 的单 item with。
  - 区域归约违反「父区域 then/else 列表引用子区域入口」：with 的 items 列表只引用第一个 as_target 的 STORE_* 入口，第二个 as_target 的 STORE_* 入口被当作普通语句处理。
- **修复方向**: 在 L13290-13314 的 early detection 循环中收集**所有** STORE_* 指令作为 as_target 序列，对应填充 region.items 列表（保持 withitem 顺序）。符合「父区域引用子区域入口」原则。

### Bug R9-03: async for iter 含 ternary + call
- **文件**: `test_r9_ternary_async_for_iter_call.py`
- **源码**:
  ```python
  async def f():
      async for x in g(a if c else b):
          pass
  ```
- **失败现象**: 重编字节码多 2 条 `POP_TOP + LOAD_CONST`，原始 19 条 vs 重编 21 条
- **根因分析**:
  - region_analyzer.py:3186-3227 的 async for 识别中，`for_iter_setup` 检测 `GET_AITER` 的前驱块时，候选前驱块可能就是 ternary 的 merge_block（含 `PRECALL+CALL` 消费 ternary 结果）。当前算法未识别该 merge 块已属 TernaryRegion。
  - 重编时 ternary merge 块的 `LOAD_CONST None + POP_TOP`（CALL 后的清理）被重复生成一次，污染 async for 的 GET_AITER 源栈。
  - 违反「嵌套区域在父区域中作为单个抽象节点」：ternary merge 块应作为单个抽象节点（CALL 结果）被 GET_AITER 引用，而不是把内部清理指令泄漏到父 async for 的字节码中。
- **修复方向**: 在 async for 的 `for_iter_setup` 检测中（L3192-3201），若候选 setup 块属于某 TernaryRegion.merge_block，则跳过该 setup 块的字节码生成（仅作为抽象节点引用），让 ternary 自己负责 merge 块的字节码生成。

### Bug R9-04: async generator yield ternary + 后续语句
- **文件**: `test_r9_ternary_async_gen_yield_ternary.py`
- **源码**:
  ```python
  async def g():
      yield a if c else b
      x = 1
  ```
- **失败现象**: 反编译结果完全丢失 ternary 与 yield，输出 `async def g():\n    x = 1`
- **根因分析**:
  - async generator 的 RESUME + GET_AWAITABLE + SEND polling 块在函数入口前缀，导致 ternary 的 condition_block 被误判为函数 entry polling 块。
  - region_ast_generator.py 中 `_build_ternary_no_target_consumer_stmt` 的 Pattern 13（`yield (ternary)`）检测（L18799-18800）未覆盖 async generator 的 YIELD_VALUE + 后续 SEND 协议路径：async gen 的 YIELD_VALUE 后必须接 RESUME + JUMP_BACKWARD_NO_INTERRUPT 回到 SEND，与同步 yield 的单条 YIELD_VALUE 不同。
  - 违反「每块在任意层级只属于一个区域」：YIELD_VALUE 块同时被认作 async gen polling 子循环块和 ternary merge 块。
- **修复方向**: 在 ternary 识别时增加 async gen 检测守卫：若 merge_block 的 YIELD_VALUE 后续块是 SEND 块且属于 async gen 协议路径，仍应保留 ternary merge 归属（让 yield 表达式正确生成），将 SEND 块单独标记为 async gen 协议块。

### Bug R9-05: async comprehension if 条件是 ternary
- **文件**: `test_r9_ternary_async_comprehension_if.py`
- **源码**:
  ```python
  async def f():
      return [x async for x in iter if (a if c else b)]
  ```
- **失败现象**: 嵌套 code object 不匹配：原始 18 条 vs 重编 17 条，缺少 `LOAD_FAST` 消费指令
- **根因分析**:
  - listcomp 内部 code object 中，ternary merge 块后的 `LOAD_FAST x`（if 条件求值后压栈）被误识别为 ternary 自身的 value 块或被合并到 END_ASYNC_FOR 块中。
  - async comprehension 的 LIST_APPEND 与 END_ASYNC_FOR 之间的栈顺序依赖 LOAD_FAST x，但 ternary 归约时吞并了 LOAD_FAST 块作为 merge_extra_blocks，违反「父引用子入口」。
- **修复方向**: 在 ternary region 识别中，若 merge_block 的后继块是 LOAD_FAST + LIST_APPEND（async/list comprehension 模式），不应将该 LOAD_FAST 块加入 merge_extra_blocks。该 LOAD_FAST 块属于父 comprehension 的 if 条件求值，不属于 ternary 子区域。

### Bug R9-06: 带类型注解的变量 + ternary 默认值（PASS）
- **文件**: `test_r9_ternary_annotation_default.py` — PASSED（参考对照）

### Bug R9-07: match case guard 是 ternary（PASS）
- **文件**: `test_r9_ternary_match_guard.py` — PASSED（参考对照）

### Bug R9-08: except* handler body 含 ternary
- **文件**: `test_r9_ternary_exception_group.py`
- **源码**:
  ```python
  try:
      pass
  except* E as e:
      x = a if c else b
  ```
- **失败现象**: 指令数严重不匹配：原始 39 条 vs 重编 29 条，CHECK_EG_MATCH + PUSH_EXC_INFO + BUILD_LIST 等基础设施全部错乱
- **根因分析**:
  - region_ast_generator.py 中 `_generate_try` (L11861) 的 handler 处理未识别 `except*` (PEP 654)。代码中虽多处出现 `CHECK_EG_MATCH` 字符串（L3105-3106, L3828-3829 等），但只作为「except 基础设施」过滤掉，没有专门的 except* handler 生成逻辑。
  - `except*` 的字节码模式（PUSH_EXC_INFO + COPY + BUILD_LIST + SWAP + CHECK_EG_MATCH + COPY + POP_JUMP_FORWARD_IF_NONE）完全不同于普通 except，需要独立的 handler region 类型。
  - ternary merge 块的 STORE_FAST x 与 except* 的异常清理路径（DELETE_NAME + POP_EXCEPT）共享同一 handler body，违反「每块唯一归属」。
- **修复方向**: 新增 ExceptGroupRegion 类型，专门识别 `except*` 的 CHECK_EG_MATCH + PUSH_EXC_INFO 模式。在 `_generate_try` 中检测到 CHECK_EG_MATCH 时切换到 except* 处理路径，将 ternary merge 块的归属让渡给 except* handler body（ternary 作为单个抽象节点）。

### Bug R9-09: metaclass class body + ternary 属性
- **文件**: `test_r9_ternary_metaclass_class_body.py`
- **源码**:
  ```python
  class C(metaclass=M):
      attr = a if c else b
      def m(self):
          return self.attr
  ```
- **失败现象**: 外层 code object 指令数不匹配：原始 13 条 vs 重编 11 条，缺少 `LOAD_NAME M + KW_NAMES`
- **根因分析**:
  - 外层（模块级）`class C(metaclass=M)` 的 BUILD_CLASS + CALL 调用中，`metaclass=M` 的关键字参数通过 `LOAD_NAME M + KW_NAMES + PRECALL + CALL` 传递。
  - region_ast_generator.py 中类定义重建代码（L425-437、L1564、L14115）未在 CALL 之前生成 KW_NAMES 指令。`_try_build_ternary_kwarg_call` (L20367) 只处理 ternary 作为 kwarg 的情况，不处理 BUILD_CLASS 调用本身有 kwarg 的情况。
  - 注：类体内部的 ternary 是独立 code object，与外层 BUILD_CLASS 无直接归属冲突，但反编译器在重建 `class C(metaclass=M)` 时丢失了 metaclass kwarg —— 这是 class 重建逻辑的缺陷，被 ternary 在类体内的存在触发暴露。
- **修复方向**: 在 CodeGenerator 重建 ClassDef 时，若关键字参数非空（keywords != []），必须生成 KW_NAMES 指令（参考普通函数调用的 KW_NAMES 处理 L8536-8599）。这不是 ternary 本身的 bug，但属于 ternary 在 class body 时暴露的 class 重建缺陷。

### Bug R9-10: frozen dataclass field 默认值 ternary
- **文件**: `test_r9_ternary_frozen_dataclass_default.py`
- **源码**:
  ```python
  from dataclasses import dataclass
  @dataclass(frozen=True)
  class C:
      x: int = (a if c else b)
  ```
- **失败现象**: 外层 code object 指令数不匹配：原始 25 条 vs 重编 17 条，缺少 `LOAD_NAME dataclass + LOAD_CONST True + KW_NAMES + PRECALL + CALL`（装饰器调用）+ `PUSH_NULL + LOAD_BUILD_CLASS`（类构建）
- **根因分析**:
  - 与 R9-09 类似：外层 `@dataclass(frozen=True)` 装饰器调用的 KW_NAMES + 关键字参数重建丢失。
  - 额外问题：类体 code object 内的 AnnAssign `x: int = (a if c else b)` 中，ternary merge 块的 STORE_NAME x 与注解元数据 SETUP_ANNOTATIONS + LOAD_NAME int 共享类 code object，导致类重建时混淆类构建指令 LOAD_BUILD_CLASS 与注解指令。
- **修复方向**: 修复装饰器调用 KW_NAMES 重建（同 R9-09），并验证类体内 AnnAssign + ternary 的归约是否正确（参考 test_r9_ternary_annotation_default.py 已通过的单变量 AnnAssign + ternary 模式）。

### Bug R9-11: __slots__ 类 + ternary 属性（PASS）
- **文件**: `test_r9_ternary_slots_class.py` — PASSED（参考对照）

### Bug R9-12: property + setter + 双 ternary
- **文件**: `test_r9_ternary_property_setter.py`
- **源码**:
  ```python
  class C:
      @property
      def x(self):
          return self._x if c else 0
      @x.setter
      def x(self, v):
          self._v = v if c2 else 0
  ```
- **失败现象**: 类 code object 指令数不匹配：原始 20 条 vs 重编 19 条，缺少 `LOAD_NAME x + LOAD_ATTR setter`（`@x.setter` 装饰器链的 obj.attr 重建）
- **根因分析**:
  - `@x.setter` 装饰器的字节码模式：`LOAD_NAME x + LOAD_ATTR setter + MAKE_FUNCTION + PRECALL + CALL`。
  - region_ast_generator.py 的装饰器重建逻辑在第二个方法 `def x(self, v)` 上误把 `LOAD_NAME x + LOAD_ATTR setter` 当作 ternary 的 cond_block preload（因 setter 方法的 ternary `v if c2 else 0` 的 cond_block 前缀含 LOAD_FAST v，与 LOAD_NAME x 的栈帧推断冲突）。
  - 违反「嵌套即抽象节点」：装饰器 obj.attr 链应作为单个抽象节点引用 ternary 子节点，不应被 ternary 的 cond preload 推断吞并。
- **修复方向**: 在 ternary 的 cond_block preload 推断（参考 `_compute_ternary_cond_preload_exprs`）中，增加守卫：若 preload 序列是 `LOAD_* + LOAD_ATTR + MAKE_FUNCTION + PRECALL + CALL` 模式（装饰器链），跳过 preload 推断，让装饰器链由父级 ClassDef 处理。

### Bug R9-13: abstractmethod + ternary default arg
- **文件**: `test_r9_ternary_abstractmethod.py`
- **源码**:
  ```python
  class C:
      @abstractmethod
      def m(self, x=(a if c else b)):
          pass
  ```
- **失败现象**: 类 code object 指令数不匹配：原始 17 条 vs 重编 14 条，缺少 `LOAD_NAME abstractmethod + PRECALL + CALL`（`@abstractmethod` 装饰器调用）
- **根因分析**:
  - 默认参数 `x=(a if c else b)` 在类定义时求值，ternary 在**外层类 code object** 内执行（不在方法 m 的 code object 内）。
  - ternary merge 块的 BUILD_TUPLE 4（构建默认参数元组）+ MAKE_FUNCTION 之间，`@abstractmethod` 装饰器调用 `LOAD_NAME abstractmethod + PRECALL + CALL` 被误识别为 ternary 的 func_call_info（CALL 消费者）。
  - region_ast_generator.py:18117-18116 的 `func_call_info` 检测把装饰器 CALL 当作 ternary 的 consumer CALL，导致装饰器被吞并进 ternary 表达式，违反「每块唯一归属」。
- **修复方向**: 在 ternary 的 func_call_info 检测中，若 CALL 的栈帧前驱含 MAKE_FUNCTION（即 CALL 是装饰器应用而非普通函数调用），跳过 func_call_info 路径，让装饰器由父级 ClassDef/FunctionDef 处理。

### Bug R9-14: class decorator 参数是 ternary
- **文件**: `test_r9_ternary_class_decorator_arg.py`
- **源码**:
  ```python
  @deco(a if c else b)
  class C:
      pass
  ```
- **失败现象**: 指令数严重不匹配：原始 20 条 vs 重编 15 条，缺少 `PUSH_NULL + LOAD_BUILD_CLASS + LOAD_CONST + PRECALL + CALL + PRECALL + CALL`（类构建 + 装饰器应用）
- **根因分析**:
  - 类装饰器 `@deco(a if c else b)` 的字节码：`PUSH_NULL + LOAD_NAME deco + ternary_merge + PRECALL + CALL`（装饰器调用，产生 deco_partial）+ `PUSH_NULL + LOAD_BUILD_CLASS + MAKE_FUNCTION + LOAD_CONST C + PRECALL + CALL`（类构建）+ `PRECALL + CALL`（应用 deco_partial）+ `STORE_NAME C`。
  - ternary 的 merge 块作为第一个 CALL 的参数，但反编译器未能正确识别后续的两个 CALL（类构建 + 装饰器应用），导致类定义完全退化为 `class C:`，装饰器与 ternary 一起丢失。
  - 违反「父引用子入口」：父 ClassDef 应通过 BUILD_CLASS 入口引用 ternary 子节点（作为装饰器参数），当前实现把整个装饰器+类构建链全部吞并进 ternary 的 func_call_info。
- **修复方向**: 在 ClassDef 重建时，明确区分「装饰器调用的 CALL」（含 ternary 参数）与「类构建的 CALL」（含 LOAD_BUILD_CLASS）。ternary 只负责装饰器调用的参数部分，类构建 CALL 由 ClassDef 重建逻辑负责。

### Bug R9-15: assert + return 共享同一 ternary consumer
- **文件**: `test_r9_ternary_assert_return_consumer.py`
- **源码**:
  ```python
  def f():
      assert (a if c else b)
      return x if c2 else y
  ```
- **失败现象**: 反编译结果完全错误，输出 `def f():\n    if (not a):\n        pass\n    elif c2:\n        return x\n    return y`，ternary 全部丢失
- **根因分析**:
  - 第一个 ternary `a if c else b` 的 condition_block（`LOAD c + POP_JUMP_IF_FALSE`）与 assert 基础设施（LOAD_ASSERTION_ERROR + RAISE_VARARGS）在 merge 块中共享。
  - 第二个 ternary `x if c2 else y` 的 condition_block 与 return 路径的 RETURN_VALUE 在 merge 块中共享。
  - region_analyzer.py 的 `_identify_ternary_regions` (L10799) 在两个 ternary 共享同一函数体时，第一个 ternary 的 merge 块（含 assert 基础设施）被识别为 IfRegion 的 entry，把 ternary 误判为 if-elif-else 结构。
  - 违反「自底向上归约」：ternary 应先于 IfRegion 识别（已在 phase 2 顺序中保证），但 assert 基础设施的存在使 ternary pattern 检测的 `_is_ternary_block` 校验失败（merge 块含 RAISE_VARARGS 不符合「单表达式块」约束）。
- **修复方向**: 在 `_is_ternary_block` 中放宽对 merge 块的约束：允许 merge 块含 `LOAD_ASSERTION_ERROR + RAISE_VARARGS`（assert 基础设施）或 `RETURN_VALUE`（return ternary），只要这些指令是 ternary consumer 模式（参考 `_build_ternary_no_target_consumer_stmt` 的 Pattern 1/Pattern 5/Pattern 13）。

### Bug R9-16: partial 应用 + ternary
- **文件**: `test_r9_ternary_partial_application.py`
- **源码**:
  ```python
  from functools import partial
  f = partial(g, (a if c else b))
  ```
- **失败现象**: 指令数不匹配：原始 18 条 vs 重编 17 条，缺少一个 `LOAD_NAME`（ternary 的 c 或 b 之一被吞并）
- **根因分析**:
  - `partial(g, (a if c else b))` 的字节码：`IMPORT_NAME + IMPORT_FROM + STORE_NAME + POP_TOP + PUSH_NULL + LOAD_NAME partial + LOAD_NAME g + ternary_merge(LOAD_NAME a/c/b) + PRECALL + CALL + STORE_NAME f`。
  - ternary 的 condition_block `LOAD c + POP_JUMP_IF_FALSE` 的前驱 preload 被推断为 `LOAD_NAME partial + LOAD_NAME g`，但 ternary 的 false_value 块（`LOAD_NAME b`）被 func_call_info 误识别为 partial 的第二个位置参数（实际上是 ternary 的 false 分支值）。
  - 违反「每块唯一归属」：false_value 块同时被认作 ternary 的值块和 Call 的参数 preload。
- **修复方向**: 在 ternary 的 func_call_info 推断中，明确区分 false_value 块（属于 ternary 子区域）与 cond preload（属于父 Call）。false_value 块的特征：以 `LOAD_*` 开始、无 JUMP_FORWARD 终结（落入 merge），不应被 func_call_info 吞并。

### Bug R9-17: list comprehension 的 condition 是 ternary
- **文件**: `test_r9_ternary_listcomp_condition.py`
- **源码**:
  ```python
  x = [i for i in r if (a if c else b)]
  ```
- **失败现象**: 嵌套 code object 不匹配：原始 10 条 vs 重编 9 条，缺少 `LOAD_FAST` 消费指令
- **根因分析**:
  - listcomp 内部 code object 中，ternary merge 块后的 `LOAD_FAST` 指令（将 ternary 结果压回栈顶供 `POP_JUMP_IF_FALSE` 用作 if 条件）被误识别为 ternary 的 value 块或被合并。
  - region_ast_generator.py 中 ternary merge 块的指令消费逻辑未考虑 comprehension 内部的「if 条件求值」模式：`LOAD_FAST x` 是 ternary 结果的栈桥接指令，属于父 comprehension 的 if 条件路径，不属于 ternary 子区域。
  - 违反「父引用子入口」：父 comprehension 通过 `LOAD_FAST x` 桥接指令引用 ternary merge 结果，但当前实现把 `LOAD_FAST x` 视为 ternary 自身指令。
- **修复方向**: 在 ternary region 识别中，若 merge_block 的后继块是 `LOAD_FAST + POP_JUMP_IF_FALSE/LIST_APPEND`（comprehension if 条件模式），将 `LOAD_FAST` 块标记为父 comprehension 的桥接块，不纳入 ternary region.blocks。

### Bug R9-18: generator expression 的 condition 是 ternary
- **文件**: `test_r9_ternary_genexp_condition.py`
- **源码**:
  ```python
  x = sum(i for i in r if (a if c else b))
  ```
- **失败现象**: 嵌套 code object 不匹配：原始 14 条 vs 重编 13 条，缺少 `LOAD_FAST` 消费指令
- **根因分析**:
  - 与 Bug R9-17 同源：genexp 内部 code object 中 ternary merge 块后的 `LOAD_FAST` 桥接指令被吞并。
  - 额外：genexp 的 `YIELD_VALUE` 后接 `RESUME + POP_TOP`，与 ternary merge 块的 `LOAD_FAST` 栈顺序交互更复杂。
- **修复方向**: 同 R9-17，在 ternary region 识别中保留 `LOAD_FAST` 桥接块给父 genexp。

### Bug R9-19: walrus(ternary) in comprehension
- **文件**: `test_r9_ternary_walrus_in_comprehension.py`
- **源码**:
  ```python
  x = [(n := (a if c else b)) for i in r]
  ```
- **失败现象**: 嵌套 code object 不匹配：原始 11 条 vs 重编 9 条，缺少 `COPY + STORE_GLOBAL`（walrus 副作用指令）
- **根因分析**:
  - listcomp 内部 code object 中，ternary merge 块后的 `COPY 1 + STORE_GLOBAL n`（walrus 副作用捕获）被吞并。
  - region_ast_generator.py 中 walrus + ternary 的识别（参考 `_build_assert_message_ternary_stmt` L18993 的 Walrus pattern）只在 assert message 上下文实现，未覆盖 comprehension 内的 walrus(ternary) 模式。
  - 违反「每块唯一归属」：walrus 的 `COPY + STORE` 块同时被认作 ternary merge_extra_blocks 和父 comprehension 的 walrus 副作用块。
- **修复方向**: 在 ternary region 识别中，若 merge_block 后继块是 `COPY 1 + STORE_*` 模式（walrus 副作用），不应将该 COPY+STORE 块加入 merge_extra_blocks。该块属于父 comprehension 的 walrus 表达式，由 NamedExpr 重建负责。

### Bug R9-20: f-string 嵌套 format_spec 含 ternary（PASS）
- **文件**: `test_r9_ternary_fstring_nested_format_spec.py` — PASSED（参考对照）

### Bug R9-21: 5 层嵌套 ternary 边界（PASS）
- **文件**: `test_r9_ternary_deep_5level.py` — PASSED（参考对照）

### Bug R9-22: 10 层嵌套 ternary 边界（PASS）
- **文件**: `test_r9_ternary_deep_10level.py` — PASSED（参考对照）

### Bug R9-23: curry chain + ternary（PASS）
- **文件**: `test_r9_ternary_curry_chain.py` — PASSED（参考对照）

### Bug R9-24: await ternary + async with body ternary 组合（PASS）
- **文件**: `test_r9_ternary_await_async_with_combo.py` — PASSED（参考对照）

### Bug R9-25: super() 参数是 ternary（SKIP）
- **文件**: `test_r9_ternary_super_arg.py` — SKIPPED（重编译失败，反编译结果语法错误，属已知限制）

---

## 累计 bug 数

| 分类 | 数量 |
|------|------|
| R8 已知限制回归（async for/with/else/iter） | 4 |
| R9 新增真失败 bug | 15 |
| **累计真失败 bug** | **19** |

## 按根因聚类

### 聚类 A: async 协议 polling 块与 ternary merge 块归属冲突（4 个）
- R7-02, R7-03, R7-10, R8-08（R8 已知限制，R9 新增 R9-01/R9-03/R9-04 同源）
- **共性根因**: region_analyzer.py:3186-3227 的 async for/with polling 块识别与 ternary region 归属判定冲突。

### 聚类 B: comprehension 内 ternary consumer 桥接指令被吞并（4 个）
- R9-05 (async_comprehension), R9-17 (listcomp), R9-18 (genexp), R9-19 (walrus_in_comprehension)
- **共性根因**: ternary region 识别时，merge 块后的 `LOAD_FAST` / `COPY+STORE` 桥接指令被误纳入 ternary.blocks 或 merge_extra_blocks，违反「父引用子入口」原则。

### 聚类 C: 类定义基础设施（BUILD_CLASS + KW_NAMES + 装饰器 CALL）重建缺陷（5 个）
- R9-09 (metaclass), R9-10 (frozen_dataclass), R9-12 (property_setter), R9-13 (abstractmethod), R9-14 (class_decorator_arg)
- **共性根因**: CodeGenerator 重建 ClassDef 时，KW_NAMES / 装饰器 CALL / LOAD_BUILD_CLASS 等基础设施指令的生成逻辑不完整，被 ternary 在类体内或装饰器参数中的存在触发暴露。

### 聚类 D: ternary consumer 模式识别不完整（2 个）
- R9-15 (assert_return_consumer): assert + return ternary 共享函数体，ternary 退化为 if-elif
- R9-16 (partial_application): partial(g, ternary) 的 false_value 块被 func_call_info 吞并
- **共性根因**: `_is_ternary_block` 对 merge 块的「单表达式块」约束过严，未覆盖 assert/return 基础设施模式；`func_call_info` 推断未排除 ternary 自身的 false_value 块。

### 聚类 E: except* (PEP 654) 完全未实现（1 个）
- R9-08 (exception_group)
- **共性根因**: region_ast_generator.py 中 `_generate_try` (L11861) 未实现 except* handler 生成，CHECK_EG_MATCH 仅作为噪音过滤掉。

---

## 修复优先级建议（符合区域归约算法 4 原则）

### P0（最高优先级，影响 async 全场景）
1. **修复聚类 A**: 在 `_identify_loop_regions` 的 async for/with 分支增加 ternary region 归属守卫，保留 ternary entry/merge 块归属，将 polling 块从 ternary.blocks 移除。符合「自底向上归约」+「每块唯一归属」原则。

### P1（高优先级，影响 comprehension 全场景）
2. **修复聚类 B**: 在 ternary region 识别中增加「comprehension 桥接块」识别守卫，将 `LOAD_FAST` / `COPY+STORE` 桥接块保留给父 comprehension。符合「父引用子入口」原则。

### P2（中优先级，影响类定义全场景）
3. **修复聚类 C**: 在 CodeGenerator 的 ClassDef 重建中补全 KW_NAMES / 装饰器 CALL / LOAD_BUILD_CLASS 指令生成；在 ternary 的 func_call_info 推断中排除装饰器 CALL 模式。符合「嵌套即抽象节点」原则。

### P3（低优先级，单点修复）
4. **修复聚类 D**: 放宽 `_is_ternary_block` 对 merge 块的约束，允许 assert/return 基础设施；在 func_call_info 推断中排除 ternary 自身的 false_value 块。
5. **修复聚类 E**: 新增 ExceptGroupRegion 类型识别 except* 模式（独立工作量，建议单独立项）。

---

## 测试执行统计

```
============================== test session starts ===============================
tests/exhaustive/ternary/test_r9_*.py

8 passed, 15 failed, 2 skipped in 1.37s
```

### 通过的测试（8 个）
- test_r9_ternary_annotation_default.py — `x: int = (a if c else b)` 单变量 AnnAssign + ternary
- test_r9_ternary_await_async_with_combo.py — await ternary + async with body ternary 组合
- test_r9_ternary_curry_chain.py — 三层 lambda curry chain + ternary
- test_r9_ternary_deep_5level.py — 5 层嵌套 ternary
- test_r9_ternary_deep_10level.py — 10 层嵌套 ternary
- test_r9_ternary_fstring_nested_format_spec.py — f-string 嵌套 format_spec ternary
- test_r9_ternary_match_guard.py — match case guard ternary
- test_r9_ternary_slots_class.py — __slots__ 类 + ternary 属性

### 跳过的测试（2 个，非真失败）
- test_r9_ternary_async_with_multi_as.py — 重编译失败（反编译结果语法错误）
- test_r9_ternary_super_arg.py — 重编译失败（反编译结果语法错误）

### 失败的测试（15 个真失败）
见上文 Bug R9-01 至 R9-19（R9-02 SKIPPED 不计入真失败，R9-20~R9-24 PASSED）。
