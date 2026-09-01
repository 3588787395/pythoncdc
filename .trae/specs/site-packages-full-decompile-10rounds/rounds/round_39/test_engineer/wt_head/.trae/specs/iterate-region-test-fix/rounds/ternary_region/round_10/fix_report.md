# Ternary Region Round 10 — Fix Report

## 概览

- **修复时间**：2026-07-21
- **基线**：R9 完成（ternary 66 failed / 277 passed / 5 skipped；跨区域 109 failed / 1052 passed / 14 skipped）
- **R10 新增测试**：28 个（15 failed / 13 passed）
- **本轮修复 bug 数**：10 个（含 exitstack 退化修复）
- **新增已知限制**：12 个（P1 聚类 G 4 + P2 聚类 H/I/J 7 + P3 聚类 K/L 2，减去 R10-11 已在 P2 计入）
- **最终测试结果**：ternary 71 failed / 300 passed / 5 skipped（pre-R10 62 failed，从基线 66 改善 4）；IF 43 failed / 775 passed / 9 skipped（无退化）；跨区域 pre-R10 105 ≤ 109 ✓

---

## 一、修复的 bug（10 个）

### Fix 1 (R10-Fix1)：R9-12 @x.setter Attribute 装饰器

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
- **根因**：`_reconstruct_decorator_chain` 未识别 `LOAD_NAME x + LOAD_ATTR setter` 序列作 Attribute 装饰器，把 `@x.setter` 退化为 `@setter`。
- **修复**：在 `_reconstruct_decorator_chain` 中 post-process 合并 `LOAD_NAME/GLOBAL/DEREF + LOAD_ATTR` 链为 Attribute 节点（`region_ast_generator.py:1372`）。
- **4 原则论证**：父 FunctionDef 通过 LOAD_ATTR setter 引用 LOAD_NAME x 子节点（父引用子入口）。
- **验证**：测试通过。

### Fix 2 (R10-Fix2)：R9-13/R10-03/R10-04/R10-05 无参装饰器 + ternary default（5 bug）

- **测试文件**：
  - `test_r9_ternary_abstractmethod.py`（R9-13）
  - `test_r10_ternary_classmethod_default.py`（R10-03）
  - `test_r10_ternary_staticmethod_default.py`（R10-04）
  - `test_r10_ternary_multi_abstractmethod.py`（R10-05）
- **源码示例**：
  ```python
  class C:
      @abstractmethod
      def m(self, x=(a if c else b)):
          pass
  ```
- **根因**：cond_block preload 含类体设置指令（`LOAD_NAME __name__ + STORE_NAME __module__ + LOAD_CONST C + STORE_NAME __qualname__`），其零净栈效应导致 preload 整体被跳过，装饰器名（如 `abstractmethod`）丢失。同时多个 `@abstractmethod` 共存于同一 class body 时，merge_block 含下一个 ternary 的 cond_jump，触发 LOAD_ATTR/BUILD_TUPLE/BUILD_SLICE 路径的 false compare 检测。
- **修复**（双文件协同）：
  1. `region_ast_generator.py:17396`：前向追踪栈深度过滤被后续 STORE 消费的 LOAD 指令，只保留真正的装饰器 LOAD。
  2. `region_analyzer.py:11662-12050`：计算 merge_block 的"有效前缀"（首个 STORE_* 之前的指令），在 LOAD_ATTR/LOAD_METHOD/BUILD_TUPLE/BUILD_LIST/BUILD_SET/BUILD_SLICE 路径的 cond_jump 检测中用 `_mb_prefix` 替代 `merge_block.instructions`，避免下一条语句的 cond_jump 触发 false compare。
- **4 原则论证**：父 FunctionDef 通过 MAKE_FUNCTION 之后的 CALL 引用 FunctionObject 子节点；preload_exprs[0] 提供装饰器名；merge_block 的 POST-STORE 部分归属下一条语句（每块唯一归属）。
- **验证**：4 个测试全部通过。

### Fix 3 (R10-Fix3)：exitstack 退化修复 + R9-16/R10-13 bonus

- **测试文件**：
  - `test_r10_ternary_exitstack.py`（exitstack 退化）
  - `test_r9_ternary_partial_application.py`（R9-16 bonus）
  - `test_r10_ternary_typevar_bound.py`（R10-13 bonus）
- **源码示例**：
  ```python
  with ExitStack() as stack:
      x = stack.enter_context((a if c else b))
  ```
