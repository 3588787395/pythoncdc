#!/usr/bin/env python3
"""
完备性测试矩阵 v6.0 (Comprehensive Test Matrix v6.0)
===============================================

设计原则：
  覆盖Python全部控制流语法及其有意义的嵌套排列组合。
  每个测试用例验证反编译器能否正确还原源码结构。

语法全集（12类 × N种变体）：

  A. 顺序结构 (Sequential)
     A1: 单赋值    A2: 链式赋值   A3: 多语句序列
     A4: 表达式语句  A5: pass       A6: return/break/continue
     A7: raise      A8: assert     A9: del/global

  B. 条件分支 (Conditional)
     B1: if/else        B2: if/elif/else链   B3: 三元表达式(if-exp)
     B4: 嵌套if(3层+)   B5: if内含return    B6: 空if体

  C. 循环 (Loops)
     C1: for/else       C2: while/else       C3: for+break
     C4: for+continue   C5: while True       C6: 空循环体
     C7: 异步for/while   C8: 嵌套循环(同类型)  C9: range/iter变体

  D. 异常处理 (Exception Handling)
     D1: try/except      D2: try/except/else  D3: try/finally
     D4: try/except/finally/else  D5: 多重except
     D6: with/as         D7: 多上下文with     D8: 异步with
     D9: 嵌套try        D10: with内嵌套异常

  E. 模式匹配 (Match)
     E1: match/literal   E2: match/or-pattern  E3: match/guard
     E4: match/class     E5: match/mapping    E6: match/sequence
     E7: match/as        E8: 嵌套match

  F. 推导式 (Comprehensions)
     F1: list comp       F2: dict comp        F3: set comp
     F4: gen expression  F5: 嵌套comp        F6: comp+条件
     F7: comp+walrus(:=)

  G. 函数定义 (Function Def)
     G1: 普通函数        G2: 默认参数          G3: *args/**kwargs
     G4: 装饰器          G5: 嵌套函数(def in def)

  H. 类定义 (Class Def)
     H1: 基本类           H2: 继承             H3: 方法中的控制流

嵌套矩阵（有意义的组合）：
  二元嵌套优先级表（外层×内层）：
    for×if, for×for, for×while, for×try, for×with, for×match,
    while×if, while×for, while×try, while×with,
    if×for, if×while, if×if, if×try, if×with, if×match,
    try×for, try×if, try×try, try×with,
    with×for, with×if, with×try, with×with,
    match×if, match×for, match×match

使用方式：
  python _test_completeness_v6.py              # 运行完整矩阵
  python _test_completeness_v6.py --category for # 仅运行for类别
  python _test_completeness_v6.py --level 0,1   # 仅运行L0+L1
  python _test_completeness_v6.py --ci          # CI模式（输出JSON）
"""

import sys
import ast
import time
import types
import dis
from dataclasses import dataclass, field
from typing import List, Optional, Tuple, Dict, Set
from enum import Enum, auto


class TestCategory(Enum):
    SEQUENTIAL = "sequential"
    CONDITIONAL = "conditional"
    LOOP = "loop"
    EXCEPTION = "exception"
    MATCH = "match"
    COMPREHENSION = "comprehension"
    FUNCTION = "function"
    CLASS = "class"
    NESTED = "nested"
    REAL_WORLD = "real-world"
    BOUNDARY = "boundary"


@dataclass
class TestMatrixCase:
    """完备性矩阵测试用例"""
    id: str
    name: str
    category: TestCategory
    level: int
    source_code: str
    required_patterns: List[str] = field(default_factory=list)
    expected_patterns: List[str] = field(default_factory=list)
    forbidden_patterns: List[str] = field(default_factory=list)
    description: str = ""
    syntax_elements: Set[str] = field(default_factory=set)


@dataclass
class TestResult:
    id: str
    passed: bool
    score: float
    structure_correct: bool
    syntax_valid: bool
    decompiled: str
    missing_required: List[str] = field(default_factory=list)
    unexpected_forbidden: List[str] = field(default_factory=list)
    error: Optional[str] = None
    duration_ms: float = 0.0


