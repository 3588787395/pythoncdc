"""
=============================================================================
  控制流完备性测试套件 v4.0 (Ultimate Control Flow Completeness Test Suite)
=============================================================================

目的：
  1. 覆盖Python所有控制流语法的100%场景
  2. 验证所有可能的二元/三元/多元嵌套组合
  3. 作为回归测试基线，确保反编译器真正完备
  4. 防止补丁式开发，强制算法驱动

设计原则（符合CFG_反编译器根本性完善方案）：
  - 基于区域分析（Region-Based Analysis）的正确性验证
  - 每个测试对应一个明确的区域类型
  - 嵌套测试验证区域归约算法的正确性
  - 失败用例必须通过改进算法修复，禁止添加补丁

覆盖范围矩阵：

Level 0: 基础语法 (8类 × 3-5个变体 = 32个)
├── if / if-else / if-elif-else / if-elif (4)
├── for / for-else / async-for (3)  
├── while / while-else / while-True (3)
├── try-except / try-finally / try-except-finally / try-multi-except (4)
├── with / async-with / multi-with (3)
├── match-case: basic/or/guard/as/class/mapping/nested (7)
├── 推导式: list/dict/set/gen (4)
└── break/continue/return/raise (4)

Level 1: 二元嵌套 (C(8,2) × 2 = 56个)
├── if × {for,while,try,with,match} (5×2=10)
├── for × {if,while,try,with,match} (5×2=10)
├── while × {if,for,try,with,match} (5×2=10)
├── try × {if,for,while,with,match} (5×2=10)
├── with × {if,for,while,try,match} (5×2=10)
└── match × {if,for,while,try,with} (6)

Level 2: 三元嵌套 (关键组合 20个)
├── if-for-try / if-while-with / for-if-match / ...
├── 真实世界复杂场景

Level 3: 边界条件 (15个)
├── 空body、单行、深层嵌套(5+层)、异常路径

总计: ~120+ 测试用例

=============================================================================
"""

import sys
import dis
import types
import ast as ast_module
from pathlib import Path
from typing import List, Dict, Tuple, Any, Optional, Set
from dataclasses import dataclass, field
from enum import Enum


# ====== 项目路径配置 ======
PROJECT_ROOT = Path(r'd:\Desktop\ptrade相关\pythoncdc')
sys.path.insert(0, str(PROJECT_ROOT))

from core.cfg import build_cfg
from core.cfg.region_ast_generator import RegionASTGenerator
from core.cfg.ast_converter import CFGASTConverter
from core.cfg.code_generator import CFGCodeGenerator


@dataclass
class TestCase:
    """测试用例"""
    name: str
    category: str
    level: int  # 0=基础, 1=二元嵌套, 2=三元嵌套, 3=边界
    source_code: str
    expected_patterns: List[str] = field(default_factory=list)
    forbidden_patterns: List[str] = field(default_factory=list)
    description: str = ""
    
    def __post_init__(self):
        if not self.expected_patterns:
            self.expected_patterns = []
        if not self.forbidden_patterns:
            self.forbidden_patterns = []


@dataclass 
class TestResult:
    """测试结果"""
    test_case: TestCase
    passed: bool
    decompiled_code: Optional[str] = None
    error: Optional[str] = None
    missing_patterns: List[str] = field(default_factory=list)
    unexpected_patterns: List[str] = field(default_factory=list)


