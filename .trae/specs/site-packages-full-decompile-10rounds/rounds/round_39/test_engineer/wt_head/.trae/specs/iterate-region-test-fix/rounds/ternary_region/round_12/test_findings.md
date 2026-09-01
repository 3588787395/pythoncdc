# Ternary Region Round 12 测试发现报告

## 概览

- **执行日期**: 2026-07-21
- **基线**: R11 已完成（commit 96b23e7），ternary 全量基线 86 failed / 320 passed / 8 skipped
- **测试范围**: 验证 R11 已知限制 + 新增 R12 对抗性测试
- **新建测试文件数**: 15
- **确认真失败 bug 数**: 21（15 个 R11 已知限制 + 6 个 R12 新发现）
- **停止条件**: 累计 21 > 10，已满足停止条件

---

## 一、R11 已知限制回归验证（全部仍失败，15/15）

### R11-01 except* PEP 654 + ternary handler body
- **测试文件**: `tests/exhaustive/ternary/test_r11_ternary_except_star.py`
- **源码**: `try:\n    pass\nexcept* E as e:\n    x = (a if c else b)`
- **失败现象**: `指令数不匹配: 39 vs 29`
- **失败原因**: except* handler 内 PUSH_EXC_INFO + CHECK_EG_MATCH + COPY 路径
  与 ternary merge 块的 STORE_NAME x 在同一 handler body，归约冲突。
- **关键指令差异**: 原始含 PUSH_EXC_INFO + CHECK_EG_MATCH + COPY，重编丢失
  这些 except* 基础设施指令。

### R11-02 frozen dataclass field 默认值 ternary
- **测试文件**: `tests/exhaustive/ternary/test_r11_ternary_frozen_dataclass_default.py`
- **源码**: `@dataclass(frozen=True)\nclass C:\n    x: int = (a if c else b)`
- **失败现象**: `指令数不匹配: 25 vs 17`
- **失败原因**: dataclass 装饰器 + KW_APPS + CALL 栈帧与 AnnAssign ternary
  merge 块 STORE_NAME x 归属冲突。重编丢失 KW_NAMES + frozen=True 调用。

### R11-03 assert + return 共享 ternary consumer
- **测试文件**: `tests/exhaustive/ternary/test_r11_ternary_assert_return_consumer.py`
- **源码**: `def f():\n    assert (a if c else b)\n    return (x if c2 else y)`
- **失败现象**: 反编译输出 `def f():\n    if (not a): pass\n    elif c2: return x\n    return y`
- **失败原因**: assert ternary 与 return ternary 在同一函数体内，反编译器把
  两个 ternary 误展开为 if/elif 结构，丢失 IfExp 节点。

### R11-04 dataclass default_factory lambda ternary
- **测试文件**: `tests/exhaustive/ternary/test_r11_ternary_dataclass_default_factory.py`
- **源码**: `@dataclass\nclass C:\n    x: int = field(default_factory=lambda: (a if c else b))`
- **失败现象**: 反编译输出 `x: int = field(default_factory=(lambda *args, **kwargs: None))`
- **失败原因**: lambda code object 内 ternary 完全丢失，反编译为空 lambda。
  func_call_info 中 lambda 的 ternary 子区域未被引用。

### R11-05 TypedDict + ternary default
- **测试文件**: `tests/exhaustive/ternary/test_r11_ternary_typeddict_default.py`
- **源码**: `class Movie(TypedDict):\n    title: str\n    year: int = (a if c else b)`
- **失败现象**: 嵌套 code object `指令数不匹配: 20 vs 16`
- **失败原因**: TypedDict 类体内 AnnAssign + ternary merge STORE_NAME year
  与 TypedDict 基类 __total__ 注解 STORE_SUBSCR 路径冲突，重编丢失 4 条
  STORE_SUBSCR 指令（TypedDict 元数据写入）。

### R11-06 ABC abstract property + setter + ternary
- **测试文件**: `tests/exhaustive/ternary/test_r11_ternary_abc_abstract_property_setter.py`
- **源码**: `class C(ABC):\n    @property\n    @abstractmethod\n    def x(self): ...\n    @x.setter\n    def x(self, v):\n        self._x = (v if c else 0)`
- **失败现象**: 嵌套 code object `指令数不匹配: 23 vs 25`
- **失败原因**: 双层装饰器链 (@property + @abstractmethod) + @x.setter
  + ternary 赋值。重编多 2 条指令，可能是装饰器链重建时重复 LOAD_NAME。