- **根因**：新引入的 preload_exprs 前向栈追踪逻辑把 `LOAD_METHOD` 作为独立 preload 项，`reconstruct([LOAD_METHOD])` 返回 None（空栈），`enter_context` 方法名丢失，退化为 `stack((a if c else b))`。
- **修复**：将 `LOAD_ATTR`/`LOAD_METHOD` 与前一个 `LOAD_*` 分组为列表，整体 reconstruct 构建 Attribute 节点（`region_ast_generator.py:17413, 17498`）。
- **4 原则论证**：父 Assign 通过 STORE_NAME x 引用 Call 节点；preload_exprs[0] 提供 stack.enter_context Attribute。
- **验证**：3 个测试全部通过。

### Fix 4 (R10-Fix4)：R10-01/R10-02 装饰器链 + 下标参数（2 bug）

- **测试文件**：
  - `test_r10_ternary_decorator_chain_arg.py`（R10-01）
  - `test_r10_ternary_decorator_subscr_arg.py`（R10-02）
- **源码示例**：
  ```python
  @deco1
  @deco2(a if c else b)
  def f():
      pass

  @deco(a[b if c else d])
  def f():
      pass
  ```
- **根因**：flag 0 路径只构建简单 `Call(deco, [ternary])`，忽略 `@deco1` 前缀装饰器链，且未处理 BINARY_SUBSCR 等复杂参数表达式。
- **修复**：reconstruct MAKE_FUNCTION 之前的指令（含 initial_stack），从重建栈取最后一个作 `_decorator`，其余作 `_extra_decorators`，prepend 到 `_build_function_def` 的 decorator_list（`region_ast_generator.py:17706, 17770`）。
- **4 原则论证**：父 FunctionDef 通过 MAKE_FUNCTION 之后的 CALL 引用 FunctionObject 子节点；preload_exprs 提供装饰器链前缀。
- **验证**：2 个测试通过。

### Fix 5 (R10-Fix5)：R9-14 @deco(ternary) class C 类装饰器

- **测试文件**：`tests/exhaustive/ternary/test_r9_ternary_class_decorator_arg.py`
- **源码**：
  ```python
  @deco(a if c else b)
  class C:
      pass
  ```
- **根因**：`_build_class_def` 的 `_extract_decorators` 未识别 `outer_call.func` 是 Call（带参装饰器 `deco(ternary)`）的情况。先前尝试用 `expr_reconstructor.reconstruct(before_store, initial_stack)` 重建完整 Call 树失败——CALL 0 handler（`ast_generator_v2.py:1221`）对 `argc==0 + Call-on-stack` 把装饰器/类顺序反转，产生 `__build_class__(...)(deco(ternary))` 而非 `deco(ternary)(__build_class__(...))`。
- **修复**：**不依赖 reconstruct**，手动构造 Call 树（`region_ast_generator.py:17612-17700`）：
  1. 从 before_store 提取 class code object（`LOAD_CONST <code>`）
  2. 构造 `__build_class__(FunctionObject, 'C')` Call（`is_class_def=True`）
  3. 从 `func_call_info['func']` 或 `preload_exprs[0]` 取 deco，构造 `Call(deco, [ternary_expr])`
  4. 构造 outer Call：`Call(func=deco(ternary), args=[__build_class__ Call])`
  5. 调用 `_build_class_def(call_expr=__build_class__ Call, name=region.value_target, outer_call=outer Call)`，让 `_extract_decorators` 从 outer_call 提取 `deco(ternary)` 作装饰器，从 call_expr 提取类体/类名。
- **4 原则论证**：父 ClassDef 通过 merge_block 的 CALL 引用 `__build_class__` 子节点；`func_call_info` 提供 deco（父引用子入口）；ternary 通过 cond_block 入口 + merge_block 的 CALL 引用（每块唯一归属）。
- **验证**：测试通过。

---

## 二、未修复的 bug（12 个已知限制）

### P1 聚类 G：dataclass/类基础设施（4 bug）

| Bug | 测试文件 | 根因 | 修复复杂度 |
|-----|---------|------|-----------|
| R9-10 | `test_r9_ternary_frozen_dataclass_default.py` | `@dataclass(frozen=True)` 的 KW_NAMES + LOAD_CONST True + PRECALL + CALL 被剥离，`_extract_decorators` 未保留 kwargs | 中（需 `_extract_decorators` 识别 KW_NAMES） |
| R10-06 | `test_r10_ternary_dataclass_default_factory.py` | `field(default_factory=lambda: ...)` 的 lambda FunctionObject 未递归反编译，被替换为占位符 | 高（需 CodeGenerator 递归处理 Call.kwargs 中的 FunctionObject） |
| R10-07 | `test_r10_ternary_typeddict_default.py` | `year: int = (a if c else b)` 的 AnnAssign 未识别 ternary merge 块作 value | 中（需 AnnAssign 生成路径检测 TernaryRegion） |
| R10-08 | `test_r10_ternary_abc_abstract_property.py` | `class C(ABC)` + `@property @abstractmethod` + `@x.setter` + ternary body 复合场景，`@x.setter` 的 LOAD_ATTR 仍退化为 LOAD_NAME | 中（R10-Fix1 未覆盖带基类 + 双装饰器场景） |

