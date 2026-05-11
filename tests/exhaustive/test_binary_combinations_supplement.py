#!/usr/bin/env python3
"""
二元组合补充测试 - Phase 4遗漏的10个核心组合 + 扩展20个

覆盖所有控制流结构的两两嵌套排列组合。
确保反编译器能正确处理任意两种控制流结构的嵌套。

理论依据（编译器结构化分析理论）：
- 二元组合是构建任意复杂嵌套的基础单元
- 每种外层/内层配对都产生唯一的CFG拓扑
- 区域归约算法必须能正确识别每种拓扑对应的区域类型

测试矩阵：
| ID | 外层 | 内层 | 说明 |
|----|------|------|------|
| N01-N10 | 核心遗漏组合 | | Phase 4明确要求的10个 |
| N11-N20 | except/finally变体 | | 异常处理与其他结构 |
| N21-N30 | match/with/comprehension | | 新语法特性组合 |
"""

import sys
import os
import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from tests.helpers.decompilation_helper import MatrixTestBase


class TestBinaryCombinationsSupplement(MatrixTestBase):
    """二元组合完备性测试 - 覆盖Phase 4遗漏及扩展的30个二元嵌套"""

    # ========================================================================
    # N01-N10: Phase 4核心遗漏组合
    # ========================================================================

    def test_N01_except_while(self):
        """N01: except>while - try-except中嵌套while循环

        组合类型：异常处理 + 条件循环
        CFG特征：except处理器内部存在回边形成循环区域
        测试要点：异常恢复后的循环行为、循环中的异常传播"""
        source = '''
def func():
    try:
        x = risky_operation()
    except ValueError:
        while condition:
            do_something()
            condition = check_state()
'''
        self.verify_matrix_decompilation(source, 'N01')

    def test_N02_except_for(self):
        """N02: except>for - try-except中嵌套for循环

        组合类型：异常处理 + 迭代循环
        CFG特征：except体内包含FOR_ITER回边
        测试要点：迭代器在异常处理中的作用域、break/continue语义"""
        source = '''
def func():
    try:
        x = risky_operation()
    except ValueError:
        for i in range(10):
            process_item(i)
'''
        self.verify_matrix_decompilation(source, 'N02')

    def test_N03_finally_if(self):
        """N03: finally>if - try-finally中嵌套if语句

        组合类型：异常终结 + 条件分支
        CFG特征：finally块内的条件跳转不影响清理语义
        测试要点：finally中的条件逻辑、保证执行的语义保持"""
        source = '''
def func():
    try:
        x = operation()
    finally:
        if cleanup_needed:
            perform_cleanup()
'''
        self.verify_matrix_decompilation(source, 'N03')

    def test_N04_finally_for(self):
        """N04: finally>for - try-finally中嵌套for循环

        组合类型：异常终结 + 迭代循环
        CFG特征：finally块内存在FOR_ITER回边，需与正常循环区分
        测试要点：finally中的循环清理、资源释放的完整性"""
        source = '''
def func():
    try:
        x = operation()
    finally:
        for item in resources:
            release_resource(item)
'''
        self.verify_matrix_decompilation(source, 'N04')

    def test_N05_elif_while(self):
        """N05: elif>while - if-elif链中嵌套while循环

        组合类型：多路分支 + 条件循环
        CFG特征：elif分支体内的回边不应影响外层条件判断
        测试要点：elif条件判断与内层循环的独立性、循环变量作用域"""
        source = '''
def func(a, b):
    if a > 0:
        result = a
    elif b > 0:
        while b > 0:
            result += b
            b -= 1
    else:
        result = 0
'''
        self.verify_matrix_decompilation(source, 'N05')

    def test_N06_else_while(self):
        """N06: else>while - if-else的else分支中嵌套while循环

        组合类型：双路分支 + 条件循环
        CFG特征：else基本块内存在回边
        测试要点：else分支的进入条件、循环终止后控制流走向"""
        source = '''
def func(x):
    if x < 0:
        handle_negative()
    else:
        while x > 0:
            process(x)
            x -= 1
'''
        self.verify_matrix_decompilation(source, 'N06')

    @pytest.mark.skipif(sys.version_info < (3, 10), reason="需要Python 3.10+支持match")
    def test_N07_for_match(self):
        """N07: for>match - for循环中嵌套match语句

        组合类型：迭代循环 + 结构化模式匹配
        CFG特征：循环体内存在多路模式匹配分支
        测试要点：每次迭代的模式匹配、match中的break对循环的影响"""
        source = '''
def func(items):
    results = []
    for i in items:
        match i:
            case int() as n:
                results.append(n * 2)
            case str() as s:
                results.append(s.upper())
            case _:
                pass
    return results
'''
        self.verify_matrix_decompilation(source, 'N07', min_equivalence=0.78)

    @pytest.mark.skipif(sys.version_info < (3, 10), reason="需要Python 3.10+支持match")
    def test_N08_while_match(self):
        """N08: while>match - while循环中嵌套match语句

        组合类型：条件循环 + 结构化模式匹配
        CFG特征：循环条件与模式匹配分支的组合控制流
        测试要点：match中的break退出循环、守卫条件的处理"""
        source = '''
def func(data):
    results = []
    while data:
        item = data.pop()
        match item:
            case None:
                break
            case {"value": v}:
                results.append(v)
            case [x, y]:
                results.extend([x, y])
            case _:
                results.append(item)
    return results
'''
        self.verify_matrix_decompilation(source, 'N08', min_equivalence=0.78)

    @pytest.mark.skipif(sys.version_info < (3, 10), reason="需要Python 3.10+支持match")
    def test_N09_try_match(self):
        """N09: try>match - try体中嵌套match语句

        组合类型：异常处理 + 结构化模式匹配
        CFG特征：try块内存在多路分支，异常可从任一case抛出
        测试要点：match各分支中的异常传播、异常处理的精确范围"""
        source = '''
def func(value):
    try:
        match value:
            case int() as n:
                result = 100 // n
            case str() as s:
                result = s[100]
            case _:
                result = str(value)
    except (ZeroDivisionError, IndexError):
        result = "error"
    return result
'''
        self.verify_matrix_decompilation(source, 'N09', min_equivalence=0.78)

    @pytest.mark.skipif(sys.version_info < (3, 10), reason="需要Python 3.10+支持match")
    def test_N10_match_try(self):
        """N10: match>try - match的case分支中嵌套try-except

        组合类型：结构化模式匹配 + 异常处理
        CFG特征：case分支体内存在异常处理子图
        测试要点：每个case独立的异常处理、异常不跨case传播"""
        source = '''
def func(value):
    match value:
        case int() as n:
            try:
                result = dangerous_op(n)
            except ValueError:
                result = n * 2
        case str() as s:
            try:
                result = parse(s)
            except SyntaxError:
                result = s
        case _:
            result = value
    return result
'''
        self.verify_matrix_decompilation(source, 'N10', min_equivalence=0.78)

    # ========================================================================
    # N11-N20: except/finally 变体组合
    # ========================================================================

    def test_N11_except_if(self):
        """N11: except>if - except中嵌套if语句"""
        source = '''
def func():
    try:
        risky()
    except ValueError as e:
        if e.args:
            handle_args(e.args)
        else:
            handle_generic()
'''
        self.verify_matrix_decompilation(source, 'N11')

    def test_N12_except_for_if(self):
        """N12: except>for>if - 三层：except>for>if"""
        source = '''
def func():
    try:
        risky()
    except ValueError:
        for i in range(5):
            if i % 2 == 0:
                process_even(i)
            else:
                process_odd(i)
'''
        self.verify_matrix_decompilation(source, 'N12')

    def test_N13_finally_while_if(self):
        """N13: finally>while>if - 三层：finally>while>if"""
        source = '''
def func():
    try:
        work()
    finally:
        while has_pending():
            task = get_task()
            if task.priority == HIGH:
                execute_now(task)
            else:
                schedule_later(task)
'''
        self.verify_matrix_decompilation(source, 'N13')

    def test_N14_try_except_else_for(self):
        """N14: try-except-else>for - try的else分支中嵌套for

        组合类型：完整异常处理 + 迭代循环
        CFG特征：无异常时进入else分支执行循环"""
        source = '''
def func(data):
    try:
        items = load_items(data)
    except LoadError:
        items = []
    else:
        for item in items:
            validate(item)
    return items
'''
        self.verify_matrix_decompilation(source, 'N14')

    def test_N15_try_except_finally_if(self):
        """N15: try-except-finally>if - 完整异常处理中嵌套if"""
        source = '''
def func():
    try:
        result = compute()
    except ComputeError:
        result = fallback()
    finally:
        if result is not None:
            save_result(result)
'''
        self.verify_matrix_decompilation(source, 'N15')

    def test_N16_except_with(self):
        """N16: except>with - except中嵌套with语句"""
        source = '''
def func():
    try:
        risky_io()
    except IOError:
        with open('log.txt', 'a') as f:
            f.write('error occurred\n')
'''
        self.verify_matrix_decompilation(source, 'N16')

    def test_N17_finally_with(self):
        """N17: finally>with - finally中嵌套with语句"""
        source = '''
def func():
    try:
        process_data()
    finally:
        with lock:
            release_resources()
'''
        self.verify_matrix_decompilation(source, 'N17')

    def test_N18_multi_except_for(self):
        """N18: 多重except>for - 多个except分支各自含for循环"""
        source = '''
def func():
    try:
        complex_operation()
    except ValueError:
        for i in range(3):
            fix_value(i)
    except TypeError:
        for k in range(5):
            convert_type(k)
    except KeyError:
        for key in default_keys():
            set_default(key)
'''
        self.verify_matrix_decompilation(source, 'N18')

    def test_N19_except_return(self):
        """N19: except>return - except中嵌套return语句"""
        source = '''
def func():
    try:
        result = may_fail()
    except ValueError:
        return None
    except TypeError:
        return "type_error"
    return result
'''
        self.verify_matrix_decompilation(source, 'N19')

    def test_N20_finally_return(self):
        """N20: finally>return - finally中嵌套return（抑制异常返回值）"""
        source = '''
def func():
    try:
        raise ValueError("test")
    finally:
        return "cleaned"
'''
        self.verify_matrix_decompilation(source, 'N20')

    # ========================================================================
    # N21-N30: match/with/comprehension 组合
    # ========================================================================

    def test_N21_with_if_for(self):
        """N21: with>if>for - with中嵌套if和for"""
        source = '''
def func(resource):
    with open_resource(resource) as r:
        if r.is_valid():
            for item in r.items():
                process(item)
'''
        self.verify_matrix_decompilation(source, 'N21')

    def test_N22_nested_with_if(self):
        """N22: with>with>if - 双层with嵌套if"""
        source = '''
def func():
    with context_a() as a:
        with context_b() as b:
            if a.compatible(b):
                merge(a, b)
'''
        self.verify_matrix_decompilation(source, 'N22')

    def test_N23_for_with_try(self):
        """N23: for>with>try - 循环中嵌套with和try"""
        source = '''
def func(files):
    results = []
    for fname in files:
        with open(fname) as f:
            try:
                data = json.load(f)
                results.append(data)
            except json.JSONDecodeError:
                results.append(None)
    return results
'''
        self.verify_matrix_decompilation(source, 'N23')

    def test_N24_while_with_if_else(self):
        """N24: while>with>if>else - 四层混合嵌套"""
        source = '''
def func():
    while has_work():
        with acquire_lock():
            if current_task():
                execute(current_task())
            else:
                wait_for_task()
'''
        self.verify_matrix_decompilation(source, 'N24')

    def test_N25_if_with_for_while(self):
        """N25: if>with>for>while - 四层混合嵌套"""
        source = '''
def func(flag, data):
    if flag:
        with manager() as m:
            for item in data:
                while m.processing():
                    m.handle(item)
'''
        self.verify_matrix_decompilation(source, 'N25')

    def test_N26_try_for_with_if(self):
        """N26: try>for>with>if - 四层混合嵌套"""
        source = '''
def func(resources):
    try:
        for res in resources:
            with open(res) as f:
                if f.readable():
                    content = f.read()
                    store(content)
    except IOError as e:
        log_error(e)
'''
        self.verify_matrix_decompilation(source, 'N26')

    def test_N27_for_if_try_except(self):
        """N27: for>if>try>except - 循环中条件判断再异常处理"""
        source = '''
def func(items):
    for item in items:
        if should_process(item):
            try:
                result = transform(item)
                collect(result)
            except TransformError:
                collect_default(item)
'''
        self.verify_matrix_decompilation(source, 'N27')

    def test_N28_while_if_for_try(self):
        """N28: while>if>for>try - 条件循环中条件判断再循环再异常保护"""
        source = '''
def func(pool):
    while pool.active():
        if pool.has_tasks():
            for task in pool.tasks():
                try:
                    task.execute()
                except TaskError:
                    task.retry()
'''
        self.verify_matrix_decompilation(source, 'N28')

    def test_N29_if_try_for_while(self):
        """N29: if>try>for>while - 条件分支中异常保护再双层循环"""
        source = '''
def func(mode, data):
    if mode == "batch":
        try:
            validated = validate_all(data)
        except ValidationError:
            validated = []
        for batch in chunks(validated):
            while not batch.done():
                batch.process_next()
'''
        self.verify_matrix_decompilation(source, 'N29')

    def test_N30_for_try_if_while_else(self):
        """N30: for>try>if>while>else - 五层混合嵌套（边界）"""
        source = '''
def func(records):
    results = []
    for rec in records:
        try:
            parsed = parse_record(rec)
        except ParseError:
            continue
        if parsed.is_complete():
            while parsed.has_more():
                results.append(parsed.next())
        else:
            results.append(parsed.partial())
    return results
'''
        self.verify_matrix_decompilation(source, 'N30')


if __name__ == '__main__':
    pytest.main([__file__, '-v', '--tb=short'])