### R11-07 __eq__/__hash__ + ternary
- **测试文件**: `tests/exhaustive/ternary/test_r11_ternary_magic_methods.py`
- **源码**: `class C:\n    def __eq__(self, other):\n        return self.x == (other.x if c else 0)\n    def __hash__(self):\n        return (hash(self.x) if c else 0)`
- **失败现象**: 嵌套 code object `指令数不匹配: 9 vs 8`
- **失败原因**: __eq__ 内 `self.x == (other.x if c else 0)` 比较表达式
  + ternary。重编丢失 1 条 LOAD_ATTR 指令，可能是 ternary consumer
  pattern 没覆盖 COMPARE_OP 的左操作数 self.x 属性访问。

### R11-08 functools.wraps + ternary in *args
- **测试文件**: `tests/exhaustive/ternary/test_r11_ternary_wraps.py`
- **源码**: `def deco(f):\n    @wraps(f)\n    def g(*args, **kwargs):\n        return f(*(args if c else ()), **kwargs)\n    return g`
- **失败现象**: 反编译输出 `def g(*args, **kwargs):\n    global c\n    nonlocal f\n    return f(**kwargs)`
- **失败原因**: ternary `args if c else ()` 在 *args 展开位置完全丢失。
  反编译器误把 c 当作 global、f 当作 nonlocal 声明（误判 *args ternary
  的 cond_block 含 LOAD_GLOBAL c / LOAD_DEREF f 为声明语句）。

### R11-09 typing.overload + ternary
- **测试文件**: `tests/exhaustive/ternary/test_r11_ternary_overload.py`
- **源码**: `@overload\ndef f(x: int) -> int: ...\n@overload\ndef f(x: str) -> str: ...\ndef f(x):\n    return (a if c else b)`
- **失败现象**: `指令数不匹配: 34 vs 24`
- **失败原因**: 3 个同名 f 定义 + @overload 装饰器。重编丢失 10 条指令，
  可能是 @overload 装饰器重建时丢失 BUILD_TUPLE (类型注解元组)。

### R11-11 async __aenter__ + ternary
- **测试文件**: `tests/exhaustive/ternary/test_r11_ternary_async_aenter.py`
- **源码**: `class C:\n    async def __aenter__(self):\n        self.x = (a if c else b)\n        return self`
- **失败现象**: 嵌套 code object `指令数不匹配: 10 vs 12`
- **失败原因**: async 方法 + RETURN_GENERATOR + ternary merge STORE_ATTR x
  + RETURN_VALUE。重编多 2 条指令，可能是 ternary 误展开为 if/else 引入
  额外 POP_TOP + RETURN_VALUE 路径。

### R11-12 ternary in kwonly default
- **测试文件**: `tests/exhaustive/ternary/test_r11_ternary_kwonly_default.py`
- **源码**: `def f(*args, x=(a if c else b)):\n    pass`
- **失败现象**: 反编译输出 `def f(*x, args):\n    return None`
- **失败原因**: 严重错误！ternary 作为 kwonly 参数 x 的默认值，反编译器
  把 *args 与 x 调换位置（*x, args），完全错误的签名重建。kwonly 默认值
  通过 BUILD_CONST_KEY_MAP 构建，ternary merge 块的栈输出作为
  KW_NAMES + LOAD_CONST ('x',) 的 value。

### R11-21 asynccontextmanager + ternary in body
- **测试文件**: `tests/exhaustive/ternary/test_r11_ternary_asynccontextmanager.py`
- **源码**: `@asynccontextmanager\nasync def cm():\n    x = (a if c else b)\n    yield x`
- **失败现象**: 嵌套 code object `指令数不匹配: 14 vs 9`
- **失败原因**: @asynccontextmanager + async generator + ternary + yield
  四重路径。重编丢失 5 条指令（YIELD_VALUE + ASYNC_GEN_WRAP + RESUME
  + POP_TOP），ternary 后的 yield 完全丢失。

### R11-22 cached_property + ternary
- **测试文件**: `tests/exhaustive/ternary/test_r11_ternary_cached_property.py`
- **源码**: `@cached_property\ndef x(self):\n    return (a if c else b)`
- **失败现象**: 嵌套 code object `指令数不匹配: 16 vs 19`
- **失败原因**: @cached_property 装饰器链 + ternary return。重编多 3 条
  指令（重复 LOAD_NAME cached_property + MAKE_FUNCTION + CALL），与
  R11-22 已知限制描述一致：装饰器链重复识别。