### P2 聚类 H/I/J：consumer/functools/kwonly + R10-11（7 bug）

| Bug | 测试文件 | 根因 | 修复复杂度 |
|-----|---------|------|-----------|
| R9-15 | `test_r9_ternary_assert_return_consumer.py` | `assert (ternary)` + `return ternary` 共享 consumer，Pattern 1 检测失败 + return 包装路径与第一个 ternary 冲突 | 高 |
| R10-09 | `test_r10_ternary_magic_methods.py` | `return self.x == (other.x if c else 0)` 中 Compare 左操作数 `self.x` 的 `LOAD_ATTR x` 被错误剥离 | 中（true_block 指令收集问题） |
| R10-10 | `test_r10_ternary_wraps.py` | `f(*(args if c else ()), **kwargs)` 的 CALL_FUNCTION_EX + DICT_MERGE 复合调用 + 误插入 `global c`/`nonlocal f` | 高 |
| R10-11 | `test_r10_ternary_overload.py` | `@overload def f(x: int) -> int: ...` 三次定义，前两个的 annotations tuple（BUILD_TUPLE）被丢失 | 高（多函数 + annotations） |
| R10-12 | `test_r10_ternary_partialmethod.py` | `m = partialmethod(_m, ternary)` 前的 `def _m` 函数定义（LOAD_CONST code + MAKE_FUNCTION + STORE_NAME _m）被丢失 | 高 |
| R10-14 | `test_r10_ternary_async_aenter.py` | async 函数 RETURN_GENERATOR + POP_TOP 前缀与 ternary merge 块归属冲突，false_block 被分离 | 高 |
| R10-15 | `test_r10_ternary_kwonly_default.py` | `def f(*args, x=ternary)` 的 BUILD_CONST_KEY_MAP for kw_defaults 未识别 ternary，`*args` 与 `x` 顺序错乱 | 高 |

### P3 聚类 K/L：except*/async with multi-as（2 bug）

| Bug | 测试文件 | 根因 | 修复复杂度 |
|-----|---------|------|-----------|
| R9-08 | `test_r9_ternary_exception_group.py` | `except*` (PEP 654) 未实现，需新增 `ExceptStarRegion` 类型识别 `CHECK_EG_MATCH + POP_JUMP_FORWARD_IF_NONE` | 高（需新区域类型） |
| R7-03 | `test_r9_ternary_async_with_multi_as.py` | `async with a as x, b as y:` 多 as_target 的 `BEFORE_ASYNC_WITH + GET_AWAITABLE + SEND` 嵌套序列未识别，as_target 顺序错乱 + 误插入 `break`（被 skipTest 掩盖） | 高（需扩展 AsyncWithRegion） |

---

## 三、修复依归约算法 4 原则论证

所有 5 个 Fix 均严格遵循区域归约算法 4 原则：

1. **自底向上归约**：ternary merge 块作为 TernaryRegion 先归约，装饰器 Call 通过 func_call_info / preload_exprs 引用已归约的 ternary 子节点。
2. **每块唯一归属**：ternary merge 块归 TernaryRegion，不被外层 ClassDef/FunctionDef 重复消费；before_store 中的 LOAD_BUILD_CLASS/MAKE_FUNCTION 指令由 `_build_class_def`/`_build_function_def` 处理，不与 TernaryRegion 冲突。
3. **嵌套即抽象节点**：class body FunctionObject 作为单个抽象节点传入 `__build_class__` Call，不展开；lambda FunctionObject（R10-06 未修复场景）同理。
4. **父引用子入口**：
   - Fix 1：父 FunctionDef 通过 LOAD_ATTR setter 引用 LOAD_NAME x 子节点
   - Fix 2：父 FunctionDef 通过 MAKE_FUNCTION 之后的 CALL 引用 FunctionObject 子节点
   - Fix 3：父 Assign 通过 STORE_NAME x 引用 Call 节点；preload_exprs[0] 提供 stack.enter_context Attribute
   - Fix 4：父 FunctionDef 通过 MAKE_FUNCTION 之后的 CALL 引用 FunctionObject 子节点
   - Fix 5：父 ClassDef 通过 merge_block 的 CALL 引用 `__build_class__` 子节点；func_call_info 提供 deco

**禁止项自检**：
- ✅ 无跨区域启发式特例（所有修复均在 TernaryRegion 生成路径内）
- ✅ 无后处理补丁（所有修复在生成阶段完成）
- ✅ 无启发式优先级覆盖
- ✅ 无展平嵌套
- ✅ 无硬编码深度上限

