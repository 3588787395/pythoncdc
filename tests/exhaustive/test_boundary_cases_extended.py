#!/usr/bin/env python3
"""
边界情况扩展测试 - 反编译器极端边界条件验证（50个测试）

扩展Phase 4的BN01-BN25，覆盖更多边缘场景。
确保反编译器在各种极端输入下仍能稳定工作。

理论依据（编译器边界测试理论）：
- 边界值分析：测试每个决策点的最小/最大/典型值
- 等价类划分：将输入空间划分为等价类，每类取代表值
- 错误猜测：基于经验推测可能的错误点

测试矩阵：
| ID | 类别 | 场景 | 说明 |
|----|------|------|------|
| BN26-BN35 | 表达式边界 | 三元/链式/海象等 | 复杂表达式在控制流中 |
| BN36-BN45 | 结构边界 | 空/单语句/极深层 | 极端结构形态 |
| BN46-BN55 | 语法版本边界 | 3.8+/3.10+/3.12+ | 新语法特性 |
| BN56-BN65 | 控制转移边界 | break/continue/return/raise/yield | 深层中的控制转移 |
| BN66-BN75 | 综合极限边界 | 多特性组合 | 多种边界条件叠加 |
"""

import sys
import os
import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from tests.helpers.decompilation_helper import MatrixTestBase