### R11-23 contextlib.suppress + ternary in with item
- **测试文件**: `tests/exhaustive/ternary/test_r11_ternary_contextlib_suppress.py`
- **源码**: `with suppress((E1 if c else E2)):\n    pass`
- **失败现象**: 反编译输出 `with context(): pass`
- **失败原因**: ternary 作为 suppress() 参数 + 整个 suppress(ternary) 作为
  with 上下文管理器。反编译器完全丢失 suppress 调用，输出无意义的
  `context()`。ternary 嵌套在 Call 内 + Call 嵌套在 with 内双重归属冲突。

### R11-24 asyncio.gather + ternary arg
- **测试文件**: `tests/exhaustive/ternary/test_r11_ternary_asyncio_gather.py`
- **源码**: `async def main():\n    return await asyncio.gather((f() if c else g()), h())`
- **失败现象**: 嵌套 code object `指令数不匹配: 23 vs 16`
- **失败原因**: ternary 作为 gather 第一个位置参数 + gather(ternary, h())
  被 await。重编丢失 7 条指令（gather 的两个 CALL 参数），ternary 完全
  丢失，反编译为 `await asyncio.gather(h())`。

---

## 二、R12 新发现对抗性 bug（6 个）

### R12-01 ternary 在 bool op 短路右侧
- **测试文件**: `tests/exhaustive/ternary/test_r12_ternary_bool_or_short_circuit.py`
- **源码**: `r = x or (a if c else b)`
- **失败现象**: 反编译输出 `r = (x or (a if c else b) and a)` — 完全错误！
  多出 `and a` 后缀，bool op 重建错误。
- **失败指令**: `指令数不匹配: 9 vs 11`
  - 原始: `LOAD_NAME x, JUMP_IF_TRUE_OR_POP, LOAD_NAME a, LOAD_NAME c, LOAD_NAME b, STORE_NAME r, ...`
  - 重编: 多出 `JUMP_IF_FALSE_OR_POP, LOAD_NAME a`，反编译器误把
    JUMP_IF_TRUE_OR_POP 后的 ternary 当作 `or` 链 + 额外 `and a` 段。
- **根因**: ternary 识别未消费 `JUMP_IF_TRUE_OR_POP` 短路指令的
  op_chain 上下文，BoolOpRegion 与 TernaryRegion 边界划分错误。
- **影响范围**: 任何 `x or (ternary)` / `x and (ternary)` 短路表达式。

### R12-02 ternary 在 dict literal **-展开位置
- **测试文件**: `tests/exhaustive/ternary/test_r12_ternary_dict_merge_double_star.py`
- **源码**: `{**(a if c else b)}`
- **失败现象**: 反编译输出 `(a if c else b)` — 完全丢失 dict literal！
  原本是 `{**ternary}` dict 解包，反编译为元组表达式。
- **失败指令**: `指令数不匹配: 9 vs 10`
  - 原始: `BUILD_MAP 0, <ternary>, DICT_UPDATE 1, POP_TOP, ...`
  - 重编: 完全没有 BUILD_MAP/DICT_UPDATE，ternary merge 块的栈输出
    被当作独立表达式 POP_TOP。
- **根因**: TernaryRegion 的 container_type 没识别 `dict_update` 模式，
  ternary merge 块的 DICT_UPDATE 1 消费未被还原为 `{**ternary}` 字面量。
- **影响范围**: 任何 `{**(ternary)}` dict literal 解包表达式。

### R12-03 ternary 在 extended slice 多维下标
- **测试文件**: `tests/exhaustive/ternary/test_r12_ternary_extended_slice.py`
- **源码**: `r = x[a:b, c if d else e]`
- **失败现象**: 反编译输出 `r = a[b, c if d else e]` — 完全错误！
  - 第一个 `x` 被替换为 `a`（误把 a:b 切片的起点 a 当作下标对象）
  - 切片 `a:b` 完全丢失
  - 只保留 `c if d else e` 作为单一维度
- **失败指令**: `指令数不匹配: 13 vs 11`
  - 原始: `LOAD_NAME x, LOAD_NAME a, LOAD_NAME b, BUILD_SLICE 2, <ternary>, BUILD_TUPLE 2, BINARY_SUBSCR, ...`
  - 重编: 缺失 BUILD_SLICE + 部分 LOAD_NAME，BUILD_TUPLE 2 收到的元素
    数量错误。