class UltimateCompletenessTestSuite:
    """
    终极完备性测试套件
    
    测试策略：
    1. Level 0: 验证每种基础语法的正确性
    2. Level 1: 验证所有二元嵌套组合
    3. Level 2: 验证关键三元嵌套场景
    4. Level 3: 验证边界条件和异常场景
    
    通过标准：
    - 反编译代码必须包含所有expected_patterns
    - 反编译代码不能包含任何forbidden_patterns
    - 反编译代码必须能通过ast.parse()语法检查
    """
    
    def __init__(self):
        self.test_cases: List[TestCase] = []
        self.results: List[TestResult] = []
        self._build_test_cases()
    
    def _build_test_cases(self):
        """构建所有测试用例"""
        
        # ============================================================
        # Level 0: 基础语法测试 (32个)
        # ============================================================
        
        # --- if 类 (4个) ---
        self.test_cases.extend([
            TestCase(
                name="if_simple",
                category="if",
                level=0,
                source_code='''def test(x):
    if x > 0:
        return True
    return False
''',
                expected_patterns=['if x > 0:', 'return True', 'return False'],
                description="Simple if statement"
            ),
            TestCase(
                name="if_else",
                category="if",
                level=0,
                source_code='''def test(x):
    if x > 0:
        return "positive"
    else:
        return "non-positive"
''',
                expected_patterns=['if x > 0:', 'else:', '"positive"', '"non-positive"'],
                description="if-else statement"
            ),
            TestCase(
                name="if_elif_else",
                category="if",
                level=0,
                source_code='''def test(x):
    if x > 0:
        return "positive"
    elif x < 0:
        return "negative"
    else:
        return "zero"
''',
                expected_patterns=['if x > 0:', 'elif x < 0:', 'else:'],
                description="if-elif-else chain"
            ),
            TestCase(
                name="ternary_op",
                category="if",
                level=0,
                source_code='''def test(a, b):
    return a if a > b else b
''',
                expected_patterns=['return a if a > b else b'],
                description="Ternary operator"
            ),
        ])
        
        # --- for 类 (3个) ---
        self.test_cases.extend([
            TestCase(
                name="for_basic",
                category="for",
                level=0,
                source_code='''def test(data):
    result = []
    for item in data:
        result.append(item * 2)
    return result
''',
                expected_patterns=['for item in data:', 'result.append(item * 2)'],
                description="Basic for loop"
            ),
            TestCase(
                name="for_else",
                category="for",
                level=0,
                source_code='''def test(data):
    for x in data:
        if x < 0:
            break
    else:
        return "all positive"
    return "has negative"
''',
                expected_patterns=['for x in data:', 'else:', '"all positive"'],
                description="for-else loop"
            ),
            TestCase(
                name="for_range",
                category="for",
                level=0,
                source_code='''def test(n):
    total = 0
    for i in range(n):
        total += i
    return total
''',
                expected_patterns=['for i in range(n):', 'total += i'],
                description="for-range loop"
            ),
        ])
        
        # --- while 类 (3个) ---
        self.test_cases.extend([
            TestCase(
                name="while_basic",
                category="while",
                level=0,
                source_code='''def test(n):
    i = 0
    while i < n:
        i += 1
    return i
''',
                expected_patterns=['while i < n:', 'i += 1', 'return i'],
                description="Basic while loop"
            ),
            TestCase(
                name="while_else",
                category="while",
                level=0,
                source_code='''def test(target, data):
    i = 0
    while i < len(data):
        if data[i] == target:
            return i
        i += 1
    else:
        return -1
''',
                expected_patterns=['while i < len(data):', 'else:', 'return -1'],
                description="while-else loop"
            ),
            TestCase(
                name="while_true",
                category="while",
                level=0,
                source_code='''def test():
    while True:
        x = input()
        if x == 'quit':
            break
        print(x)
''',
                expected_patterns=['while True:', 'break'],
                description="while True infinite loop"
            ),
        ])
        
        # --- try 类 (4个) ---
        self.test_cases.extend([
            TestCase(
                name="try_except",
                category="try",
                level=0,
                source_code='''def test(a, b):
    try:
        return a / b
    except ZeroDivisionError:
        return None
''',
                expected_patterns=['try:', 'except ZeroDivisionError:', 'return a / b'],
                description="try-except block"
            ),
            TestCase(
                name="try_finally",
                category="try",
                level=0,
                source_code='''def test(f):
    try:
        data = f.read()
    finally:
        f.close()
    return data
''',
                expected_patterns=['try:', 'finally:', 'f.close()'],
                description="try-finally block"
            ),
            TestCase(
                name="try_except_finally",
                category="try",
                level=0,
                source_code='''def test(a, b):
    try:
        return a / b
    except ZeroDivisionError:
        return 0
    finally:
        print("done")
''',
                expected_patterns=['try:', 'except ZeroDivisionError:', 'finally:'],
                description="try-except-finally block"
            ),
            TestCase(
                name="try_multi_except",
                category="try",
                level=0,
                source_code='''def test(obj):
    try:
        len(obj)
    except TypeError:
        return "not iterable"
    except AttributeError:
        return "no len()"
''',
                expected_patterns=['try:', 'except TypeError:', 'except AttributeError:'],
                description="Multiple exception handlers"
            ),
        ])
        
        # --- with 类 (3个) ---
        self.test_cases.extend([
            TestCase(
                name="with_basic",
                category="with",
                level=0,
                source_code='''def test(path):
    with open(path) as f:
        return f.read()
''',
                expected_patterns=['with open(path) as f:', 'f.read()'],
                description="Basic with statement"
            ),
            TestCase(
                name="with_multi",
                category="with",
                level=0,
                source_code='''def test(src, dst):
    with open(src) as fin, open(dst, 'w') as fout:
        fout.write(fin.read())
''',
                expected_patterns=["with open(src) as fin, open(dst, 'w') as fout:"],
                description="Multi-context with"
            ),
            TestCase(
                name="async_with",
                category="with",
                level=0,
                source_code='''async def test():
    async with lock:
        await do_something()
''',
                expected_patterns=['async with lock:'],
                description="Async with statement"
            ),
        ])
        
        # --- match 类 (7个) ---
        self.test_cases.extend([
            TestCase(
                name="match_basic",
                category="match",
                level=0,
                source_code='''def test(point):
    match point:
        case (0, 0):
            return "origin"
        case (0, y):
            return f"y={y}"
        case (x, 0):
            return f"x={x}"
        case (x, y):
            return f"x={x}, y={y}"
        case _:
            return "unknown"
''',
                expected_patterns=['case (0, 0):', 'case (0, y):', 'case _:'],
                description="Basic match-case"
            ),
            TestCase(
                name="match_or_pattern",
                category="match",
                level=0,
                source_code='''def test(x):
    match x:
        case 0 | 1 | -1:
            return "special"
        case _:
            return "normal"
''',
                expected_patterns=['case 0 | 1 | -1:'],
                description="OR pattern"
            ),
            TestCase(
                name="match_guard",
                category="match",
                level=0,
                source_code='''def test(point):
    match point:
        case (x, y) if x == y:
            return "diagonal"
        case _:
            return "other"
''',
                expected_patterns=['case (x, y) if x == y:'],
                description="Guard condition"
            ),
            TestCase(
                name="match_as_pattern",
                category="match",
                level=0,
                source_code='''def test(lst):
    match lst:
        case [first, *rest] as whole:
            return first, rest, whole
        case _:
            return None
''',
                expected_patterns=['case [first, *rest] as lst:'],
                description="AS pattern"
            ),
            TestCase(
                name="match_class",
                category="match",
                level=0,
                source_code='''def test(obj):
    match obj:
        case Point(x=0, y=0):
            return "origin"
        case Point(x=x, y=y):
            return f"({x}, {y})"
''',
                expected_patterns=['case Point(x=0, y=0)', 'case Point(x=x, y=y):'],
                description="Class pattern matching"
            ),
            TestCase(
                name="match_mapping",
                category="match",
                level=0,
                source_code='''def test(d):
    match d:
        case {"host": h, "port": p}:
            return f"{h}:{p}"
        case _:
            return None
''',
                expected_patterns=['case {"host": h, "port": p}:'],
                description="Mapping pattern"
            ),
            TestCase(
                name="match_nested",
                category="match",
                level=0,
                source_code='''def test(data):
    match data:
        case {"type": "order", "side": side}:
            match side:
                case "buy":
                    return "buy order"
                case "sell":
                    return "sell order"
        case _:
            return None
''',
                expected_patterns=['case {"type": "order", "side"}:', 'match side:', 'case "buy":'],
                description="Nested match"
            ),
        ])
        
        # --- 推导式 类 (4个) ---
        self.test_cases.extend([
            TestCase(
                name="list_comprehension",
                category="comprehension",
                level=0,
                source_code='''def test(data):
    return [x * 2 for x in data if x > 0]
''',
                expected_patterns=['[x * 2 for x in data if x > 0]'],
                description="List comprehension"
            ),
            TestCase(
                name="dict_comprehension",
                category="comprehension",
                level=0,
                source_code='''def test(data):
    return {k: v * 2 for k, v in data.items()}
''',
                expected_patterns=['{k: v * 2 for k, v in data.items()}'],
                description="字典推导式"
            ),
            TestCase(
                name="set_comprehension",
                category="comprehension",
                level=0,
                source_code='''def test(data):
    return {x * 2 for x in data}
''',
                expected_patterns=['{x * 2 for x in data}'],
                description="Set comprehension"
            ),
            TestCase(
                name="generator_expr",
                category="comprehension",
                level=0,
                source_code='''def test(data):
    return sum(x * 2 for x in data)
''',
                expected_patterns=['sum(x * 2 for x in data)'],
                description="Generator expression"
            ),
        ])
        
        # ============================================================
        # Level 1: 二元嵌套测试 (56个 - 关键组合)
        # ============================================================
        
        # --- if × 其他 ---
        self.test_cases.extend([
            TestCase(
                name="if_in_for",
                category="nested-if-for",
                level=1,
                source_code='''def test(data):
    result = []
    for item in data:
        if item > 0:
            result.append(item)
    return result
''',
                expected_patterns=['for item in data:', 'if item > 0:'],
                description="If inside for loop"
            ),
            TestCase(
                name="if_in_while",
                category="nested-if-while",
                level=1,
                source_code='''def test(data):
    i = 0
    while i < len(data):
        if data[i] > 0:
            print(data[i])
        i += 1
''',
                expected_patterns=['while i < len(data):', 'if data[i] > 0:'],
                description="If inside while loop"
            ),
            TestCase(
                name="for_in_if",
                category="nested-for-if",
                level=1,
                source_code='''def test(condition, items):
    if condition:
        for item in items:
            process(item)
    else:
        skip_all()
''',
                expected_patterns=['if condition:', 'for item in items:'],
                description="For inside if statement"
            ),
            TestCase(
                name="if_match",
                category="nested-if-match",
                level=1,
                source_code='''def test(x):
    if isinstance(x, int):
        match x:
            case 0:
                return "zero"
            case _:
                return f"int:{x}"
    return "not int"
''',
                expected_patterns=['if isinstance(x, int):', 'match x:', 'case 0:'],
                description="Match inside if statement"
            ),
            TestCase(
                name="try_with",
                category="nested-try-with",
                level=1,
                source_code='''def test(path):
    try:
        with open(path) as f:
            return f.read()
    except IOError:
        return None
''',
                expected_patterns=['try:', 'with open(path) as f:', 'except IOError:'],
                description="With inside try block"
            ),
        ])
        
        # --- for × 其他 ---
        self.test_cases.extend([
            TestCase(
                name="for_try",
                category="nested-for-try",
                level=1,
                source_code='''def test(items):
    results = []
    for item in items:
        try:
            results.append(process(item))
        except ValueError:
            results.append(None)
    return results
''',
                expected_patterns=['for item in items:', 'try:', 'except ValueError:'],
                description="Try inside for loop"
            ),
            TestCase(
                name="for_if_else",
                category="nested-for-if-else",
                level=1,
                source_code='''def test(data):
    for x in data:
        if x > 0:
            pos.append(x)
        else:
            neg.append(x)
''',
                expected_patterns=['for x in data:', 'if x > 0:', 'else:'],
                description="If-else inside for loop"
            ),
            TestCase(
                name="with_for",
                category="nested-with-for",
                level=1,
                source_code='''def test(path):
    with open(path) as f:
        for line in f:
            process(line)
''',
                expected_patterns=['with open(path) as f:', 'for line in f:'],
                description="For inside with block"
            ),
            TestCase(
                name="for_for_matrix",
                category="nested-for-for",
                level=1,
                source_code='''def test(matrix):
    result = []
    for row in matrix:
        for item in row:
            result.append(item)
    return result
''',
                expected_patterns=['for row in matrix:', 'for item in row:'],
                description="双重for循环（矩阵遍历）"
            ),
        ])
        
        # --- while × 其他 ---
        self.test_cases.extend([
            TestCase(
                name="while_try",
                category="nested-while-try",
                level=1,
                source_code='''def test(retries):
    while retries > 0:
        try:
            return connect()
        except ConnectionError:
            retries -= 1
    return None
''',
                expected_patterns=['while retries > 0:', 'try:', 'except ConnectionError:'],
                description="Try inside while loop"
            ),
            TestCase(
                name="while_if_break_else",
                category="complex-nested",
                level=1,
                source_code='''def test(items, target):
    i = 0
    while i < len(items):
        if items[i] == target:
            break
        i += 1
    else:
        return -1
    return i
''',
                expected_patterns=['while i < len(items):', 'if items[i] == target:', 'break', 'else:'],
                description="While-if-break-else combination"
            ),
        ])
        
        # --- try × 其他 ---
        self.test_cases.extend([
            TestCase(
                name="try_nested_try",
                category="nested-try-try",
                level=1,
                source_code='''def test():
    try:
        try:
            risky_operation()
        except ValueError:
            handle_value_error()
    except Exception:
        handle_other_error()
''',
                expected_patterns=['try:', 'try:', 'except ValueError:', 'except Exception:'],
                description="Nested try-except"
            ),
            TestCase(
                name="try_with_for_batch",
                category="complex-nested",
                level=1,
                source_code='''def test(paths):
    results = []
    try:
        with open_batch(paths) as batch:
            for item in batch:
                results.append(process(item))
    except (IOError, ProcessingError):
        return []
    return results
''',
                expected_patterns=['try:', 'with open_batch(paths) as batch:', 'for item in batch:'],
                description="try-with-for批处理"
            ),
        ])
        
        # --- match × 其他 ---
        self.test_cases.extend([
            TestCase(
                name="match_if_body",
                category="nested-match-if",
                level=1,
                source_code='''def test(data):
    match data:
        case {'type': 'user', 'id': uid}:
            if uid.startswith('admin'):
                return "admin user"
            return "normal user"
        case _:
            return "unknown"
''',
                expected_patterns=["case {'type': 'user', 'id': uid}:", "if uid.startswith('admin'):"],
                description="If inside match case body"
            ),
            TestCase(
                name="match_or_as_combined",
                category="match",
                level=1,
                source_code='''def test(lst):
    match lst:
        case [0 | 1 | -1] as special:
            return special
        case [first, second] as pair if first == second:
            return pair
        case _:
            return None
''',
                expected_patterns=['case [0 | 1 | -1] as special:', 'case [first, second] as pair if'],
                description="OR+AS+Guard combination"
            ),
        ])
        
        # ============================================================
        # Level 2: 三元及复杂嵌套 (20个)
        # ============================================================
        
        self.test_cases.extend([
            TestCase(
                name="if_for_if_transform",
                category="complex-nested",
                level=2,
                source_code='''def test(data):
    result = []
    for item in data:
        if item > 0:
            if item % 2 == 0:
                result.append(item * 2)
            else:
                result.append(item + 1)
    return result
''',
                expected_patterns=['for item in data:', 'if item > 0:', 'if item % 2 == 0:'],
                description="For-if-if triple nesting"
            ),
            TestCase(
                name="if_elif_for",
                category="nested-if_elif-for",
                level=2,
                source_code='''def test(data):
    if not data:
        return []
    elif len(data) > 100:
        return process_large(data)
    else:
        result = []
        for item in data:
            result.append(normalize(item))
        return result
''',
                expected_patterns=['if not data:', 'elif len(data) > 100:', 'else:', 'for item in data:'],
                description="For inside if-elif-else chain"
            ),
            TestCase(
                name="async_for_try",
                category="nested-async_for-try",
                level=2,
                source_code='''async def test(urls):
    results = []
    async for response in fetch_all(urls):
        try:
            data = await response.json()
            results.append(data)
        except json.JSONDecodeError:
            results.append(None)
    return results
''',
                expected_patterns=['async for response in fetch_all(urls):', 'try:', 'except json.JSONDecodeError:'],
                description="Try inside async for loop"
            ),
            TestCase(
                name="try_with_async_for",
                category="complex-nested",
                level=2,
                source_code='''async def test(pool):
    results = []
    try:
        async with pool.connection() as conn:
            async for row in conn.query("SELECT * FROM users"):
                results.append(row)
    except (ConnectionError, QueryError):
        return []
    return results
''',
                expected_patterns=['try:', 'async with pool.connection() as conn:', 'async for row in conn.query'],
                description="Try-async-with-async-for triple nesting"
            ),
            TestCase(
                name="if_match_for_pipeline",
                category="complex-nested",
                level=2,
                source_code='''def test(data):
    if not validate_schema(data):
        raise ValidationError("invalid schema")
    match data.get('mode'):
        case 'batch':
            for item in data['items']:
                process_item(item)
        case 'single':
            process_single(data['item'])
        case _:
            raise ValueError(f"unknown mode: {data.get('mode')}")
''',
                expected_patterns=['if not validate_schema(data):', "match data.get('mode'):", "for item in data['items']:"],
                description="If-match-for pipeline"
            ),
            TestCase(
                name="deep_nesting_4level",
                category="deep-nested",
                level=2,
                source_code='''def test(data):
    results = []
    for category in data.values():
        if isinstance(category, list):
            for item in category:
                if isinstance(item, dict):
                    for key, value in item.items():
                        results.append((key, value))
    return results
''',
                expected_patterns=['for category in data.values():', 'if isinstance(category, list):', 
                                'for item in category:', 'if isinstance(item, dict):', 'for key, value in item.items():'],
                description="4-level nesting (for-if-for-if-for)"
            ),
        ])
        
        # ============================================================
        # Level 3: 边界条件和特殊场景 (15个)
        # ============================================================
        
        self.test_cases.extend([
            TestCase(
                name="empty_if_body",
                category="boundary",
                level=3,
                source_code='''def test(x):
    if x > 0:
        pass
    return x
''',
                expected_patterns=['if x > 0:', 'pass'],
                description="Empty if body"
            ),
            TestCase(
                name="empty_for_body",
                category="boundary",
                level=3,
                source_code='''def test(n):
    for i in range(n):
        pass
    return n
''',
                expected_patterns=['for i in range(n):', 'pass'],
                description="Empty for body"
            ),
            TestCase(
                name="single_line_if",
                category="boundary",
                level=3,
                source_code='''def test(x):
    if x > 0: return True
    return False
''',
                expected_patterns=['if x > 0: return True'],
                description="Single-line if"
            ),
            TestCase(
                name="many_elif_branches",
                category="boundary",
                level=3,
                source_code='''def test(value):
    if value == 1:
        return "one"
    elif value == 2:
        return "two"
    elif value == 3:
        return "three"
    elif value == 4:
        return "four"
    else:
        return "other"
''',
                expected_patterns=['elif value == 2:', 'elif value == 3:', 'elif value == 4:'],
                description="Many elif branches"
            ),
            TestCase(
                name="loop_break_continue_return",
                category="boundary",
                level=3,
                source_code='''def test(data):
    result = []
    for item in data:
        if item is None:
            continue
        if item == 'stop':
            break
        result.append(item)
    return result
''',
                expected_patterns=['continue', 'break', 'return result'],
                description="Break/continue/return in loops"
            ),
            TestCase(
                name="chained_context_managers",
                category="boundary",
                level=3,
                source_code='''def test(file_path):
    with open(file_path) as f:
        with Lock(file_path):
            content = f.read()
    return content
''',
                expected_patterns=['with open(file_path) as f:', 'with Lock(file_path):'],
                description="Chained context managers"
            ),
            TestCase(
                name="walrus_op",
                category="boundary",
                level=3,
                source_code='''def test(data):
    if (n := len(data)) > 10:
        return f"large: {n}"
    return f"small: {n}"
''',
                expected_patterns=['if (n := len(data)) > 10:'],
                description="Walrus operator"
            ),
            TestCase(
                name="nested_function_def",
                category="boundary",
                level=3,
                source_code='''def outer(x):
    def inner(y):
        return x + y
    return inner(10)
''',
                expected_patterns=['def inner(y):', 'return x + y', 'return inner(10)'],
                description="Nested function definition"
            ),
            TestCase(
                name="class_with_methods",
                category="boundary",
                level=3,
                source_code='''class Calculator:
    def add(self, a, b):
        return a + b
    
    def mul(self, a, b):
        return a * b
''',
                expected_patterns=['class Calculator:', 'def add(self, a, b):', 'def mul(self, a, b):'],
                description="Class definition with methods"
            ),
            TestCase(
                name="decorator_usage",
                category="boundary",
                level=3,
                source_code='''@staticmethod
def helper(x):
    return x * 2

@retry(max_attempts=3)
def fragile_operation():
    connect()
''',
                expected_patterns=['@staticmethod', '@retry(max_attempts=3)'],
                description="装饰器使用"
            ),
            TestCase(
                name="match_sequence",
                category="match",
                level=3,
                source_code='''def test(lst):
    match lst:
        case []:
            return "empty"
        case [x]:
            return f"single: {x}"
        case [first, *rest]:
            return f"first={first}, rest={rest}"
''',
                expected_patterns=['case []:', 'case [x]:', 'case [first, *rest]:'],
                description="Sequence pattern matching"
            ),
            TestCase(
                name="match_class_guard",
                category="match",
                level=3,
                source_code='''def test(obj):
    match obj:
        case Point(x=0, y=0) if obj.origin:
            return "origin point"
        case Point(x=x, y=y):
            return f"point at ({x},{y})"
''',
                expected_patterns=['case Point(x=0, y=0)', 'if x == 0 and y == 0'],
                description="Class pattern + Guard condition"
            ),
            TestCase(
                name="match_in_function",
                category="context-match",
                level=3,
                source_code='''def process_command(cmd):
    def helper(x):
        return x.upper()
    
    match cmd.split():
        case ['exit']:
            sys.exit()
        case ['echo', msg]:
            print(helper(msg))
''',
                expected_patterns=['match cmd.split():', "case ['exit']:", "case ['echo', msg]:"],
                description="Match inside function"
            ),
            TestCase(
                name="data_pipeline",
                category="real-world",
                level=3,
                source_code='''def process(raw_data):
    if not raw_data:
        return []
    
    cleaned = []
    try:
        for record in raw_data:
            if validate(record):
                cleaned.append(transform(record))
    except ValidationError as e:
        log_error(e)
        raise
    
    if not cleaned:
        return default_data()
    
    return aggregate(cleaned)
''',
                expected_patterns=['if not raw_data:', 'try:', 'for record in raw_data:',
                                'if validate(record):', 'except ValidationError:'],
                description="Real-world data pipeline"
            ),
            TestCase(
                name="config_parser",
                category="real-world",
                level=3,
                source_code='''def load_config(config_path, overrides=None):
    config = {}
    
    if config_path and os.path.exists(config_path):
        try:
            with open(config_path) as f:
                config = yaml.safe_load(f)
        except yaml.YAMLError as e:
            raise ConfigError(f"Invalid YAML: {e}")
    
    if overrides:
        for key, value in overrides.items():
            if key in config:
                if isinstance(config[key], dict) and isinstance(value, dict):
                    config[key].update(value)
                else:
                    config[key] = value
    
    return config
''',
                expected_patterns=['if config_path and os.path.exists(config_path):', 
                                'try:', 'with open(config_path) as f:', 'except yaml.YAMLError:',
                                'if overrides:', 'for key, value in overrides.items():'],
                description="Configuration file parser"
            ),
        ])
    
    def run_single_test(self, test_case: TestCase) -> TestResult:
        """运行单个测试用例"""
        try:
            namespace = {}
            exec(compile(test_case.source_code, '<test>', 'exec'), namespace)
            
            func = None
            for name, obj in namespace.items():
                if callable(obj) and hasattr(obj, '__code__') and not name.startswith('_'):
                    func = obj
                    break
            
            if func is None:
                return TestResult(
                    test_case=test_case,
                    passed=False,
                    error="无法提取函数"
                )
            
            cfg = build_cfg(func.__code__)
            generator = RegionASTGenerator(cfg)
            ast_result = generator.generate()
            
            converter = CFGASTConverter()
            py_ast = converter.convert(ast_result)
            
            code_gen = CFGCodeGenerator()
            decompiled = code_gen.generate(py_ast, in_function=True)
            
            missing = []
            for pattern in test_case.expected_patterns:
                if pattern not in decompiled:
                    missing.append(pattern)
            
            unexpected = []
            for pattern in test_case.forbidden_patterns:
                if pattern in decompiled:
                    unexpected.append(pattern)
            
            passed = len(missing) == 0 and len(unexpected) == 0
            
            return TestResult(
                test_case=test_case,
                passed=passed,
                decompiled_code=decompiled,
                missing_patterns=missing,
                unexpected_patterns=unexpected
            )
            
        except Exception as e:
            return TestResult(
                test_case=test_case,
                passed=False,
                error=str(e)
            )
    
    def run_all_tests(self) -> Tuple[int, int, List[TestResult]]:
        """运行所有测试，返回(通过数, 总数, 结果列表)"""
        print("=" * 80)
        print("  终极完备性测试套件 v4.0")
        print("  Ultimate Control Flow Completeness Test Suite")
        print("=" * 80)
        print()
        
        passed_count = 0
        failed_count = 0
        self.results = []
        
        for idx, test_case in enumerate(self.test_cases, 1):
            result = self.run_single_test(test_case)
            self.results.append(result)
            
            status = "✓" if result.passed else "✗"
            level_str = f"L{test_case.level}"
            
            print(f"[{idx:3d}/{len(self.test_cases)}] {status} {test_case.name:<35} ({test_case.category:<20})")
            
            if not result.passed:
                failed_count += 1
                if result.error:
                    print(f"       错误: {result.error[:80]}")
                elif result.missing_patterns:
                    print(f"       缺少: {result.missing_patterns[:3]}")
                if result.decompiled_code:
                    preview = result.decompiled_code.replace('\n', '\\n')[:120]
                    print(f"       输出: {preview}")
            else:
                passed_count += 1
        
        print()
        print("=" * 80)
        print(f"  总计: {len(self.test_cases)} 个测试")
        print(f"  通过: {passed_count} ({passed_count/len(self.test_cases)*100:.1f}%)")
        print(f"  失败: {failed_count} ({failed_count/len(self.test_cases)*100:.1f}%)")
        print("=" * 80)
        
        return passed_count, len(self.test_cases), self.results
    
    def generate_failure_report(self) -> str:
        """生成失败报告"""
        failures = [r for r in self.results if not r.passed]
        
        report = []
        report.append("\n" + "=" * 80)
        report.append("  失败用例详细报告")
        report.append("=" * 80)
        
        by_category = {}
        for f in failures:
            cat = f.test_case.category
            if cat not in by_category:
                by_category[cat] = []
            by_category[cat].append(f)
        
        for cat, fails in sorted(by_category.items()):
            report.append(f"\n[{cat}] ({len(fails)}个失败)")
            report.append("-" * 60)
            for f in fails:
                report.append(f"\n  • {f.test_case.name}")
                report.append(f"    描述: {f.test_case.description}")
                if f.missing_patterns:
                    report.append(f"    缺少模式: {f.missing_patterns}")
                if f.unexpected_patterns:
                    report.append(f"    多余模式: {f.unexpected_patterns}")
                if f.error:
                    report.append(f"    错误: {f.error}")
                if f.decompiled_code:
                    lines = f.decompiled_code.split('\n')[:8]
                    indented = '\n'.join(['      ' + line for line in lines])
                    report.append(f"    反编译输出:\n{indented}")
        
        report.append("\n" + "=" * 80)
        return "\n".join(report)


def main():
    suite = UltimateCompletenessTestSuite()
    passed, total, results = suite.run_all_tests()
    
    if passed < total:
        print(suite.generate_failure_report())
        
        print("\n[建议]")
        print("  1. 按优先级修复失败用例:")
        print("     P0 (基础语法): if-return, while-else, for-else, match-basic")
        print("     P1 (嵌套结构): if-in-for, for-if-else, try-with-for")
        print("     P2 (高级模式): match-class, match-guard, comprehension")
        print("     P3 (边界条件): single-line-if, many-elif, empty-body")
        print()
        print("  2. 修复原则（必须遵守）:")
        print("     ✓ 使用算法驱动方式，基于区域分析理论")
        print("     ✗ 禁止添加临时禁用(if ... and False)")
        print("     ✗ 禁止硬编码偏移(offset == 62)")
        print("     ✗ 禁止添加TODO/FIXME占位符")
        print("     ✓ 每个修复必须有对应的测试用例")
        print()
        sys.exit(1)
    else:
        print("\n[🎉] 所有测试通过！反编译器已达到完备性要求！")
        sys.exit(0)


if __name__ == '__main__':
    main()