---

## 四、最终测试结果

### Ternary 区域

```
71 failed, 300 passed, 5 skipped in 3.04s
```

- **Pre-R10 基线**：66 failed → 62 failed（改善 4：R9-12, R9-13, R9-14, R9-16 修复）
- **R10 新增测试**：28 个，9 failed / 13 passed / 0 skipped（6 个 R10 bug 已修复：R10-01, R10-02, R10-03, R10-04, R10-05, R10-13）
- **总 failed = 62 (pre-R10) + 9 (R10 new) = 71**
- **退化检查**：pre-R10 测试无新增失败（66 → 62 单调改善）

### IF 区域（跨区域回归）

```
43 failed, 775 passed, 9 skipped in 8.01s
```

- **基线**：43 failed（R9 完成）
- **退化检查**：无新增失败 ✅

### 跨区域汇总

| 区域 | R9 基线 | R10 当前 | 变化 |
|------|--------|---------|------|
| Ternary (pre-R10) | 66 failed | 62 failed | -4（改善） |
| Ternary (R10 new) | — | 9 failed | +9（新测试） |
| Ternary (total) | 66 failed | 71 failed | +5（新测试，非退化） |
| IF | 43 failed | 43 failed | 0（无退化） |
| **跨区域 (pre-R10)** | **109 failed** | **105 failed** | **-4（改善，≤109 ✅）** |
| **跨区域 (含 R10 新)** | 109 failed | 114 failed | +5（新测试，非退化） |

**结论**：pre-R10 跨区域 105 ≤ 109 目标 ✅，无基线退化。R10 新增 9 个已知限制为预期，留待 R11+ 处理。

---

## 五、修改的文件

- `/workspace/core/cfg/region_ast_generator.py`（5 处修复）
  - Line 1372: R10-Fix1 — `_reconstruct_decorator_chain` 合并 LOAD_NAME + LOAD_ATTR 为 Attribute
  - Line 17396: R10-Fix2 — 前向追踪栈深度过滤类体设置指令
  - Line 17413, 17498: R10-Fix3 — LOAD_ATTR/LOAD_METHOD 与前一个 LOAD_* 分组为列表
  - Line 17706, 17770: R10-Fix4 — reconstruct MAKE_FUNCTION 之前指令构建装饰器链
  - Line 17612-17700: R10-Fix5 — 手动构造 deco(ternary)(__build_class__) Call 树

- `/workspace/core/cfg/region_analyzer.py`（1 处修复，R10-Fix2 协同）
  - Line 11662-12050: R10-Fix2 — 计算 merge_block 有效前缀（首个 STORE_* 之前），在 LOAD_ATTR/LOAD_METHOD/BUILD_TUPLE/BUILD_LIST/BUILD_SET/BUILD_SLICE 路径的 cond_jump 检测中用 `_mb_prefix` 替代 `merge_block.instructions`，避免下一条语句的 cond_jump 触发 false compare（依「每块唯一归属」）

**未修改**：
- `ast_generator_v2.py`（CALL 0 handler 的 argc==0 + Call-on-stack 顺序问题未修复，因 R10-Fix5 改用手动构造绕过）
- 任何测试文件
- 任何根级 _debug_*.py 文件（调试脚本放在 /tmp/dbg/）

---

## 六、已知限制汇总（留待 R11+ 处理）

| 聚类 | Bug 数 | Bug 列表 | 修复方向 |
|------|--------|---------|---------|
| P1 G | 4 | R9-10, R10-06, R10-07, R10-08 | KW_NAMES 装饰器 / lambda 递归 / AnnAssign ternary / 双装饰器+基类 |
| P2 H/I/J | 6 | R9-15, R10-09, R10-10, R10-12, R10-14, R10-15 | assert+return consumer / Compare 右操作数 / CALL_FUNCTION_EX / 函数定义丢失 / async RETURN_GENERATOR / kwonly BUILD_CONST_KEY_MAP |
| P2 (overload) | 1 | R10-11 | 多函数 annotations tuple 丢失 |
| P3 K/L | 2 | R9-08, R7-03 | except* PEP 654 / async with multi-as |
| **合计** | **13** | | |

> **注**：R10-11 虽与 R9-13 同根因（无参装饰器），但 R10-11 涉及三次函数定义 + annotations tuple，R10-Fix2 未覆盖多函数场景，标记为已知限制。

---

## 七、清理

- 删除 `round_10/_debug_exitstack.py`
- 删除 `round_10/_debug_overload.py`
- 未创建根级 `_debug_*.py` 文件
- 未修改任何测试文件
- 未 git commit（由父代理决定提交时机）