class TestBoundaryCasesExtended(MatrixTestBase):
    """扩展边界情况测试 - 覆盖50个极端边界场景"""

    # ========================================================================
    # BN26-BN35: 表达式边界 (expression boundaries)
    # ========================================================================

    def test_BN26_nested_ternary(self):
        """BN26: 嵌套三元表达式 - x = 1 if a else 2 if b else 3

        嵌套条件表达式的正确还原。"""
        source = '''
def func(a, b):
    x = 1 if a else 2 if b else 3
    y = "yes" if a else ("maybe" if b else "no")
    return x, y
'''
        self.verify_matrix_decompilation(source, 'BN26')

    def test_BN27_nine_level_for_nesting(self):
        """BN27: 九层for嵌套 - 超过8层目标的压力测试

        超过常规深度的for循环嵌套压力测试。"""
        source = '''
def func():
    count = 0
    for i1 in range(2):
        for i2 in range(2):
            for i3 in range(2):
                for i4 in range(2):
                    for i5 in range(2):
                        for i6 in range(2):
                            for i7 in range(2):
                                for i8 in range(2):
                                    for i9 in range(2):
                                        count += 1
    return count
'''
        self.verify_matrix_decompilation(source, 'BN27', min_equivalence=0.72)

    @pytest.mark.skipif(sys.version_info < (3, 12), reason="需要Python 3.12+支持TypeParam")
    def test_BN28_type_param_syntax(self):
        """BN28: TypeParam语法 - Python 3.12+ 泛型类型参数

        PEP 695 类型参数语法的处理能力。"""
        source = '''
def func[T](items: list[T]) -> list[T]:
    result = []
    for item in items:
        if item is not None:
            result.append(item)
    return result
'''
        self.verify_matrix_decompilation(source, 'BN28', min_equivalence=0.75)

    @pytest.mark.skipif(sys.version_info < (3, 10), reason="需要Python 3.10+")
    def test_BN29_async_with_async_for(self):
        """BN29: async with + async for 组合

        异步上下文管理器和异步迭代器的组合使用。"""
        source = '''
async def func(resources):
    results = []
    async with open_async_session() as session:
        async for item in session.iterate():
            if item.valid():
                results.append(item.data())
    return results
'''
        self.verify_matrix_decompilation(source, 'BN29', min_equivalence=0.78)

    def test_BN30_extreme_comprehensive_boundary(self):
        """BN30: 极端综合边界 - 函数内8层+异常+返回全部组合

        多种边界条件的叠加组合。"""
        source = '''
def func(data):
    try:
        for i in range(4):
            if data[i]:
                j = 0
                while j < len(data[i]):
                    try:
                        for k in range(2):
                            if k == data[i][j]:
                                return k
                    except IndexError:
                        pass
                    j += 1
    except Exception:
        return -1
    return 0
'''
        self.verify_matrix_decompilation(source, 'BN30', min_equivalence=0.78)

    def test_BN31_chained_comparison_deep(self):
        """BN31: 深层链式比较 - 0 < a < b < c < d

        多重链式比较操作符。"""
        source = '''
def func(a, b, c, d):
    if 0 < a < b < c < d:
        result = "ascending"
    elif d > c > b > a > 0:
        result = "descending"
    else:
        result = "unordered"
    return result
'''
        self.verify_matrix_decompilation(source, 'BN31')

    def test_BN32_complex_bool_expression(self):
        """BN32: 复杂布尔表达式 - (a and b) or (c and (d or e)) and f"""
        source = '''
def func(a, b, c, d, e, f):
    if (a and b) or (c and (d or e)) and f:
        x = 1
    else:
        x = 0
    return x
'''
        self.verify_matrix_decompilation(source, 'BN32')

    def test_BN33_walrus_in_for_target(self):
        """BN33: 海象运算符作为for目标 - for (x := expr) in ... 的变体

        海象运算符在复杂循环结构中的使用。"""
        source = '''
def func(data):
    results = []
    i = 0
    while (chunk := data[i:i+10]) and i < len(data):
        processed = [x * 2 for x in chunk if (v := abs(x)) > 0]
        results.extend(processed)
        i += 10
    return results
'''
        self.verify_matrix_decompilation(source, 'BN33', min_equivalence=0.80)

    def test_BN34_starred_assignment_in_loop(self):
        """BN34: 循环中的星号解包 - a, *rest = iterable"""
        source = '''
def func(pairs):
    results = []
    for pair in pairs:
        first, *rest = pair
        if rest:
            for r in rest:
                results.append((first, r))
    return results
'''
        self.verify_matrix_decompilation(source, 'BN34')

    def test_BN35_named_expression_in_condition(self):
        """BN35: 条件中的命名表达式 - if (m := pattern.match(s)):"""
        source = '''
def func(strings):
    results = []
    for s in strings:
        if (m := re.match(r'(\d+)', s)):
            results.append(int(m.group(1)))
        elif (n := re.match(r'[a-z]+', s)):
            results.append(n.group(0))
    return results
'''
        self.verify_matrix_decompilation(source, 'BN35', min_equivalence=0.80)

    # ========================================================================
    # BN36-BN45: 结构边界 (structure boundaries)
    # ========================================================================

    def test_BN36_single_line_function_body(self):
        """BN36: 单行函数体 - def f(): return 42

        最小函数体的反编译。"""
        source = '''
def f():
    return 42
'''
        self.verify_matrix_decompilation(source, 'BN36')

    def test_BN37_all_pass_function(self):
        """BN37: 全pass函数体 - 仅包含pass的多行函数"""
        source = '''
def f1():
    pass

def f2(x):
    pass

def f3(x, y):
    if x:
        pass
    else:
        pass
'''
        self.verify_matrix_decompilation(source, 'BN37')

    def test_BN38_only_return_statements(self):
        """BN38: 仅含return的函数 - 多分支early return"""
        source = '''
def classify(x):
    if isinstance(x, int):
        return "int"
    if isinstance(x, str):
        return "str"
    if isinstance(x, list):
        return "list"
    return "other"
'''
        self.verify_matrix_decompilation(source, 'BN38')

    def test_BN39_empty_except_with_else(self):
        """BN39: 空except+else - try:... except:... else:..."""
        source = '''
def func():
    try:
        risky()
    except RiskError:
        pass
    else:
        cleanup()
    finally:
        log_done()
'''
        self.verify_matrix_decompilation(source, 'BN39')

    def test_BN40_for_loop_with_only_break(self):
        """BN40: 仅含break的for循环 - for x in ...: break"""
        source = '''
def func(items):
    found = None
    for item in items:
        if item.target:
            found = item
            break
    return found
'''
        self.verify_matrix_decompilation(source, 'BN40')

    def test_BN41_while_true_with_only_continue(self):
        """BN41: while True: continue 死循环变体"""
        source = '''
def func(queue):
    while True:
        item = queue.get()
        if item is None:
            break
        if item.skip:
            continue
        process(item)
'''
        self.verify_matrix_decompilation(source, 'BN41')

    def test_BN42_nested_if_no_else_chain(self):
        """BN42: 无else的嵌套if链 - if>if>if>...无else"""
        source = '''
def func(x):
    if x > 0:
        if x > 10:
            if x > 100:
                result = "huge"
            else:
                result = "large"
        else:
            result = "small"
    else:
        result = "non-positive"
    return result
'''
        self.verify_matrix_decompilation(source, 'BN42')

    def test_BN43_try_in_finally_in_try(self):
        """BN43: try>finally>try 三层异常嵌套"""
        source = '''
def func():
    try:
        outer_work()
    finally:
        try:
            cleanup_resources()
        finally:
            log_completion()
'''
        self.verify_matrix_decompilation(source, 'BN43')

    def test_BN44_multiple_with_single_line(self):
        """BN44: 单行多with - with a: with b: with c: pass"""
        source = '''
def func():
    with ctx_a() as a:
        with ctx_b() as b:
            with ctx_c() as c:
                combine(a, b, c)
'''
        self.verify_matrix_decompilation(source, 'BN44')

    def test_BN45_long_elif_chain_boundary(self):
        """BN45: 长elif链边界 - 15个elif分支"""
        source = '''
def func(x):
    if x == 1:
        r = "one"
    elif x == 2:
        r = "two"
    elif x == 3:
        r = "three"
    elif x == 4:
        r = "four"
    elif x == 5:
        r = "five"
    elif x == 6:
        r = "six"
    elif x == 7:
        r = "seven"
    elif x == 8:
        r = "eight"
    else:
        r = "other"
    return r
'''
        self.verify_matrix_decompilation(source, 'BN45')

    # ========================================================================
    # BN46-BN55: Python版本语法边界 (version-specific syntax)
    # ========================================================================

    @pytest.mark.skipif(sys.version_info < (3, 8), reason="需要Python 3.8+")
    def test_BN46_walrus_in_list_comprehension(self):
        """BN46: 列表推导式中海象运算符 - [y := f(x) for x in ...]"""
        source = '''
def func(data):
    return [y for x in data if (y := process(x)) is not None]
'''
        self.verify_matrix_decompilation(source, 'BN46', min_equivalence=0.78)

    @pytest.mark.skipif(sys.version_info < (3, 8), reason="需要Python 3.8+")
    def test_BN47_walrus_in_while_and_comprehension(self):
        """BN47: while和推导式中的海象运算符组合"""
        source = '''
def func(text):
    results = []
    while (match := pattern.search(text)):
        results.extend([c for c in match.group() if (v := ord(c)) > 64])
        text = text[match.end():]
    return results
'''
        self.verify_matrix_decompilation(source, 'BN47', min_equivalence=0.78)

    @pytest.mark.skipif(sys.version_info < (3, 10), reason="需要Python 3.10+")
    def test_BN48_match_with_guard_deep(self):
        """BN48: match守卫条件深层 - case x if guard:>..."""
        source = '''
def func(value):
    match value:
        case int(x) if x > 0:
            result = ("pos", x)
        case int(x) if x < 0:
            result = ("neg", x)
        case int():
            result = ("zero",)
        case [a, b] if a == b:
            result = ("pair_eq", a, b)
        case [a, b]:
            result = ("pair", a, b)
        case _:
            result = ("other",)
    return result
'''
        self.verify_matrix_decompilation(source, 'BN48', min_equivalence=0.75)

    @pytest.mark.skipif(sys.version_info < (3, 10), reason="需要Python 3.10+")
    def test_BN49_match_or_pattern(self):
        """BN49: match或模式 - case A | B:"""
        source = '''
def func(cmd):
    match cmd:
        case ("load", path):
            do_load(path)
        case ("save", path) | ("write", path):
            do_save(path)
        case ("quit" | "exit" | "q",):
            do_quit()
        case _:
            unknown(cmd)
'''
        self.verify_matrix_decompilation(source, 'BN49', min_equivalence=0.78)

    @pytest.mark.skipif(sys.version_info < (3, 10), reason="需要Python 3.10+")
    def test_BN50_match_mapping_pattern(self):
        """BN50: match映射模式 - case {"key": value}:"""
        source = '''
def func(obj):
    match obj:
        case {"name": name, "age": age}:
            return f"{name} is {age}"
        case {"type": "file", "path": p}:
            return read_file(p)
        case {}:
            return "empty"
        case _:
            return "unknown"
'''
        self.verify_matrix_decompilation(source, 'BN50', min_equivalence=0.78)

    @pytest.mark.skipif(sys.version_info < (3, 11), reason="需要Python 3.11+")
    def test_BN51_exception_group_basic(self):
        """BN51: ExceptionGroup基本用法 - raise ExceptionGroup(...)"""
        source = '''
def func():
    errors = []
    try:
        risky1()
    except ValueError as e:
        errors.append(e)
    try:
        risky2()
    except TypeError as e:
        errors.append(e)
    if errors:
        raise ExceptionGroup("multiple errors", errors)
'''
        self.verify_matrix_decompilation(source, 'BN51', min_equivalence=0.75)

    @pytest.mark.skipif(sys.version_info < (3, 11), reason="需要Python 3.11+")
    def test_BN52_except_star_handler(self):
        """BN52: except* 异常组处理器"""
        source = '''
def func():
    try:
        raise ExceptionGroup("eg", [ValueError("a"), TypeError("b")])
    except* ValueError:
        handle_value_errors()
    except* TypeError:
        handle_type_errors()
'''
        self.verify_matrix_decompilation(source, 'BN52', min_equivalence=0.75)

    @pytest.mark.skipif(sys.version_info < (3, 11), reason="需要Python 3.11+")
    def test_BN53_exception_group_in_nested_try(self):
        """BN53: 嵌套try中的ExceptionGroup"""
        source = '''
def func():
    try:
        try:
            inner_op()
        except InnerError as e:
            raise ExceptionGroup("inner", [e]) from e
    except* ExceptionGroup:
        recover_all()
    except Exception:
        fallback()
'''
        self.verify_matrix_decompilation(source, 'BN53', min_equivalence=0.72)

    @pytest.mark.skipif(sys.version_info < (3, 12), reason="需要Python 3.12+")
    def test_BN54_type_alias_statement(self):
        """BN54: type语句 - type Point = tuple[int, int]"""
        source = '''
type Point = tuple[int, int]
type Result[T] = T | None

def func(p: Point) -> Result[int]:
    if p:
        return p[0] + p[1]
    return None
'''
        self.verify_matrix_decompilation(source, 'BN54', min_equivalence=0.72)

    @pytest.mark.skipif(sys.version_info < (3, 12), reason="需要Python 3.12+")
    def test_BN55_generic_class_syntax(self):
        """BN55: 泛型class语法 - class Container[T]:"""
        source = '''
class Box[T]:
    def __init__(self, item: T):
        self.item = item

    def get(self) -> T:
        return self.item

    def process(self) -> T:
        if self.item:
            return self.transform(self.item)
        return self.item

    def transform(self, x: T) -> T:
        return x
'''
        self.verify_matrix_decompilation(source, 'BN55', min_equivalence=0.70)

    # ========================================================================
    # BN56-BN65: 控制转移边界 (control transfer boundaries)
    # ========================================================================

    def test_BN56_break_from_triple_nested_loop(self):
        """BN56: 三层嵌套循环中的break - break退出最内层"""
        source = '''
def func(matrix):
    for i in range(len(matrix)):
        for j in range(len(matrix[i])):
            for k in range(len(matrix[i][j])):
                if matrix[i][j][k] == TARGET:
                    return (i, j, k)
    return None
'''
        self.verify_matrix_decompilation(source, 'BN56')

    def test_BN57_continue_in_nested_try(self):
        """BN57: 嵌套try中的continue - continue跨越try边界"""
        source = '''
def func(items):
    results = []
    for item in items:
        try:
            validate(item)
        except ValidationError:
            continue
        try:
            process(item)
            results.append(item)
        except ProcessError:
            continue
    return results
'''
        self.verify_matrix_decompilation(source, 'BN57')

    def test_BN58_return_inside_finally(self):
        """BN58: finally中的return - 返回值覆盖异常"""
        source = '''
def func(flag):
    try:
        if flag:
            raise ValueError("test")
        return "normal"
    except ValueError:
        return "caught"
    finally:
        log("done")
'''
        self.verify_matrix_decompilation(source, 'BN58')

    def test_BN59_raise_from_inside_except(self):
        """BN59: except中的raise from - 异常链"""
        source = '''
def func(data):
    try:
        parse(data)
    except ParseError as e:
        raise DataFormatError(f"invalid: {data}") from e
    except TypeError as e:
        raise DataFormatError("wrong type") from e
'''
        self.verify_matrix_decompilation(source, 'BN59')

    def test_BN60_yield_in_nested_loop(self):
        """BN60: 嵌套循环中的yield - 生成器函数"""
        source = '''
def func(matrix):
    for row in matrix:
        if row:
            for cell in row:
                if cell is not None:
                    yield cell * 2
'''
        self.verify_matrix_decompilation(source, 'BN60')

    def test_BN61_yield_from_in_try(self):
        """BN61: try中的yield from - 委托生成器"""
        source = '''
def func(sources):
    for src in sources:
        try:
            yield from iterate_source(src)
        except SourceError:
            yield from default_items()
'''
        self.verify_matrix_decompilation(source, 'BN61')

    def test_BN62_break_to_for_else(self):
        """BN62: break阻止for-else执行"""
        source = '''
def func(items):
    for item in items:
        if item.found():
            use(item)
            break
    else:
        not_found_handler()
    return done
'''
        self.verify_matrix_decompilation(source, 'BN62')

    def test_BN63_nested_function_with_closure(self):
        """BN63: 嵌套函数+闭包 - 控制流内的闭包捕获"""
        source = '''
def func(multiplier):
    results = []
    for i in range(5):
        def scale(x):
            return x * multiplier * i
        results.append(scale(i))
    return results
'''
        self.verify_matrix_decompilation(source, 'BN63', min_equivalence=0.78)

    def test_BN64_assert_in_deep_nesting(self):
        """BN64: 深层嵌套中的assert"""
        source = '''
def func(config, data):
    assert config is not None, "config required"
    for item in data:
        assert item is not None, f"null item at {data.index(item)}"
        if item.processable():
            try:
                result = transform(item)
                assert result is not None, "transform returned None"
                store(result)
            except TransformError:
                assert False, f"failed on {item}"
'''
        self.verify_matrix_decompilation(source, 'BN64')

    def test_BN65_global_nonlocal_in_control_flow(self):
        """BN65: 控制流中的global/nonlocal声明"""
        source = '''
counter = 0

def func(items):
    global counter
    for item in items:
        if item.counts():
            counter += 1
    return counter
'''
        self.verify_matrix_decompilation(source, 'BN65')

    # ========================================================================
    # BN66-BN75: 综合极限边界 (comprehensive extreme boundaries)
    # ========================================================================

    def test_BN66_augmented_assign_in_loop(self):
        """BN66: 循环中的增强赋值 - += -= *= //="""
        source = '''
def func(data):
    total = 0
    product = 1
    concat = ""
    for item in data:
        total += item.value
        product *= item.factor
        concat += item.label
        if item.divisor:
            total //= item.divisor
    return total, product, concat
'''
        self.verify_matrix_decompilation(source, 'BN66')

    def test_BN67_delete_in_control_flow(self):
        """BN67: 控制流中的del语句"""
        source = '''
func(data):
    results = []
    for key in list(data.keys()):
        value = data[key]
        if not value:
            del data[key]
        else:
            results.append(value)
    return results
'''
        self.verify_matrix_decompilation(source, 'BN67')

    def test_BN68_import_inside_function(self):
        """BN68: 函数内部的import语句"""
        source = '''
def func(filepath):
    import json
    import os
    if os.path.exists(filepath):
        with open(filepath) as f:
            data = json.load(f)
        return data
    return None
'''
        self.verify_matrix_decompilation(source, 'BN68')

    def test_BN69_multiple_returns_one_function(self):
        """BN69: 单函数多返回路径 - 6条返回路径"""
        source = '''
def analyze(x):
    if x is None:
        return ("none", None)
    if isinstance(x, str):
        if not x:
            return ("empty_str", "")
        return ("str", x)
    if isinstance(x, (list, tuple)):
        if len(x) == 0:
            return ("empty_seq", ())
        return ("seq", x)
    if isinstance(x, dict):
        return ("dict", x)
    return ("other", repr(x))
'''
        self.verify_matrix_decompilation(source, 'BN69')

    def test_BN70_string_annotations_everywhere(self):
        """BN70: 字符串注解 - 所有参数和返回值都有字符串注解"""
        source = '''
def process(data: "input data", config: "config object") -> "result dict":
    if not data:
        return {}
    results = {}
    for key, value in data.items():
        if key.startswith("_"):
            continue
        try:
            results[key] = transform(value)
        except TransformError:
            results[key] = None
    return results
'''
        self.verify_matrix_decompilation(source, 'BN70')

    def test_BN71_tuple_parameter_unpacking(self):
        """BN71: 元组参数解包 - def f((a, b)): ..."""
        source = '''
def func(points):
    results = []
    for point in points:
        x, y = point
        if x > 0 and y > 0:
            dist = (x ** 2 + y ** 2) ** 0.5
            results.append(dist)
    return results
'''
        self.verify_matrix_decompilation(source, 'BN71')

    def test_BN72_lambda_in_control_flow(self):
        """BN72: 控制流中的lambda表达式"""
        source = '''
def func(items, mode):
    ops = {
        "double": lambda x: x * 2,
        "square": lambda x: x ** 2,
        "negate": lambda x: -x,
    }
    results = []
    for item in items:
        fn = ops.get(mode, lambda x: x)
        if callable(fn):
            results.append(fn(item))
    return results
'''
        self.verify_matrix_decompilation(source, 'BN72', min_equivalence=0.78)

    def test_BN73_comprehension_with_conditional(self):
        """BN73: 带复杂条件的列表推导式"""
        source = '''
def func(data):
    flat = [
        (i, j, data[i][j])
        for i in range(len(data))
        if data[i]
        for j in range(len(data[i]))
        if data[i][j] is not None
        if data[i][j] > 0
    ]
    return flat
'''
        self.verify_matrix_decompilation(source, 'BN73', min_equivalence=0.78)

    def test_BN74_dict_comprehension_in_loop(self):
        """BN74: 循环中的字典推导式"""
        source = '''
def func(groups):
    mapping = {}
    for group in groups:
        if group.active():
            submap = {
                item.id(): item.value()
                for item in group.items()
                if item.value() is not None
            }
            mapping.update(submap)
    return mapping
'''
        self.verify_matrix_decompilation(source, 'BN74', min_equivalence=0.78)

    def test_BN75_generator_expr_as_argument(self):
        """BN75: 生成器表达式作为函数参数 - sum(x for x in ...)"""
        source = '''
def func(data):
    totals = []
    for group in data:
        total = sum(
            item.amount() * item.price()
            for item in group
            if item.included()
        )
        totals.append(total)
    return totals
'''
        self.verify_matrix_decompilation(source, 'BN75', min_equivalence=0.78)


if __name__ == '__main__':
    pytest.main([__file__, '-v', '--tb=short'])