class ComprehensiveTestMatrix:
    
    def __init__(self):
        self.test_cases: List[TestMatrixCase] = []
        self.results: List[TestResult] = []
        self._build_matrix()
    
    def _build_matrix(self):
        self._add_sequential()
        self._add_conditional()
        self._add_loops()
        self._add_exception()
        self._add_match()
        self._add_comprehensions()
        self._add_nested_binary()
        self._add_nested_ternary()
        self._add_real_world()
        self._add_boundary()
    
    def _add(self, tc: TestMatrixCase):
        self.test_cases.append(tc)
    
    def _add_sequential(self):
        base = {"category": TestCategory.SEQUENTIAL, "level": 0}
        
        self._add(TestMatrixCase(
            id="A1", name="single_assign", source_code='''def foo():\n    x = 42\n''',
            required_patterns=["x = 42"], expected_patterns=["x = 42"],
            syntax_elements={"assign"}, **base))
        
        self._add(TestMatrixCase(
            id="A2", name="chain_assign", source_code='''def foo():\n    a = b = c = 0\n''',
            required_patterns=["a =", "b =", "c ="], expected_patterns=["a = b = c = 0"],
            syntax_elements={"chain_assign"}, **base))
        
        self._add(TestMatrixCase(
            id="A3", name="multi_stmt", source_code='''def foo():\n    x = 1\n    y = 2\n    z = 3\n''',
            required_patterns=["x =", "y =", "z ="], expected_patterns=["x = 1", "y = 2"],
            syntax_elements={"multi_stmt"}, **base))
        
        self._add(TestMatrixCase(
            id="A4a", name="expr_stmt_call", source_code='''def foo():\n    print("hello")\n''',
            required_patterns=["print("], expected_patterns=['print("hello")'],
            syntax_elements={"expr_stmt", "call"}, **base))
        
        self._add(TestMatrixCase(
            id="A4b", name="expr_stmt_method_chain",
            source_code='''def foo():\n    obj.method().attr\n''',
            required_patterns=["obj.", ".method(", ".attr"], description="方法链表达式",
            syntax_elements={"method_chain"}, **base))
        
        self._add(TestMatrixCase(
            id="A5", name="pass_stmt", source_code='''def foo():\n    pass\n''',
            required_patterns=["pass"], expected_patterns=["pass"],
            syntax_elements={"pass"}, **base))
        
        self._add(TestMatrixCase(
            id="A6a", name="return_simple", source_code='''def foo():\n    return 42\n''',
            required_patterns=["return 42"], expected_patterns=["return 42"],
            syntax_elements={"return"}, **base))
        
        self._add(TestMatrixCase(
            id="A6b", name="return_none", source_code='''def foo():\n    return\n''',
            required_patterns=["return"], expected_patterns=["return"],
            syntax_elements={"return_none"}, **base))
        
        self._add(TestMatrixCase(
            id="A6c", name="return_expr", source_code='''def foo():\n    return [1, 2, 3]\n''',
            required_patterns=["return ["], expected_patterns=["return [1, 2, 3]"],
            syntax_elements={"return_expr"}, **base))
        
        self._add(TestMatrixCase(
            id="A7", name="raise_exception", source_code='''def foo():\n    raise ValueError("err")\n''',
            required_patterns=["raise ValueError"], expected_patterns=["raise ValueError"],
            syntax_elements={"raise"}, **base))
        
        self._add(TestMatrixCase(
            id="A8", name="assert_stmt", source_code='''def foo(x):\n    assert x > 0\n''',
            required_patterns=["assert x > 0"], expected_patterns=["assert x > 0"],
            syntax_elements={"assert"}, **base))
        
        self._add(TestMatrixCase(
            id="A9", name="augmented_assign", source_code='''def foo():\n    x = 0\n    x += 1\n    x -= 1\n    x *= 2\n''',
            required_patterns=["x +=", "x -=", "x *="], expected_patterns=["x += 1"],
            syntax_elements={"augmented_assign"}, **base))
        
        self._add(TestMatrixCase(
            id="A10", name="walrus_assign", source_code='''def foo():\n    if (n := len([1,2,3])) > 2:\n        return n\n''',
            required_patterns=[":="], expected_patterns=["n :="],
            syntax_elements={"walrus"}, **base))
    
    def _add_conditional(self):
        base = {"category": TestCategory.CONDITIONAL, "level": 0}
        
        self._add(TestMatrixCase(
            id="B1a", name="if_else", source_code='''def foo(x):\n    if x > 0:\n        return "pos"\n    else:\n        return "neg"\n''',
            required_patterns=["if x > 0:", "else:"],
            expected_patterns=["if x > 0:", 'return "pos"', "else:", 'return "neg"'],
            syntax_elements={"if_else"}, **base))
        
        self._add(TestMatrixCase(
            id="B1b", name="if_no_else", source_code='''def foo(x):\n    if x > 0:\n        print("pos")\n''',
            required_patterns=["if x > 0:"], expected_patterns=["if x > 0:", "print("],
            syntax_elements={"if_only"}, **base))
        
        self._add(TestMatrixCase(
            id="B2", name="if_elif_else", source_code='''def foo(x):\n    if x >= 90:\n        return "A"\n    elif x >= 70:\n        return "B"\n    elif x >= 50:\n        return "C"\n    else:\n        return "F"\n''',
            required_patterns=["if x >= 90:", "elif", "else:"],
            expected_patterns=["elif x >= 70:", "elif x >= 50:"],
            syntax_elements={"if_elif_else"}, **base))
        
        self._add(TestMatrixCase(
            id="B3", name="ternary_expr", source_code='''def foo(a, b):\n    return a if a > b else b\n''',
            required_patterns=["return a if a > b else b"],
            expected_patterns=["return a if a > b else b"],
            syntax_elements={"ternary"}, **base))
        
        self._add(TestMatrixCase(
            id="B4", name="nested_if_deep", source_code='''def foo(a, b, c):\n    if a:\n        if b:\n            if c:\n                return "all"\n    return "none"\n''',
            required_patterns=["if a:", "if b:", "if c:"],
            expected_patterns=["if a:", "if b:", "if c:", 'return "all"'],
            syntax_elements={"nested_if_3deep"}, **base))
        
        self._add(TestMatrixCase(
            id="B5", name="if_return_both", source_code='''def foo(x):\n    if x > 100:\n        return "big"\n    else:\n        return "small"\n''',
            required_patterns=["if x > 100:", "else:", "return"],
            expected_patterns=['return "big"', 'return "small"'],
            syntax_elements={"if_return_branches"}, **base))
        
        self._add(TestMatrixCase(
            id="B6", name="if_single_line", source_code='''def foo(x):\n    if x > 0: return True\n    return False\n''',
            required_patterns=["if x > 0: return True"],
            expected_patterns=["if x > 0: return True", "return False"],
            syntax_elements={"if_oneline"}, **base))
        
        self._add(TestMatrixCase(
            id="B7", name="boolop_and_or", source_code='''def foo(x):\n    if x > 0 and x < 100:\n        return "ok"\n    if x < 0 or x > 100:\n        return "out"\n''',
            required_patterns=["and", "or"],
            expected_patterns=["and", "or"],
            syntax_elements={"boolop"}, **base))
    
    def _add_loops(self):
        base = {"category": TestCategory.LOOP, "level": 0}
        
        self._add(TestMatrixCase(
            id="C1a", name="for_basic", source_code='''def foo(data):\n    result = []\n    for x in data:\n        result.append(x)\n    return result\n''',
            required_patterns=["for x in data:"],
            forbidden_patterns=["else:"],
            expected_patterns=["for x in data:", "result.append(x)"],
            syntax_elements={"for"}, **base))
        
        self._add(TestMatrixCase(
            id="C1b", name="for_enum", source_code='''def foo(data):\n    for i, x in enumerate(data):\n        print(i, x)\n''',
            required_patterns=["for i, x in enumerate"],
            expected_patterns=["for i, x in enumerate(data):"],
            syntax_elements={"for_enum"}, **base))
        
        self._add(TestMatrixCase(
            id="C1c", name="for_zip", source_code='''def foo(a, b):\n    for x, y in zip(a, b):\n        print(x, y)\n''',
            required_patterns=["for x, y in zip"],
            expected_patterns=["for x, y in zip(a, b):"],
            syntax_elements={"for_zip"}, **base))
        
        self._add(TestMatrixCase(
            id="C1d", name="for_dict_items", source_code='''def foo(d):\n    for k, v in d.items():\n        print(k, v)\n''',
            required_patterns=["for k, v in d.items()"],
            expected_patterns=["for k, v in d.items():"],
            syntax_elements={"for_dict_items"}, **base))
        
        self._add(TestMatrixCase(
            id="C2a", name="for_with_else", source_code='''def foo(data):\n    for x in data:\n        if x < 0:\n            break\n    else:\n        print("all positive")\n''',
            required_patterns=["for x in data:", "else:"],
            expected_patterns=["for x in data:", "break", "else:"],
            syntax_elements={"for_else_break"}, **base))
        
        self._add(TestMatrixCase(
            id="C2b", name="for_without_else", source_code='''def foo(data):\n    for x in data:\n        process(x)\n    cleanup()\n''',
            required_patterns=["for x in data:"],
            forbidden_patterns=["else:"],
            expected_patterns=["for x in data:", "process(x)"],
            syntax_elements={"for_no_else"}, **base))
        
        self._add(TestMatrixCase(
            id="C3a", name="while_basic", source_code='''def foo(n):\n    i = 0\n    while i < n:\n        i += 1\n    return i\n''',
            required_patterns=["while i < n:"],
            forbidden_patterns=["else:"],
            expected_patterns=["while i < n:", "i += 1"],
            syntax_elements={"while"}, **base))
        
        self._add(TestMatrixCase(
            id="C3b", name="while_true", source_code='''def foo():\n    while True:\n        x = work()\n        if x is None:\n            break\n''',
            required_patterns=["while True:"],
            expected_patterns=["while True:", "break"],
            syntax_elements={"while_true"}, **base))
        
        self._add(TestMatrixCase(
            id="C3c", name="while_with_else", source_code='''def foo(items, target):\n    i = 0\n    while i < len(items):\n        if items[i] == target:\n            return i\n        i += 1\n    else:\n        return -1\n''',
            required_patterns=["while i < len(items):", "else:"],
            expected_patterns=["while i < len(items):", "else:", "return -1"],
            syntax_elements={"while_else"}, **base))
        
        self._add(TestMatrixCase(
            id="C4a", name="for_continue", source_code='''def foo(data):\n    result = []\n    for x in data:\n        if skip(x):\n            continue\n        result.append(process(x))\n    return result\n''',
            required_patterns=["for x in data:", "continue"],
            expected_patterns=["for x in data:", "continue"],
            syntax_elements={"for_continue"}, **base))
        
        self._add(TestMatrixCase(
            id="C4b", name="while_continue", source_code='''def foo(nums):\n    total = 0\n    i = 0\n    while i < len(nums):\n        if nums[i] <= 0:\n            i += 1\n            continue\n        total += nums[i]\n        i += 1\n    return total\n''',
            required_patterns=["while", "continue"],
            expected_patterns=["while", "continue"],
            syntax_elements={"while_continue"}, **base))
        
        self._add(TestMatrixCase(
            id="C5a", name="for_empty_body", source_code='''def foo(data):\n    for x in data:\n        pass\n''',
            required_patterns=["for x in data:", "pass"],
            expected_patterns=["for x in data:", "pass"],
            syntax_elements={"for_empty"}, **base))
        
        self._add(TestMatrixCase(
            id="C5b", name="while_empty_body", source_code='''def foo():\n    start = time.time()\n    while time.time() - start < timeout:\n        pass\n''',
            required_patterns=["while", "pass"],
            expected_patterns=["while", "pass"],
            syntax_elements={"while_empty"}, **base))
        
        self._add(TestMatrixCase(
            id="C6a", name="async_for", source_code='''async def foo():\n    async for item in async_iter:\n        await process(item)\n''',
            required_patterns=["async for", "await"],
            expected_patterns=["async for item in async_iter:", "await process(item)"],
            syntax_elements={"async_for"}, **base))
        
        self._add(TestMatrixCase(
            id="C6b", name="async_while", source_code='''async def foo():\n    while condition:\n        await async_work()\n''',
            required_patterns=["async while" if False else "while", "await"],
            expected_patterns=["while condition:", "await async_work()"],
            syntax_elements={"async_while"}, **base))
        
        self._add(TestMatrixCase(
            id="C7", name="for_range_variants",
            source_code='''def foo(n):\n    for i in range(n):\n        pass\n    for i in range(0, n):\n        pass\n    for i in range(0, n, 2):\n        pass\n    for i in reversed(range(n)):\n        pass\n''',
            required_patterns=["range(n)", "range(0, n)", "range(0, n, 2)", "reversed(range"],
            syntax_elements={"for_range"}, **base))
        
        self._add(TestMatrixCase(
            id="C8", name="for_nested_same_type",
            source_code='''def foo(matrix):\n    result = []\n    for row in matrix:\n        for val in row:\n            result.append(val)\n    return result\n''',
            required_patterns=["for row in matrix:", "for val in row:"],
            expected_patterns=["for row in matrix:", "for val in row:"],
            syntax_elements={"for_nested_for"}, **base))
    
    def _add_exception(self):
        base = {"category": TestCategory.EXCEPTION, "level": 0}
        
        self._add(TestMatrixCase(
            id="D1a", name="try_except", source_code='''def foo(a, b):\n    try:\n        return a / b\n    except ZeroDivisionError:\n        return float(\'inf\')\n''',
            required_patterns=["try:", "except ZeroDivisionError:"],
            expected_patterns=["try:", "except ZeroDivisionError:", "float('inf')"],
            syntax_elements={"try_except"}, **base))
        
        self._add(TestMatrixCase(
            id="D1b", name="try_bare_except", source_code='''def foo():\n    try:\n        risky_op()\n    except:\n        handle_error()\n''',
            required_patterns=["try:", "except:"],
            expected_patterns=["try:", "except:"],
            syntax_elements={"try_bare_except"}, **base))
        
        self._add(TestMatrixCase(
            id="D2", name="try_multi_except",
            source_code='''def foo(obj):\n    try:\n        len(obj)\n    except TypeError:\n        pass\n    except AttributeError:\n        pass\n    except Exception as e:\n        log(e)\n''',
            required_patterns=["try:", "except TypeError:", "except AttributeError:", "except Exception as e:"],
            expected_patterns=["except AttributeError:", "except Exception as e:"],
            syntax_elements={"try_multi_except"}, **base))
        
        self._add(TestMatrixCase(
            id="D3a", name="try_finally", source_code='''def foo(path):\n    f = None\n    try:\n        f = open(path)\n        f.read()\n    finally:\n        if f:\n                f.close()\n''',
            required_patterns=["try:", "finally:"],
            expected_patterns=["try:", "finally:", "f.close()"],
            syntax_elements={"try_finally"}, **base))
        
        self._add(TestMatrixCase(
            id="D3b", name="try_except_finally",
            source_code='''def foo(a, b):\n    try:\n        return a / b\n    except ZeroDivisionError:\n        return 0\n    finally:\n        cleanup()\n''',
            required_patterns=["try:", "except", "finally:"],
            expected_patterns=["try:", "except ZeroDivisionError:", "finally:"],
            syntax_elements={"try_except_finally"}, **base))
        
        self._add(TestMatrixCase(
            id="D4", name="try_except_else",
            source_code='''def foo(divisor):\n    try:\n        result = 10 / divisor\n    except ZeroDivisionError:\n        raise ValueError("division by zero")\n    else:\n        print(f"result={result}")\n''',
            required_patterns=["try:", "except", "else:"],
            expected_patterns=["try:", "except ZeroDivisionError:", "else:"],
            syntax_elements={"try_except_else"}, **base))
        
        self._add(TestMatrixCase(
            id="D5a", name="with_basic", source_code='''def read_file(path):\n    with open(path) as f:\n        return f.read()\n''',
            required_patterns=["with open(path) as f:"],
            forbidden_patterns=["None(None, None)"],
            expected_patterns=["with open(path) as f:", "f.read()"],
            syntax_elements={"with_as"}, **base))
        
        self._add(TestMatrixCase(
            id="D5b", name="with_no_as", source_code='''def use_lock(lock):\n    with lock:\n        critical_section()\n''',
            required_patterns=["with lock:"],
            forbidden_patterns=["None(None, None)"],
            expected_patterns=["with lock:", "critical_section()"],
            syntax_elements={"with_no_as"}, **base))
        
        self._add(TestMatrixCase(
            id="D5c", name="with_multi_context",
            source_code='''def copy_data(src, dst):\n    with open(src) as fin, open(dst, \'w\') as fout:\n        fout.write(fin.read())\n''',
            required_patterns=["with open(src) as fin,", "open(dst,"],
            forbidden_patterns=["None(None, None)"],
            expected_patterns=["with open(src) as fin,", "open(dst, \'w\') as fout:"],
            syntax_elements={"with_multi"}, **base))
        
        self._add(TestMatrixCase(
            id="D5d", name="with_async", source_code='''async def op():\n    async with async_lock:\n        await work()\n''',
            required_patterns=["async with async_lock:"],
            forbidden_patterns=["None(None, None)"],
            expected_patterns=["async with async_lock:", "await work()"],
            syntax_elements={"async_with"}, **base))
        
        self._add(TestMatrixCase(
            id="D5e", name="with_nested", source_code='''def process(files):\n    with open(\'log.txt\', \'w\') as logfile:\n        for f in files:\n            with open(f) as infile:\n                logfile.write(infile.read())\n''',
            required_patterns=["with open(\'log.txt\'", "with open(f) as infile:"],
            forbidden_patterns=["None(None, None)"],
            expected_patterns=["with open(\'log.txt\'", "w\') as logfile:", "with open(f) as infile:"],
            syntax_elements={"with_nested"}, **base))
        
        self._add(TestMatrixCase(
            id="D5f", name="with_try_inside",
            source_code='''def safe_read(path):\n    with open(path) as f:\n        try:\n            return f.read()\n        except IOError:\n            return ""\n''',
            required_patterns=["with open(path) as f:", "try:", "except IOError:"],
            forbidden_patterns=["None(None, None)"],
            expected_patterns=["with open(path) as f:", "try:", "except IOError:"],
            syntax_elements={"with_try"}, **base))
        
        self._add(TestMatrixCase(
            id="D5g", name="with_empty_body", source_code='''def noop(resource):\n    with resource:\n        pass\n    return resource\n''',
            required_patterns=["with resource:", "pass"],
            forbidden_patterns=["None(None, None)"],
            expected_patterns=["with resource:", "pass"],
            syntax_elements={"with_empty"}, **base))
        
        self._add(TestMatrixCase(
            id="D6", name="try_nested", source_code='''def foo():\n    try:\n        try:\n            inner()\n        except InnerError:\n            pass\n    except OuterError:\n        pass\n''',
            required_patterns=["try:", "except InnerError:", "except OuterError:"],
            expected_patterns=["try:", "try:", "except InnerError:"],
            syntax_elements={"try_nested"}, **base))
    
    def _add_match(self):
        base = {"category": TestCategory.MATCH, "level": 0}
        
        self._add(TestMatrixCase(
            id="E1", name="match_literal",
            source_code='''def classify(x):\n    match x:\n        case 0:\n            return "zero"\n        case 1:\n            return "one"\n        case _:\n            return "other"\n''',
            required_patterns=["match x:", "case 0:", "case 1:", "case _:"],
            expected_patterns=["match x:", "case 0:", "case 1:", "case _:"],
            syntax_elements={"match_literal"}, **base))
        
        self._add(TestMatrixCase(
            id="E2", name="match_or_pattern",
            source_code='''def check(cmd):\n    match cmd:\n        case "start" | "go" | "begin":\n            return "run"\n        case "stop" | "end" | "halt":\n            return "stop"\n        case _:\n            return "unknown"\n''',
            required_patterns=["match cmd:", "case \"start\" | \"go\" | \"begin\":"],
            expected_patterns=["match cmd:", "|"],
            syntax_elements={"match_or"}, **base))
        
        self._add(TestMatrixCase(
            id="E3", name="match_guard",
            source_code='''def describe(point):\n    match point:\n        case (x, y) if x == y:\n            return "diagonal"\n        case (x, y):\n            return f"({x},{y})"\n        case _:\n            return "unknown"\n''',
            required_patterns=["match point:", "case (x, y):", "if x == y:"],
            expected_patterns=["match point:", "case (x, y):", "if x == y:"],
            syntax_elements={"match_guard"}, **base))
        
        self._add(TestMatrixCase(
            id="E4", name="match_class",
            source_code='''def handle(obj):\n    match obj:\n        case int() as n:\n            return f"int {n}"\n        case str() as s:\n            return f"str {s}"\n        case _:\n            return "other"\n''',
            required_patterns=["match obj:", "case int() as", "case str() as"],
            expected_patterns=["match obj:", "case int() as n:", "case str() as s:"],
            syntax_elements={"match_class"}, **base))
        
        self._add(TestMatrixCase(
            id="E5", name="match_mapping",
            source_code='''def get(d, key):\n    match d:\n        case {"name": n, "age": a}:\n            return (n, a)\n        case {}:\n            return None\n        case _:\n            return d.get(key)\n''',
            required_patterns=["match d:", 'case {"name":'],
            expected_patterns=["match d:", 'case {"name":'],
            syntax_elements={"match_mapping"}, **base))
        
        self._add(TestMatrixCase(
            id="E6", name="match_sequence",
            source_code='''def first_three(seq):\n    match seq:\n        case [a, b, c]:\n            return (a, b, c)\n        case [a, b]:\n            return (a, b, None)\n        case []:\n            return (None, None, None)\n        case _:\n            return tuple(seq[:3])\n''',
            required_patterns=["match seq:", "case [a, b, c]:"],
            expected_patterns=["match seq:", "case [a, b, c]:"],
            syntax_elements={"match_sequence"}, **base))
        
        self._add(TestMatrixCase(
            id="E7", name="match_as_pattern",
            source_code='''def head_tail(seq):\n    match seq:\n        case [first, *rest] as head_tail:\n            return (first, rest)\n        case []:\n            return (None, [])\n''',
            required_patterns=["match seq:", "case [first, *rest] as"],
            expected_patterns=["match seq:", "case [first, *rest] as head_tail:"],
            syntax_elements={"match_as"}, **base))
        
        self._add(TestMatrixCase(
            id="E8", name="match_in_function",
            source_code='''def categorize(value):\n    result = []\n    match value:\n        case int(v) if v > 0:\n            result.append("positive int")\n        case int(v):\n            result.append("non-positive int")\n        case str(s):\n            result.append(f"string: {s}")\n        case _:\n            result.append("other")\n    return result\n''',
            required_patterns=["match value:", "case int(", "case str(", "case _:"],
            expected_patterns=["match value:", "case int(", "case str("],
            syntax_elements={"match_in_func"}, **base))
        
        self._add(TestMatrixCase(
            id="E9", name="match_nested_match",
            source_code='''def deep_match(data):\n    match data:\n        case {"type": "point", "coords": [x, y]}:\n            match (x, y):\n                case (0, 0):\n                    return "origin"\n                case (_, _) if _ > 0:\n                    return "positive quadrant"\n                case _:\n                    return "other quadrant"\n        case _:\n            return "not a point"\n''',
            required_patterns=["match data:", "case {\"type\":", "match (x, y):"],
            expected_patterns=["match data:", "match (x, y):"],
            syntax_elements={"match_nested"}, **base))
    
    def _add_comprehensions(self):
        base = {"category": TestCategory.COMPREHENSION, "level": 0}
        
        self._add(TestMatrixCase(
            id="F1", name="list_comp", source_code='''def square(nums):\n    return [x**2 for x in nums]\n''',
            required_patterns=["[x**2 for x in nums]"],
            expected_patterns=["[x**2 for x in nums]"],
            syntax_elements={"list_comp"}, **base))
        
        self._add(TestMatrixCase(
            id="F2", name="dict_comp", source_code='''def invert(d):\n    return {v: k for k, v in d.items()}\n''',
            required_patterns=["{v: k for k, v in d.items()}"],
            expected_patterns=["{v: k for k, v in d.items()}"],
            syntax_elements={"dict_comp"}, **base))
        
        self._add(TestMatrixCase(
            id="F3", name="set_comp", source_code='''def unique(items):\n    return {x for x in items}\n''',
            required_patterns=["{x for x in items}"],
            expected_patterns=["{x for x in items}"],
            syntax_elements={"set_comp"}, **base))
        
        self._add(TestMatrixCase(
            id="F4", name="gen_expr", source_code='''def lazy_sum(data):\n    return sum(x**2 for x in data)\n''',
            required_patterns=["sum(", "(x**2 for x in data)"],
            expected_patterns=["sum(", "(x**2 for x in data)"],
            syntax_elements={"gen_expr"}, **base))
        
        self._add(TestMatrixCase(
            id="F5", name="comp_conditional",
            source_code='''def pos_even(nums):\n    return [x for x in nums if x > 0 and x % 2 == 0]\n''',
            required_patterns=["[x for x in nums if"],
            expected_patterns=["[x for x in nums if x > 0"],
            syntax_elements={"comp_if"}, **base))
        
        self._add(TestMatrixCase(
            id="F6", name="comp_walrus",
            source_code='''def extract(numbers):\n    return [result for n in numbers if (result := process(n)) > threshold]\n''',
            required_patterns=["[result for n in numbers if (result :="],
            expected_patterns=["[result for n in numbers if (result := process(n)) > threshold]"],
            syntax_elements={"comp_walrus"}, **base))
        
        self._add(TestMatrixCase(
            id="F7", name="comp_nested",
            source_code='''def flatten(matrix):\n    return [val for row in matrix for val in row]\n''',
            required_patterns=["[val for row in matrix for val in row]"],
            expected_patterns=["[val for row in matrix for val in row]"],
            syntax_elements={"comp_nested"}, **base))
        
        self._add(TestMatrixCase(
            id="F8", name="comp_in_func",
            source_code='''def filter_map(data):\n    return [process(x) for x in data if valid(x)]\n''',
            required_patterns=["[process(x) for x in data if valid(x)]"],
            expected_patterns=["[process(x) for x in data if valid(x)]"],
            syntax_elements={"comp_func_call"}, **base))
    
    def _add_nested_binary(self):
        base = {"category": TestCategory.NESTED, "level": 1}
        
        for_inner = ["if", "for", "while", "try", "with", "match"]
        for outer in for_inner:
            combo_id = f"N1_{outer}_in_{for_inner}"
            
            templates = {
                ("if", "if"): ('''def fn(data):\n    if cond_a:\n        if cond_b:\n            action()\n''', ["if cond_a:", "if cond_b:"], ["if cond_a:", "if cond_b:", "action()"]),
                ("if", "for"): ('''def fn(data):\n    if pred(data):\n        for x in data:\n            use(x)\n''', ["if pred(data):", "for x in data:"], ["if pred(data):", "for x in data:", "use(x)"]),
                ("if", "while"): ('''def fn(items):\n    if has_items:\n        while items:\n            proc(items.pop())\n''', ["if has_items:", "while items:"], ["if has_items:", "while items:"]),
                ("if", "try"): ('''def fn(item):\n    if valid(item):\n        try:\n            risky(item)\n        except Error:\n            fallback()\n''', ["if valid(item):", "try:", "except Error:"], ["if valid(item):", "try:", "risky(item)"]),
                ("if", "with"): ('''def fn(file_path, data):\n    if data:\n        with open(file_path, \'w\') as f:\n            f.write(str(data))\n''', ["if data:", "with open"], ["if data:", "with open"]),
                ("if", "match"): ('''def fn(value):\n    if isinstance(value, int):\n        match value:\n            case 0:\n                return "zero"\n            case _:\n                return f"int: {value}"\n        else:\n            return str(value)\n''', ["if isinstance", "match value:"], ["if isinstance", "match value:", "case 0:"]),
                ("for", "if"): ('''def fn(data):\n    result = []\n    for x in data:\n        if x > 0:\n            result.append(x)\n''', ["for x in data:", "if x > 0:"], ["for x in data:", "if x > 0:", "result.append(x)"]),
                ("for", "for"): ('''def fn(matrix):\n    result = []\n    for row in matrix:\n        for col in row:\n            result.append(col)\n    return result\n''', ["for row in matrix:", "for col in row:"], ["for row in matrix:", "for col in row:"]),
                ("for", "while"): ('''def fn(batch, max_retries):\n    attempts = 0\n    while attempts < max_retries:\n        for i in range(batch_size):\n            if attempt(i):\n                return True\n        attempts += 1\n''', ["while attempts <", "for i in range"], ["while attempts < max_retries:", "for i in range("]),
                ("for", "try"): ('''def fn(items):\n    results = []\n    for item in items:\n        try:\n            results.append(risky(item))\n        except RiskError:\n            results.append(None)\n    return results\n''', ["for item in items:", "try:", "except RiskError:"], ["for item in items:", "try:", "results.append"]),
                ("for", "with"): ('''def fn(files):\n    results = []\n    for f in files:\n        with open(f) as file:\n            results.append(file.read())\n    return results\n''', ["for f in files:", "with open(f)"], ["for f in files:", "with open(f) as file:", "file.read()"]),
                ("for", "match"): ('''def fn(pairs):\n    result = []\n    for a, b in pairs:\n        match (a, b):\n            case (x, y) if x > 0 and y > 0:\n                result.append((x, y))\n    return result\n''', ["for a, b in pairs:", "match (a, b):"], ["for a, b in pairs:", "match (a, b):"]),
                ("while", "if"): ('''def fn(items):\n    i = 0\n    while i < len(items):\n        if pred(items[i]):\n            found(items[i])\n            break\n        i += 1\n''', ["while i < len(items):", "if pred(items[i]):"], ["while i < len(items):", "found(items[i])"]),
                ("while", "for"): ('''def fn(max_retries):\n    attempts = 0\n    while attempts < max_retries:\n        for i in range(batch_size):\n            attempt(i)\n        attempts += 1\n''', ["while attempts <", "for i in range("], ["while attempts < max_retries:", "for i in range("]),
                ("while", "try"): ('''def fn(data):\n    while data:\n        try:\n            process(data.pop())\n        except EmptyError:\n            break\n''', ["while data:", "try:", "except EmptyError:"], ["while data:", "try:"]),
                ("while", "with"): ('''def fn(paths):\n    while paths:\n        path = paths.pop()\n        with open(path) as f:\n            contents.append(f.read())\n''', ["while paths:", "with open(path)"], ["while paths:", "with open(path) as f:"]),
                ("try", "if"): ('''def fn(item):\n    try:\n        if item is None:\n            raise ValueError("None")\n        process(item)\n    except ProcessError:\n        fallback()\n''', ["try:", "if item is None:"], ["try:", "if item is None:", "process(item)"]),
                ("try", "for"): ('''def fn(resources):\n    results = []\n    try:\n        for r in resources:\n            with r.lock:\n                data = r.read()\n                if data:\n                    results.append(parse(data))\n    finally:\n        cleanup(results)\n    return results\n''', ["try:", "for r in resources:", "with r.lock:"], ["try:", "for r in resources:", "parse(data)"]),
                ("try", "try"): ('''def fn(obj):\n    try:\n        try:\n            inner_risky(obj)\n        except InnerError:\n            recover_inner()\n    except OuterError:\n        recover_outer()\n''', ["try:", "try:", "except InnerError:", "except OuterError:"], ["try:", "try:", "inner_risky(obj)"]),
                ("with", "if"): ('''def fn(file_path, data):\n    with open(file_path, \'w\') as f:\n        if data:\n            f.write(str(data))\n        else:\n            f.write("empty")\n''', ["with open", "if data:", "else:"], ["with open", "if data:", "f.write(str(data))"]),
                ("with", "for"): ('''def fn(files):\n    with ThreadPool() as pool:\n        for path in files:\n            results.append(pool.submit(process, path))\n    return [r.result() for r in results]\n''', ["with ThreadPool() as pool:", "for path in files:"], ["with ThreadPool() as pool:", "for path in files:"]),
                ("with", "with"): ('''def fn(outer, inner):\n    with context_a(outer) as a:\n        with context_b(inner) as b:\n            combine(a, b)\n''', ["with context_a", "with context_b"], ["with context_a(outer) as a:", "with context_b(inner) as b:"]),
                ("with", "try"): ('''def fn(path):\n    with open(path) as f:\n        try:\n            return f.read()\n        except IOError:\n            return ""\n''', ["with open(path) as f:", "try:", "except IOError:"], ["with open(path) as f:", "try:", "f.read()"]),
                ("match", "if"): ('''def fn(value):\n    match value:\n        case int(v) if v > 0:\n            if v < 100:\n                return "small positive"\n            else:\n                return "large positive"\n        case _:\n            return "other"\n''', ["match value:", "case int(v) if v > 0:", "if v < 100:"], ["match value:", "case int(v) if v > 0:", "if v < 100:"]),
                ("match", "for"): ('''def fn(groups):\n    results = []\n    for g in groups:\n        match g:\n            case [name, score] if score > 80:\n                results.append(name)\n            case _:\n                pass\n    return results\n''', ["for g in groups:", "match g:", "case [name, score]"], ["for g in groups:", "match g:"]),
                ("match", "match"): ('''def fn(data):\n    match data:\n        case {"type": "outer", "inner": inner}:\n            match inner:\n                case {"value": v}:\n                    return v\n                case _:\n                    return None\n        case _:\n            return None\n''', ["match data:", "case {\"type\":", "match inner:"], ["match data:", "match inner:", "case {\"value\":"]),
            }
            
            if outer in templates and (outer, for_inner) in templates:
                src, req, exp = templates[(outer, for_inner)]
                self._add(TestMatrixCase(
                    id=combo_id, name=f"{outer}_in_{for_inner}",
                    source_code=src, required_patterns=req,
                    expected_patterns=exp,
                    description=f"{outer}包含{for_inner}",
                    syntax_elements={outer, for_inner},
                    **base))
    
    def _add_nested_ternary(self):
        base = {"category": TestCategory.NESTED, "level": 2}
        
        self._add(TestMatrixCase(
            id="N2_for_if_if", name="for_if_if",
            source_code='''def fn(data):\n    positives = []\n    negatives = []\n    for x in data:\n        if x > 0:\n            if x < 100:\n                positives.append(x)\n            else:\n                negatives.append(x)\n        else:\n            negatives.append(abs(x))\n''',
            required_patterns=["for x in data:", "if x > 0:", "if x < 100:"],
            expected_patterns=["for x in data:", "if x > 0:", "if x < 100:"],
            syntax_elements={"for", "if", "nested_if"},
            **base))
        
        self._add(TestMatrixCase(
            id="N2_for_if_try", name="for_if_try_except",
            source_code='''def fn(items):\n    results = []\n    for item in items:\n        try:\n            results.append(risky(item))\n        except RiskError:\n            results.append(None)\n            continue\n        safe_process(results)\n    return results\n''',
            required_patterns=["for item in items:", "try:", "except RiskError:"],
            expected_patterns=["for item in items:", "try:", "except RiskError:"],
            syntax_elements={"for", "if", "try", "continue"},
            **base))
        
        self._add(TestMatrixCase(
            id="N2_for_try_for", name="for_try_for",
            source_code='''def fn(rows):\n    flat = []\n    for row in rows:\n        try:\n            for cell in row:\n                flat.append(cell.value)\n        except InvalidCell:\n            continue\n    return flat\n''',
            required_patterns=["for row in rows:", "try:", "for cell in row:"],
            expected_patterns=["for row in rows:", "for cell in row:"],
            syntax_elements={"for", "try", "nested_for"},
            **base))
        
        self._add(TestMatrixCase(
            id="N2_try_for_with_for", name="try_for_with_for",
            source_code='''def fn(resources):\n    results = []\n    try:\n        for r in resources:\n            with r.lock:\n                for item in r.items:\n                    results.append(process(item))\n    finally:\n        save(results)\n    return results\n''',
            required_patterns=["try:", "for r in resources:", "with r.lock:", "for item in r.items:"],
            expected_patterns=["try:", "for r in resources:", "with r.lock:", "for item in r.items:"],
            syntax_elements={"try", "for", "with", "deep_nest"},
            **base))
        
        self._add(TestMatrixCase(
            id="N2_if_for_if_elif", name="if_for_if_elif",
            source_code='''def fn(data):\n    small = []\n    medium = []\n    large = []\n    for x in data:\n        if x < 10:\n            small.append(x)\n        elif x < 100:\n            medium.append(x)\n        else:\n            large.append(x)\n    return small + medium + large\n''',
            required_patterns=["for x in data:", "if x < 10:", "elif x < 100:"],
            expected_patterns=["for x in data:", "if x < 10:", "elif x < 100:"],
            syntax_elements={"for", "if", "elif"},
            **base))
    
    def _add_real_world(self):
        base = {"category": TestCategory.REAL_WORLD, "level": 2}
        
        self._add(TestMatrixCase(
            id="R1_data_pipeline", name="data_pipeline",
            source_code='''def pipeline(raw_data):\n    validated = []\n    for item in raw_data:\n        if item is None:\n            continue\n        cleaned = sanitize(item)\n        if not cleaned:\n            continue\n        enriched = transform(cleaned)\n        if validate(enriched):\n            validated.append(enriched)\n    return validated\n''',
            required_patterns=["for item in raw_data:", "if item is None:", "continue"],
            expected_patterns=["for item in raw_data:", "sanitize", "transform", "validate"],
            syntax_elements={"pipeline", "for_if_continue"},
            **base))
        
        self._add(TestMatrixCase(
            id="R2_state_machine", name="state_machine",
            source_code='''class StateMachine:\n    def run(self, events):\n        state = "idle"\n        for event in events:\n            match (state, event):\n                case ("idle", "start"):\n                    state = "running"\n                case ("running", "stop"):\n                    state = "idle"\n                case ("running", "pause"):\n                    state = "paused"\n                case ("paused", "resume"):\n                    state = "running"\n                case _:\n                    pass\n        return state\n''',
            required_patterns=["for event in events:", "match (state, event):", "case ("],
            expected_patterns=["for event in events:", "match (state, event):"],
            syntax_elements={"state_machine", "for_match"},
            **base))
        
        self._add(TestMatrixCase(
            id="R3_resource_management", name="resource_management",
            source_code='''def process_files(input_paths, output_dir):\n    results = {}\n    try:\n        with ThreadPoolExecutor() as pool:\n            futures = {}\n            for path in input_paths:\n                if not path.exists():\n                    continue\n                fut = pool.submit(load_and_parse, path)\n                futures[path] = fut\n\n            for path, fut in futures.items():\n                try:\n                    result = fut.result(timeout=30)\n                    results[path] = result\n                except TimeoutError:\n                    results[path] = "TIMEOUT"\n\n    except KeyboardInterrupt:\n        partial_save(results)\n        raise\n    finally:\n        write_results(results, output_dir)\n\n    return results\n''',
            required_patterns=["with ThreadPoolExecutor", "for path in input_paths:",
                        "try:", "except TimeoutError:", "finally:"],
            expected_patterns=["with ThreadPoolExecutor", "for path in input_paths:",
                        "finally:"],
            syntax_elements={"resource_mgmt", "try_for_with_finally"},
            **base))
    
    def _add_boundary(self):
        base = {"category": TestCategory.BOUNDARY, "level": 3}
        
        self._add(TestMatrixCase(
            id="BD1_empty_functions", name="empty_functions",
            source_code='''def empty_func():\n    pass\n\ndef empty_with_ret():\n    return\n\ndef empty_class:\n    pass\n''',
            required_patterns=["def empty_func():", "pass", "def empty_with_ret():"],
            expected_patterns=["def empty_func():", "pass", "def empty_with_ret():"],
            syntax_elements={"empty_func", "boundary"},
            **base))
        
        self._add(TestMatrixCase(
            id="BD2_single_line", name="single_line_statements",
            source_code='''def quick(x, y):\n    if x > 0: return True\n    return y * 2 if y > 0 else 0\n''',
            required_patterns=["if x > 0: return True", "return y * 2 if y > 0 else 0"],
            expected_patterns=["if x > 0: return True", "return y * 2 if y > 0 else 0"],
            syntax_elements={"oneline", "boundary"},
            **base))
        
        self._add(TestMatrixCase(
            id="BD3_extreme_elif", name="extreme_elif_chain",
            source_code='''def grade(score):\n    if score >= 90:\n        return "A"\n    elif score >= 80:\n        return "B"\n    elif score >= 70:\n        return "C"\n    elif score >= 60:\n        return "D"\n    elif score >= 50:\n        return "E"\n    else:\n        return "F"\n''',
            required_patterns=["if score >= 90:", "elif", "else:"],
            expected_patterns=["elif score >= 80:", "elif score >= 70:", "elif score >= 60:"],
            syntax_elements={"extreme_elif", "boundary"},
            **base))
        
        self._add(TestMatrixCase(
            id="BD4_complex_mix", name="complex_control_mix",
            source_code='''def chaos(data):\n    try:\n        for i, x in enumerate(data):\n            if x is None:\n                continue\n            if x == 0:\n                if i % 2 == 0:\n                    break\n            with open(\'log\', \'a\') as f:\n                f.write(f"{i}: {x}\\n")\n    finally:\n        cleanup()\n''',
            required_patterns=["try:", "for i, x in enumerate(data):", "with open"],
            expected_patterns=["try:", "for i, x in enumerate(data):", "with open('log'"],
            syntax_elements={"complex_mix", "boundary"},
            **base))
        
        self._add(TestMatrixCase(
            id="BD5_decorator", name="decorator_syntax",
            source_code='''def memoize(func):\n    cache = {}\n    def wrapper(*args, **kwargs):\n        key = (args, frozenset(kwargs.items()))\n        if key not in cache:\n            cache[key] = func(*args, **kwargs)\n        return cache[key]\n    return wrapper\n\n@memoize\ndef fib(n):\n    if n <= 1:\n        return n\n    return fib(n-1) + fib(n-2)\n''',
            required_patterns=["@memoize", "def fib(n):", "if n <= 1:"],
            expected_patterns=["@memoize", "def fib(n):", "fib(n-1)"],
            syntax_elements={"decorator", "recursion", "boundary"},
            **base))
        
        self._add(TestMatrixCase(
            id="BD6_generator_yield", name="generator_yield",
            source_code='''def count_up_to(n):\n    i = 0\n    while i < n:\n        yield i\n        i += 1\n''',
            required_patterns=["yield i", "while i < n:"],
            expected_patterns=["yield i", "while i < n:"],
            syntax_elements={"generator", "yield", "boundary"},
            **base))
        
        self._add(TestMatrixCase(
            id="BD7_async_def", name="async_full",
            source_code='''async def fetch_all(urls):\n    results = []\n    async with aiohttp.ClientSession() as session:\n        for url in urls:\n            async with session.get(url) as resp:\n                data = await resp.json()\n                if data.get(\"error\"):\n                    continue\n                results.append(data)\n    return results\n''',
            required_patterns=["async def fetch_all", "async with", "async with session.get",
                        "for url in urls:", "if data.get", "continue"],
            expected_patterns=["async def fetch_all", "async with aiohttp.ClientSession()",
                        "for url in urls:", "await resp.json()"],
            syntax_elements={"async_full", "boundary"},
            **base))
    
    def run_test(self, tc: TestMatrixCase) -> TestResult:
        start = time.perf_counter()
        tr = TestResult(id=tc.id, passed=False, score=0.0,
                       structure_correct=False, syntax_valid=False,
                       decompiled="")
        
        try:
            code_obj = compile(tc.source_code, '<test>', 'exec')
            namespace = {}
            exec(code_obj, namespace)
            
            func = None
            for name, obj in namespace.items():
                if isinstance(obj, types.FunctionType):
                    func = obj
                    break
            
            if func is None:
                tr.error = "No function found"
                tr.duration_ms = (time.perf_counter() - start) * 1000
                return tr
            
            from core.cfg.cfg_builder import build_cfg
            from core.cfg.region_ast_generator import RegionASTGenerator
            from core.cfg.ast_converter import CFGASTConverter
            from core.cfg.code_generator import CFGCodeGenerator
            
            cfg = build_cfg(func.__code__)
            gen = RegionASTGenerator(cfg)
            ast_dict = gen.generate()
            converter = CFGASTConverter()
            py_ast = converter.convert(ast_dict)
            code_gen = CFGCodeGenerator()
            tr.decompiled = code_gen.generate(py_ast, in_function=True)
            
            tr.duration_ms = (time.perf_counter() - start) * 1000
            
            try:
                ast.parse(tr.decompiled)
                tr.syntax_valid = True
            except SyntaxError:
                tr.syntax_valid = False
            
            req_met = sum(1 for p in tc.required_patterns if p in tr.decompiled)
            req_total = len(tc.required_patterns) if tc.required_patterns else 1
            tr.structure_correct = (req_met / req_total >= 0.7) if req_total > 0 else False
            
            exp_met = sum(1 for p in tc.expected_patterns if p in tr.decompiled)
            exp_total = len(tc.expected_patterns) if tc.expected_patterns else 1
            tr.score = (exp_met / exp_total * 80 + req_met / req_total * 20) if exp_total > 0 else (req_met / req_total * 100)
            
            tr.missing_required = [p for p in tc.required_patterns if p not in tr.decompiled]
            tr.unexpected_forbidden = [p for p in tc.forbidden_patterns if p in tr.decompiled]
            
            if tr.structure_correct and tr.syntax_valid and tr.score >= 60:
                tr.passed = True
            
        except Exception as e:
            tr.error = f"{type(e).__name__}: {e}"
            tr.duration_ms = (time.perf_counter() - start) * 1000
        
        return tr
    
    def run_all(self, verbose=True, category_filter=None, level_filter=None):
        cases = self.test_cases
        
        if category_filter:
            cat_name = category_filter.lower() if isinstance(category_filter, str) else None
            cats = [TestCategory(c) for c in (category_filter if isinstance(category_filter, list) else [category_filter])]
            cases = [tc for tc in cases if tc.category.name.lower() in [c.name.lower() for c in cats]]
        
        if level_filter is not None:
            levels = level_filter if isinstance(level_filter, list) else [level_filter]
            cases = [tc for tc in cases if tc.level in levels]
        
        self.results = []
        passed = 0
        failed = 0
        errors = 0
        
        for tc in cases:
            tr = self.run_test(tc)
            self.results.append(tr)
            
            if verbose:
                status = "\u2713 FAIL" if not tr.passed else ("\u229e PARTIAL" if tr.score < 100 else "\u2713 PASS")
                score_info = f"(score:{tr.score:.0f}, missing: {tr.missing_required})"
                print(f"[{len(self.results):>3d}/{len(cases)}] {status} {tc.id:<35s} ({tc.category.value:<12s} L{tc.level}) {score_info}")
                if not tr.passed or tr.score < 100:
                    if tr.missing_required:
                        print(f"       missing: {tr.missing_required}")
                    if tr.unexpected_forbidden:
                        print(f"       unexpected: {tr.unexpected_forbidden}")
                    if tr.decompiled and len(tr.decompiled) < 200:
                        print(f"       output: {repr(tr.decompiled)}")
                    if tr.error:
                        print(f"       \u2757 ERROR: {tr.error}")
            
            if tr.passed:
                passed += 1
            elif tr.error:
                errors += 1
            else:
                failed += 1
        
        total = len(cases)
        struct_ok = sum(1 for r in self.results if r.structure_correct)
        avg_score = sum(r.score for r in self.results) / max(total, 1)
        
        print("\n" + "=" * 72)
        print(f"完备性测试矩阵 v6.0 结果")
        print("=" * 72)
        print(f"总测试数: {total} | 通过: {passed} ({passed/max(total,1)*100:.1f}%) | "
              f"部分: {failed-passed} | 错误: {errors}")
        print(f"结构正确率: {struct_ok/max(total,1)*100:.1f}% | 平均分: {avg_score:.1f}")
        
        by_cat = {}
        for r in self.results:
            cat = r.id.split("_")[0]
            if cat not in by_cat:
                by_cat[cat] = {"total": 0, "pass": 0, "struct": 0, "score": 0}
            by_cat[cat]["total"] += 1
            if r.passed: by_cat[cat]["pass"] += 1
            if r.structure_correct: by_cat[cat]["struct"] += 1
            by_cat[cat]["score"] += r.score
        
        print(f"\n按类别:")
        for cat, stats in sorted(by_cat.items()):
            pct = stats["pass"]/stats["total"]*100
            print(f"  {cat}: {stats['pass']}/{stats['total']} ({pct:.0f}%) 结构:{stats['struct']}/{stats['total']} 均{stats['score']/max(stats['total'],1):.0f}")
        
        return {"passed": passed, "failed": failed, "errors": errors, "total": total,
                "struct_rate": struct_ok/max(total,1), "avg_score": avg_score}


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="完备性测试矩阵 v6.0")
    parser.add_argument("--category", nargs="+", help="过滤类别")
    parser.add_argument("--level", type=int, nargs="+", help="过滤级别")
    parser.add_argument("--ci", action="store_true", help="CI模式")
    args = parser.parse_args()
    
    suite = ComprehensiveTestMatrix()
    print(f"\n完备性测试矩阵 v6.0")
    print(f"测试用例总数: {len(suite.test_cases)}")
    
    cat_counts = {}
    for tc in suite.test_cases:
        cn = tc.category.name[0]
        cat_counts[cn] = cat_counts.get(cn, 0) + 1
    print(f"  类别分布: {dict(sorted(cat_counts.items()))}")
    
    lev_counts = {}
    for tc in suite.test_cases:
        lev_counts[tc.level] = lev_counts.get(tc.level, 0) + 1
    print(f"  级别分布: {dict(sorted(lev_counts.items()))}")
    
    print("\n开始运行...\n")
    stats = suite.run_all(verbose=True,
                          category_filter=args.category,
                          level_filter=args.level)
    
    if args.ci:
        import json
        print(json.dumps(stats))
        sys.exit(0 if stats["passed"] / max(stats["total"], 1) >= 0.5 else 1)