- **根因**: ternary 在 extended slice (BUILD_TUPLE N + BINARY_SUBSCR) 的
  某个维度时，consumer pattern 没处理 BUILD_SLICE + BUILD_TUPLE 组合，
  cond preload 的 LOAD_NAME x 被误并入 ternary cond 表达式。
- **影响范围**: 任何多维下标含 ternary 的表达式，如 numpy 数组索引。

### R12-04 ternary 在 list literal *-展开位置
- **测试文件**: `tests/exhaustive/ternary/test_r12_ternary_list_extend_star.py`
- **源码**: `[*(a if c else b)]`
- **失败现象**: 反编译输出 `(a if c else b)` — 完全丢失 list literal！
  原本是 `[*ternary]` list 解包，反编译为元组表达式。
- **失败指令**: `指令数不匹配: 9 vs 10`
  - 原始: `BUILD_LIST 0, <ternary>, LIST_EXTEND 1, POP_TOP, ...`
  - 重编: 没有 BUILD_LIST/LIST_EXTEND，ternary 被当作独立表达式。
- **根因**: 与 R12-02 同源，TernaryRegion 的 container_type 未覆盖
  `list_extend` 模式（CALL_FUNCTION_EX 路径有 LIST_TO_TUPLE 转换，
  但 list literal 不需要，两种路径未统一）。
- **影响范围**: 任何 `[*(ternary)]` list literal 解包表达式。

### R12-05 ternary 在 max(default=...) kwarg 位置
- **测试文件**: `tests/exhaustive/ternary/test_r12_ternary_max_default.py`
- **源码**: `max(x, default=(a if c else b))`
- **失败现象**: 反编译输出 `max(default=a if c else b)` — 丢失位置参数 `x`！
- **失败指令**: `指令数不匹配: 13 vs 12`
  - 原始: `PUSH_NULL, LOAD_NAME max, LOAD_NAME x, <ternary>, KW_NAMES, PRECALL, CALL, ...`
  - 重编: 缺失 1 条 LOAD_NAME x，positional arg 完全丢失。
- **根因**: `_try_build_ternary_kwarg_call` 假设 cond_block 的 preload
  positional args 不与 ternary 共存（注释 "preload args are rare for
  ternary-as-kwarg and not present in any R9 test case"）。R12 测试发现
  `max(x, default=ternary)` 模式确实需要 preload positional arg `x`，
  但当前实现返回 None 走 fallback，丢失 `x`。
- **影响范围**: 任何 `f(positional, kwarg=ternary)` 形式调用，常见于
  `dict.get(k, default=ternary)`、`min(x, key=ternary)` 等内置函数。

### R12-06 ternary 在 set literal *-展开位置
- **测试文件**: `tests/exhaustive/ternary/test_r12_ternary_set_update_star.py`
- **源码**: `{*(a if c else b)}`
- **失败现象**: 反编译输出 `(a if c else b)` — 完全丢失 set literal！
  原本是 `{*ternary}` set 解包，反编译为元组表达式。
- **失败指令**: `指令数不匹配: 9 vs 10`
  - 原始: `BUILD_SET 0, <ternary>, SET_UPDATE 1, POP_TOP, ...`
  - 重编: 没有 BUILD_SET/SET_UPDATE，ternary 被当作独立表达式。
- **根因**: 与 R12-02/R12-04 同源，container_type 未覆盖 `set_update`
  模式。
- **影响范围**: 任何 `{*(ternary)}` set literal 解包表达式。

---

## 三、统计汇总

### 按 bug 类型分组

| 类型 | 数量 | 编号 |
|------|------|------|
| 装饰器链 + ternary | 5 | R11-02, R11-04, R11-06, R11-22, R11-09 |
| 函数定义/参数 + ternary | 4 | R11-08, R11-12, R11-09, R12-05 |
| async/await + ternary | 4 | R11-11, R11-21, R11-24, (R11-01 except*) |
| 容器 literal 解包 + ternary | 3 | R12-02, R12-04, R12-06 |
| 异常处理 + ternary | 2 | R11-01, R11-23 |
| 类型/类 + ternary | 2 | R11-05, R11-06 |
| bool op 短路 + ternary | 1 | R12-01 |
| slice + ternary | 1 | R12-03 |
| magic method + ternary | 1 | R11-07 |
| control flow + ternary | 1 | R11-03 |
| with + ternary | 1 | R11-23 |

### 修复优先级建议

**高优先级（影响常见代码模式）**:
1. **R12-05** `f(positional, kwarg=ternary)`：max/min/get/sorted 等内置函数常用
2. **R11-12** kwonly default ternary：函数签名错误，影响 API 定义
3. **R11-08** `*(ternary)` in *args：影响 wraps/decorator 通用模式
4. **R12-01** `x or (ternary)` 短路：影响条件赋值常用模式
5. **R11-23** `with suppress(ternary)`：影响异常处理常用模式

**中优先级（影响特定场景）**:
6. **R12-02/R12-04/R12-06** 容器 literal 解包：list/dict/set 解包常用
7. **R12-03** extended slice ternary：numpy/pandas 索引常用
8. **R11-03** assert + return ternary：测试代码常用

**低优先级（影响高级特性）**:
9. **R11-21/R11-24** async + ternary：异步代码
10. **R11-01** except* PEP 654：Python 3.11+ 新语法
11. **R11-22** cached_property：装饰器链重复识别
12. **R11-02/R11-04/R11-05** dataclass/TypedDict + ternary：数据类
13. **R11-06/R11-07** ABC/magic method + ternary：OOP
14. **R11-09** typing.overload：类型注解
15. **R11-11** async __aenter__：async context manager

---

## 四、测试文件清单

### R11 已知限制回归测试（已存在，本轮验证）
- `test_r11_ternary_except_star.py` (R11-01) — FAIL
- `test_r11_ternary_frozen_dataclass_default.py` (R11-02) — FAIL
- `test_r11_ternary_assert_return_consumer.py` (R11-03) — FAIL
- `test_r11_ternary_dataclass_default_factory.py` (R11-04) — FAIL
- `test_r11_ternary_typeddict_default.py` (R11-05) — FAIL
- `test_r11_ternary_abc_abstract_property_setter.py` (R11-06) — FAIL
- `test_r11_ternary_magic_methods.py` (R11-07) — FAIL
- `test_r11_ternary_wraps.py` (R11-08) — FAIL
- `test_r11_ternary_overload.py` (R11-09) — FAIL
- `test_r11_ternary_async_aenter.py` (R11-11) — FAIL
- `test_r11_ternary_kwonly_default.py` (R11-12) — FAIL
- `test_r11_ternary_asynccontextmanager.py` (R11-21) — FAIL
- `test_r11_ternary_cached_property.py` (R11-22) — FAIL
- `test_r11_ternary_contextlib_suppress.py` (R11-23) — FAIL
- `test_r11_ternary_asyncio_gather.py` (R11-24) — FAIL

### R12 新增对抗性测试（本轮创建）
- `test_r12_ternary_dict_get_default.py` — PASS（无新 bug）
- `test_r12_ternary_next_default.py` — PASS（无新 bug）
- `test_r12_ternary_max_default.py` — **FAIL** (R12-05)
- `test_r12_ternary_list_extend_star.py` — **FAIL** (R12-04)
- `test_r12_ternary_dict_merge_double_star.py` — **FAIL** (R12-02)
- `test_r12_ternary_set_update_star.py` — **FAIL** (R12-06)
- `test_r12_ternary_matrix_mul.py` — PASS（无新 bug）
- `test_r12_ternary_power.py` — PASS（无新 bug）
- `test_r12_ternary_floor_div.py` — PASS（无新 bug）
- `test_r12_ternary_shift_left.py` — PASS（无新 bug）
- `test_r12_ternary_aug_assign_attr.py` — PASS（无新 bug）
- `test_r12_ternary_unary_minus.py` — PASS（无新 bug）
- `test_r12_ternary_bool_or_short_circuit.py` — **FAIL** (R12-01)
- `test_r12_ternary_extended_slice.py` — **FAIL** (R12-03)
- `test_r12_ternary_fstring_format_spec.py` — PASS（无新 bug）

---

## 五、结论

R12 测试确认了 **21 个真失败 bug**：
- 15 个 R11 已知限制（全部仍失败，未修复）
- 6 个 R12 新发现 bug（覆盖 bool op 短路、容器 literal 解包、extended slice、kwarg 位置参数等常见模式）

R12 新发现的 6 个 bug 都涉及常见的 Python 代码模式（容器解包、短路表达式、多维下标、内置函数 kwarg），具有较高的修复价值。建议下一轮（R13）优先修复这 6 个新 bug，因为它们的影响范围比部分 R11 已知限制更广。

测试已满足 "10 个以上真失败" 的停止条件，结束 R12 测试。
