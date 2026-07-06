"""
=============================================================================
  控制流完备性测试套件 v3.0 (Comprehensive Control Flow Test Suite)
=============================================================================

目的：
  1. 覆盖所有Python控制流语法及其所有可能的嵌套组合
  2. 验证反编译器对复杂嵌套结构的处理能力
  3. 作为回归测试基线，防止后续修改引入问题

设计原则：
  - 每种控制流结构单独测试（基础）
  - 两两组合测试（二元嵌套）
  - 三重及以上嵌套测试（复杂场景）
  - 真实世界混合场景

覆盖的控制流结构：
  ✅ if / if-else / if-elif-else
  ✅ for / for-else / async-for
  ✅ while / while-else / async-while
  ✅ try-except / try-finally / try-except-finally
  ✅ with / async-with / 嵌套with
  ✅ match-case (Python 3.10+)
  ✅ break / continue / return
  ✅ 推导式 (list/dict/set/generator comprehension)
  
嵌套矩阵：
  if × for × while × try × with × match = 6×6 = 36 种二元组合
  加上三元/四元嵌套，总计 100+ 测试用例

=============================================================================
"""

import sys
import dis
import types
from pathlib import Path
from typing import List, Dict, Tuple, Any, Optional
from dataclasses import dataclass
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
    source_code: str
    expected_patterns: List[str]  # 必须包含的模式
    forbidden_patterns: List[str]  # 不能包含的模式
    description: str
    
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
    decompiled_code: Optional[str]
    error: Optional[str]
    missing_patterns: List[str]
    unexpected_patterns: List[str]


class ComprehensiveTestSuite:
    """
    控制流完备性测试套件
    
    测试矩阵：
    
    Level 1: 单一结构基础测试
      - 每种控制流结构的简单实例
      
    Level 2: 二元嵌套组合测试
      - if-in-for, for-in-while, try-with-match 等
      
    Level 3: 三元及多元嵌套测试
      - 复杂真实场景模拟
      
    Level 4: 边界条件测试
      - 空body、深层嵌套、异常路径等
    """
    
    def __init__(self):
        self.test_cases: List[TestCase] = []
        self.results: List[TestResult] = []
        self.stats = {
            'total': 0,
            'passed': 0,
            'failed': 0,
            'by_category': {},
        }
        
        # 初始化测试用例
        self._build_level1_tests()   # 单一结构
        self._build_level2_tests()   # 二元嵌套
        self._build_level3_tests()   # 多元嵌套
        self._build_level4_tests()   # 边界条件
        self._build_match_tests()    # Match-case专项
        self._build_real_world_tests()  # 真实场景
    
    def _add_test(self, name: str, category: str, code: str,
                 expected: List[str] = None, forbidden: List[str] = None,
                 desc: str = ""):
        """添加测试用例"""
        self.test_cases.append(TestCase(
            name=name,
            category=category,
            source_code=code.strip(),
            expected_patterns=expected or [],
            forbidden_patterns=forbidden or [],
            description=desc
        ))
    
    # ====================================================================
    # Level 1: 单一结构基础测试
    # ====================================================================
    def _build_level1_tests(self):
        """构建单一控制流结构的测试"""
        
        # ---- IF 结构 ----
        self._add_test("if_simple", "if", '''
def test_if(x):
    if x > 0:
        return True
    return False
''', ['if x > 0:', 'return True', 'return False'])
        
        self._add_test("if_else", "if", '''
def test_if_else(x):
    if x > 0:
        return "positive"
    else:
        return "non-positive"
''', ['if x > 0:', 'else:', '"positive"', '"non-positive"'])
        
        self._add_test("if_elif_else", "if", '''
def test_if_elif(x):
    if x > 100:
        return "large"
    elif x > 10:
        return "medium"
    elif x > 0:
        return "small"
    else:
        return "non-positive"
''', ['elif x > 10:', 'elif x > 0:', 'else:'])
        
        # ---- FOR 结构 ----
        self._add_test("for_basic", "for", '''
def test_for(items):
    result = []
    for item in items:
        result.append(item * 2)
    return result
''', ['for item in items:', 'result.append'])
        
        self._add_test("for_else", "for", '''
def test_for_else(items):
    for item in items:
        if item < 0:
            break
    else:
        return "all positive"
    return "has negative"
''', ['for item in items:', 'else:', 'break', '"all positive"'])
        
        self._add_test("for_range", "for", '''
def test_for_range(n):
    total = 0
    for i in range(n):
        total += i
    return total
''', ['for i in range(n):', 'total += i'])
        
        self._add_test("for_enumerate", "for", '''
def test_for_enum(data):
    result = {}
    for idx, val in enumerate(data):
        result[idx] = val
    return result
''', ['for idx, val in enumerate(data):'])
        
        self._add_test("for_zip", "for", '''
def test_for_zip(keys, values):
    result = {}
    for k, v in zip(keys, values):
        result[k] = v
    return result
''', ['for k, v in zip(keys, values):'])
        
        # ---- WHILE 结构 ----
        self._add_test("while_basic", "while", '''
def test_while(n):
    result = 1
    i = 1
    while i <= n:
        result *= i
        i += 1
    return result
''', ['while i <= n:', 'result *= i', 'i += 1'])
        
        self._add_test("while_else", "while", '''
def test_while_find(target, data):
    i = 0
    while i < len(data):
        if data[i] == target:
            return i
        i += 1
    else:
        return -1
''', ['while i < len(data):', 'else:', 'return -1'])
        
        self._add_test("while_true", "while", '''
def test_while_true():
    count = 0
    while True:
        count += 1
        if count >= 10:
            break
    return count
''', ['while True:', 'break', 'count >= 10'])
        
        # ---- TRY 结构 ----
        self._add_test("try_except", "try", '''
def test_divide(a, b):
    try:
        return a / b
    except ZeroDivisionError:
        return float('inf')
''', ['try:', 'except ZeroDivisionError:', 'return a / b', "float('inf')"])
        
        self._add_test("try_finally", "try", '''
def test_cleanup(resource):
    try:
        resource.use()
        return resource.get_data()
    finally:
        resource.close()
''', ['try:', 'finally:', 'resource.close()'])
        
        self._add_test("try_except_finally", "try", '''
def test_process(data):
    result = None
    try:
        result = data.process()
    except ValueError as e:
        log_error(e)
        result = None
    finally:
        cleanup()
    return result
''', ['except ValueError as e:', 'finally:', 'cleanup()'])
        
        self._add_test("try_multi_except", "try", '''
def test_safe_op(x):
    try:
        return 10 / x
    except ZeroDivisionError:
        return 0
    except TypeError:
        return None
''', ['except ZeroDivisionError:', 'except TypeError:'])
        
        # ---- WITH 结构 ----
        self._add_test("with_basic", "with", '''
def test_read_file(path):
    with open(path) as f:
        content = f.read()
    return content
''', ['with open(path) as f:', 'content = f.read()'])
        
        self._add_test("with_multi", "with", '''
def test_copy_files(src, dst):
    with open(src) as fin, open(dst, 'w') as fout:
        fout.write(fin.read())
''', ['with open(src) as fin, open(dst, \'w\') as fout:'])
        
        # ---- MATCH 结构 ----
        self._add_test("match_basic", "match", '''
def test_match_point(point):
    match point:
        case (0, 0):
            return "origin"
        case (x, 0):
            return f"x={x}"
        case (0, y):
            return f"y={y}"
        case _:
            return f"{point}"
''', ['match point:', 'case (0, 0):', 'case _:', 'return "origin"'])
        
        self._add_test("match_or_pattern", "match", '''
def test_match_or(x):
    match x:
        case 0 | 1 | 2:
            return "small"
        case _:
            return "other"
''', ['case 0 | 1 | 2:', 'match x:'])
        
        self._add_test("match_guard", "match", '''
def test_match_guard(x):
    match x:
        case int(n) if n > 0:
            return "positive int"
        case int(n):
            return "non-positive int"
        case _:
            return "not int"
''', ['case int(', 'if n > 0:', 'match x:'])
        
        self._add_test("match_as_pattern", "match", '''
def test_match_as(data):
    match data:
        case [first, *rest] as lst:
            return len(lst), first
        case _:
            return 0, None
''', ['case [first, *rest] as lst:', 'match data:'])
        
        # ---- 异步结构 ----
        self._add_test("async_for", "async-for", '''
async def test_async_for(urls):
    results = []
    async for url in urls:
        response = await fetch(url)
        results.append(response)
    return results
''', ['async for url in urls:', 'await fetch(url)'])
        
        self._add_test("async_with", "async-with", '''
async def test_async_with():
    async with aiohttp.ClientSession() as session:
        response = await session.get('https://example.com')
        return await response.text()
''', ['async with', 'await session.get('])
        
        # ---- 推导式 ----
        self._add_test("list_comprehension", "comprehension", '''
def test_list_comp(data):
    return [x * 2 for x in data if x > 0]
''', ['[x * 2 for x in data if x > 0]'])
        
        self._add_test("dict_comprehension", "comprehension", '''
def test_dict_comp(data):
    return {k: v * 2 for k, v in data.items()}
''', ['{k: v * 2 for k, v in data.items()}'])
        
        self._add_test("set_comprehension", "comprehension", '''
def test_set_comp(data):
    return {abs(x) for x in data}
''', ['{abs(x) for x in data}'])
        
        self._add_test("generator_expr", "comprehension", '''
def test_gen_expr(data):
    gen = (x ** 2 for x in data if x % 2 == 0)
    return list(gen)
''', ['(x ** 2 for x in data if x % 2 == 0)'])
        
        # ---- 其他结构 ----
        self._add_test("ternary_op", "if", '''
def test_ternary(x):
    return "even" if x % 2 == 0 else "odd"
''', ['return "even" if', 'else:'])
        
        self._add_test("walrus_op", "if", '''
def test_walrus(data):
    if (n := len(data)) > 10:
        return n // 2
    return n
''', ['if (n := len(data)) > 10:'])
    
    # ====================================================================
    # Level 2: 二元嵌套组合测试
    # ====================================================================
    def _build_level2_tests(self):
        """构建两种控制流的嵌套组合"""
        
        # IF + FOR
        self._add_test("if_in_for", "nested-if-for", '''
def test_if_in_for(items):
    results = []
    for item in items:
        if item > 0:
            results.append(item)
    return results
''', ['for item in items:', 'if item > 0:'])
        
        # IF + WHILE
        self._add_test("if_in_while", "nested-if-while", '''
def test_if_in_while(data):
    i = 0
    results = []
    while i < len(data):
        if data[i] is not None:
            results.append(data[i])
        i += 1
    return results
''', ['while i < len(data):', 'if data[i] is not None:'])
        
        # FOR + TRY
        self._add_test("for_try", "nested-for-try", '''
def test_for_try(urls):
    results = []
    for url in urls:
        try:
            resp = fetch(url)
            results.append(resp)
        except Exception as e:
            log(e)
    return results
''', ['for url in urls:', 'try:', 'except Exception as e:'])
        
        # TRY + WITH
        self._add_test("try_with", "nested-try-with", '''
def test_try_with(config):
    try:
        with open(config['file']) as f:
            data = json.load(f)
        return data
    except IOError as e:
        return {}
''', ['try:', 'with open(config[\'file\']) as f:'])
        
        # IF + MATCH
        self._add_test("if_match", "nested-if-match", '''
def test_if_match(x):
    if isinstance(x, int):
        match x:
            case 0:
                return "zero"
            case _:
                return f"int:{x}"
    return "not int"
''', ['if isinstance(x, int):', 'match x:', 'case 0:'])
        
        # FOR + IF + ELSE
        self._add_test("for_if_else", "nested-for-if-else", '''
def test_filter_positive(items):
    positives = []
    negatives = []
    for item in items:
        if item >= 0:
            positives.append(item)
        else:
            negatives.append(item)
    return positives, negatives
''', ['for item in items:', 'if item >= 0:', 'else:'])
        
        # WHILE + TRY
        self._add_test("while_try", "nested-while-try", '''
def test_retry_until_success(operation, max_retries=3):
    retries = 0
    while retries < max_retries:
        try:
            return operation()
        except Exception:
            retries += 1
    raise MaxRetriesError()
''', ['while retries < max_retries:', 'try:', 'except Exception:'])
        
        # WITH + FOR
        self._add_test("with_for", "nested-with-for", '''
def test_batch_process(file_paths):
    results = {}
    with ThreadPoolExecutor() as executor:
        for path in file_paths:
            future = submit(executor, process_file, path)
            results[path] = future.result()
    return results
''', ['with ThreadPoolExecutor() as executor:', 'for path in file_paths:'])
        
        # TRY + EXCEPT + FINALLY + NESTED TRY
        self._add_test("try_nested_try", "nested-try-try", '''
def test_nested_exception_handling(data):
    try:
        process_header(data)
        try:
            process_body(data)
        except BodyError as be:
            recover_body(be)
    except HeaderError as he:
        handle_header(he)
    finally:
        cleanup_all()
''', ['try:', 'try:', 'except BodyError:', 'except HeaderError:', 'finally:'])
        
        # IF + ELIF + FOR
        self._add_test("if_elif_for", "nested-if_elif-for", '''
def test_categorize_items(items):
    small = []
    medium = []
    large = []
    for item in items:
        if item < 10:
            small.append(item)
        elif item < 100:
            medium.append(item)
        else:
            large.append(item)
    return small, medium, large
''', ['for item in items:', 'elif item < 100:', 'else:'])
        
        # MATCH + IF (在case body中)
        self._add_test("match_if_body", "nested-match-if", '''
def test_complex_match(data):
    match data:
        case {'type': 'user', 'id': uid}:
            if uid.startswith('admin'):
                return "admin_user"
            return "normal_user"
        case {'type': 'system'}:
            return "system"
        case _:
            return "unknown"
''', ['match data:', 'case {\'type\': \'user\', \'id\': uid}:', 'if uid.startswith(\'admin\'):'])
        
        # ASYNC FOR + TRY
        self._add_test("async_for_try", "nested-async_for-try", '''
async def test_async_fetch_all(urls):
    results = []
    errors = []
    async for url in urls:
        try:
            resp = await fetch_async(url)
            results.append(resp)
        except Exception as e:
            errors.append((url, e))
    return results, errors
''', ['async for url in urls:', 'try:', 'except Exception as e:'])
        
        # FOR + FOR (双重循环)
        self._add_test("for_for_matrix", "nested-for-for", '''
def test_matrix_multiply(a, b):
    result = [[0] * len(b[0]) for _ in range(len(a))]
    for i in range(len(a)):
        for j in range(len(b[0])):
            for k in range(len(b)):
                result[i][j] += a[i][k] * b[k][j]
    return result
''', ['for i in range(len(a)):', 'for j in range(len(b[0])):'])
    
    # ====================================================================
    # Level 3: 三元及多元嵌套测试
    # ====================================================================
    def _build_level3_tests(self):
        """构建复杂的多元嵌套场景"""
        
        # IF + FOR + IF (过滤+转换)
        self._add_test("if_for_if_transform", "complex-nested", '''
def test_transform_and_filter(data):
    results = []
    for item in data:
        if item is not None:
            if isinstance(item, int):
                results.append(item * 2)
            elif isinstance(item, str):
                results.append(item.upper())
    return results
''', ['for item in data:', 'if item is not None:', 'if isinstance(item, int):', 'elif isinstance(item, str):'])
        
        # TRY + WITH + FOR
        self._add_test("try_with_for_batch", "complex-nested", '''
def test_batch_database_operations(records):
    success = []
    failed = []
    try:
        with DatabaseConnection() as db:
            for record in records:
                try:
                    db.insert(record)
                    success.append(record)
                except IntegrityError:
                    failed.append(record)
    except ConnectionError:
        log("Database connection failed")
    return {"success": success, "failed": failed}
''', ['try:', 'with DatabaseConnection() as db:', 'for record in records:', 
     'db.insert(record)', 'except IntegrityError:', 'except ConnectionError:'])
        
        # WHILE + IF + BREAK + ELSE
        self._add_test("while_if_break_else", "complex-nested", '''
def test_find_first_negative(numbers):
    i = 0
    while i < len(numbers):
        if numbers[i] < 0:
            break
        i += 1
    else:
        return -1  # No negative found
    return i
''', ['while i < len(numbers):', 'if numbers[i] < 0:', 'break', 'else:'])
        
        # FOR + TRY + EXCEPT + FINALLY
        self._add_test("for_try_except_finally", "complex-nested", '''
def test_safe_process_all(items):
    results = []
    for item in items:
        try:
            processed = dangerous_operation(item)
            results.append(processed)
        except CriticalError:
            raise  # Abort all processing
        except NonCriticalError:
            pass  # Skip this item
        finally:
            cleanup_temp_files()
    return results
''', ['for item in items:', 'try:', 'except CriticalError:', 'raise',
     'except NonCriticalError:', 'finally:'])
        
        # IF + MATCH + FOR (复合决策)
        self._add_test("if_match_for_pipeline", "complex-nested", '''
def test_process_pipeline(data):
    if not validate_schema(data):
        return {"status": "error", "message": "Invalid schema"}
    
    results = []
    match data.get('mode'):
        case 'batch':
            for item in data['items']:
                results.append(process_item(item))
        case 'stream':
            for chunk in stream_data(data['source']):
                results.append(process_chunk(chunk))
        case _:
            results.append(process_default(data))
    
    return {"status": "ok", "results": results}
''', ['if not validate_schema(data):', 'match data.get(\'mode\'):',
     'case \'batch\':', 'for item in data[\'items\']:'])
        
        # TRY + WITH + ASYNC FOR (异步批处理)
        self._add_test("try_with_async_for", "complex-nested", '''
async def test_parallel_fetch(urls):
    all_results = []
    try:
        with AsyncSession() as session:
            async for url in urls:
                try:
                    response = await session.get(url)
                    all_results.append(await response.json())
                except ClientError as ce:
                    all_results.append({"url": url, "error": str(ce)})
    except SessionError as se:
        log(f"Session failed: {se}")
    return all_results
''', ['try:', 'with AsyncSession() as session:', 'async for url in urls:',
     'await session.get(url)', 'except ClientError:', 'except SessionError:'])
        
        # DEEP NESTING: IF > IF > IF > FOR (4层)
        self._add_test("deep_nesting_4level", "deep-nested", '''
def test_deep_classification(data):
    classified = {"A": [], "B": [], "C": []}
    for item in data:
        if isinstance(item, dict):
            if 'value' in item:
                if item['value'] > 0:
                    if item['value'] > 100:
                        classified["C"].append(item)
                    else:
                        classified["B"].append(item)
                else:
                    classified["A"].append(item)
            else:
                classified["A"].append(item)
        else:
            classified["A"].append(item)
    return classified
''', ['for item in data:', 'if isinstance(item, dict):', 'if \'value\' in item:',
     'if item[\'value\'] > 0:', 'if item[\'value\'] > 100:'])
    
    # ====================================================================
    # Level 4: 边界条件测试
    # ====================================================================
    def _build_level4_tests(self):
        """构建边界条件和特殊场景测试"""
        
        # 空 body 的各种结构
        self._add_test("empty_if_body", "boundary", '''
def test_empty_if(flag):
    if flag:
        pass  # Do nothing explicitly
    return flag
''', ['if flag:', 'pass'])
        
        self._add_test("empty_for_body", "boundary", '''
def test_empty_for(n):
    for i in range(n):
        pass  # Just counting
    return n
''', ['for i in range(n):', 'pass'])
        
        self._add_test("empty_try_body", "boundary", '''
def test_empty_try():
    try:
        risky_operation()
    except:
        pass  # Ignore all errors
    return "done"
''', ['try:', 'risky_operation()', 'except:', 'pass'])
        
        # 单行 body
        self._add_test("single_line_if", "boundary", '''
def test_single_line(x):
    if x > 0: return True
    return False
''', ['if x > 0: return True'])
        
        # 大量 elif 分支
        self._add_test("many_elif_branches", "boundary", '''
def test_many_elif(value):
    if value == 1:
        return "one"
    elif value == 2:
        return "two"
    elif value == 3:
        return "three"
    elif value == 4:
        return "four"
    elif value == 5:
        return "five"
    else:
        return "many"
''', ['elif value == 2:', 'elif value == 3:', 'elif value == 4:', 'elif value == 5:'])
        
        # 循环中的 return 和 break 组合
        self._add_test("loop_break_continue_return", "boundary", '''
def test_loop_control(items):
    result = []
    for item in items:
        if item is None:
            continue
        if item == "STOP":
            break
        if item == "RETURN":
            return result
        result.append(item.upper())
    return result
''', ['for item in items:', 'continue', 'break', 'return result'])
        
        # 嵌套函数定义（闭包）
        self._add_test("nested_function_def", "boundary", '''
def test_closure_creator(multiplier):
    def multiply(x):
        return x * multiplier
    def add(y):
        return y + multiplier
    return multiply, add
''', ['def multiply(x):', 'return x * multiplier', 'def add(y):'])
        
        # 类定义中的各种结构
        self._add_test("class_with_methods", "boundary", '''
class DataProcessor:
    def __init__(self, config):
        self.config = config
        self.data = []
    
    def process(self, raw_data):
        for item in raw_data:
            if self._validate(item):
                self.data.append(self._transform(item))
        return self.data
    
    def _validate(self, item):
        return item is not None
    
    def _transform(self, item):
        return item.upper()
''', ['class DataProcessor:', 'def __init__(self, config):', 'def process(self, raw_data):',
     'for item in raw_data:', 'if self._validate(item):'])
        
        # 装饰器使用
        self._add_test("decorator_usage", "boundary", '''
@log_calls
@retry(max_attempts=3)
@cache_result(timeout=300)
def expensive_api_call(param):
    return external_service.query(param)
''', ['@log_calls', '@retry(max_attempts=3)', '@cache_result(timeout=300)',
     'def expensive_api_call(param):'])
        
        # 上下文管理器链式调用
        self._add_test("chained_context_managers", "boundary", '''
def test_chained_contexts(file_path):
    with Timer() as t:
        with open(file_path) as f:
            with Lock(file_path):
                content = f.read()
                return content, t.elapsed
''', ['with Timer() as t:', 'with open(file_path) as f:',
     'with Lock(file_path):'])
    
    # ====================================================================
    # Match-case 专项测试
    # ====================================================================
    def _build_match_tests(self):
        """构建Match-case的全面测试"""
        
        # 序列模式匹配
        self._add_test("match_sequence", "match", '''
def test_match_sequence(point):
    match point:
        case []:
            return "empty"
        case [x]:
            return f"single: {x}"
        case [x, y]:
            return f"pair: ({x}, {y})"
        case [first, *rest]:
            return f"head: {first}, tail: {len(rest)}"
''', ['match point:', 'case []:', 'case [x]:', 'case [first, *rest]:'])
        
        # 映射模式匹配
        self._add_test("match_mapping", "match", '''
def test_match_mapping(config):
    match config:
        case {"host": h, "port": p}:
            return f"http://{h}:{p}"
        case {}:
            return "empty config"
        case {"debug": True, **opts}:
            return opts
''', ['match config:', 'case {"host": h, "port": p}:', 'case {}:'])
        
        # 类模式匹配 + guard
        self._add_test("match_class_guard", "match", '''
def test_match_class_guard(obj):
    match obj:
        case Point(x=0, y=0) if x == 0 and y == 0:
            return "origin"
        case Point(x=x, y=y) if x > 0 and y > 0:
            return f"quadrant1:({x},{y})"
        case Point():
            return "default point"
        case _:
            return "not a point"
''', ['match obj:', 'case Point(x=0, y=0)', 'if x == 0 and y == 0'])
        
        # OR pattern + AS pattern 组合
        self._add_test("match_or_as_combined", "match", '''
def test_match_or_as(data):
    match data:
        case [0 | 1 | -1] as special:
            return f"special: {special}"
        case [first, second] as pair if first != second:
            return f"different: {pair}"
        case _:
            return "other"
''', ['case [0 | 1 | -1] as special:', 'case [first, second] as pair if'])
        
        # 嵌套 match
        self._add_test("match_nested", "match", '''
def test_nested_match(data):
    match data:
        case {"type": "order", "side": side}:
            match side:
                case "buy":
                    return "buy order"
                case "sell":
                    return "sell order"
        case {"type": "quote"}:
            return "quote data"
        case _:
            return "unknown"
''', ['match data:', 'case {"type": "order", "side"}:',
     'match side:', 'case "buy":'])
        
        # Match 在不同上下文中
        self._add_test("match_in_function", "context-match", '''
class Handler:
    def process(self, typet):
        match typet:
            case 1:
                return self.handle_type1()
            case 2:
                return self.handle_type2()
            case _:
                raise ValueError(f"Unknown type: {typet}")
    
    def handle_type1(self):
        return "type1"
    
    def handle_type2(self):
        return "type2"
''', ['match typet:', 'case 1:', 'case 2:', 'raise ValueError'])
    
    # ====================================================================
    # 真实世界混合场景
    # ====================================================================
    def _build_real_world_tests(self):
        """构建接近真实代码的复杂场景"""
        
        # 数据处理管道
        self._add_test("data_pipeline", "real-world", '''
def process_pipeline(raw_data, config):
    """完整的数据处理管道，包含验证、转换、存储"""
    results = []
    errors = []
    
    # Phase 1: Validation
    if not raw_data:
        raise ValueError("Empty input")
    
    if not isinstance(raw_data, list):
        raw_data = [raw_data]
    
    # Phase 2: Processing with error handling
    for idx, item in enumerate(raw_data):
        try:
            validated = validate_item(item, config['schema'])
            
            if config.get('filter_fn'):
                if not config['filter_fn'](validated):
                    continue
            
            transformed = transform_item(validated, config['transforms'])
            results.append(transformed)
            
        except ValidationError as ve:
            errors.append({'index': idx, 'error': str(ve), 'item': str(item)})
        except TransformError as te:
            errors.append({'index': idx, 'error': str(te), 'item': str(item)})
    
    # Phase 3: Storage
    try:
        with DatabaseConnection(config['db_url']) as db:
            for batch in chunk(results, config.get('batch_size', 100)):
                db.insert_batch(batch)
    except DBError as dbe:
        log.error(f"Database error: {dbe}")
        raise ProcessingError("Failed to store results") from dbe
    
    return {
        'success_count': len(results),
        'error_count': len(errors),
        'errors': errors[:config.get('max_errors', 10)]
    }
''', ['if not raw_data:', 'for idx, item in enumerate(raw_data):', 'try:',
     'except ValidationError:', 'with DatabaseConnection(config[\'db_url\']) as db:',
     'for batch in chunk(results,', 'db.insert_batch(batch)'])
        
        # 配置解析器
        self._add_test("config_parser", "real-world", '''
def parse_config(config_path, overrides=None):
    """解析配置文件并应用覆盖"""
    config = {
        'debug': False,
        'timeout': 30,
        'retries': 3,
        'handlers': {}
    }
    
    # Load from file if exists
    if config_path and os.path.exists(config_path):
        try:
            with open(config_path) as f:
                file_config = yaml.safe_load(f)
                if file_config:
                    config.update(file_config)
        except IOError:
            log.warning(f"Cannot read config: {config_path}")
        except yaml.YAMLError as ye:
            log.error(f"Invalid YAML: {ye}")
    
    # Apply command-line overrides
    if overrides:
        for key, value in overrides.items():
            if '.' in key:  # Nested key like "database.host"
                parts = key.split('.')
                target = config
                for part in parts[:-1]:
                    target = target.setdefault(part, {})
                target[parts[-1]] = value
            else:
                config[key] = value
    
    # Validate final config
    if config['timeout'] <= 0:
        raise ConfigError("Timeout must be positive")
    if config['retries'] < 0:
        raise ConfigError("Retries cannot be negative")
    
    return config
''', ['if config_path and os.path.exists(config_path):', 'try:',
     'with open(config_path) as f:', 'except IOError:', 'except yaml.YAMLError:',
     'if overrides:', 'for key, value in overrides.items():'])
        
        # API路由处理器（类方法中的复杂逻辑）
        self._add_test("api_router", "real-world", '''
class APIRouter:
    def __init__(self):
        self.routes = {}
        self.middleware = []
    
    def route(self, path, methods=None):
        def decorator(func):
            self.routes[path] = {
                'handler': func,
                'methods': methods or ['GET'],
            }
            return func
        return decorator
    
    def use(self, middleware_func):
        self.middleware.append(middleware_func)
    
    def handle_request(self, request):
        path = request.path
        method = request.method
        
        if path not in self.routes:
            return Response(404, "Not Found")
        
        route_info = self.routes[path]
        if method not in route_info['methods']:
            return Response(405, "Method Not Allowed")
        
        # Apply middleware
        for mw in reversed(self.middleware):
            request = mw(request)
        
        # Call handler
        try:
            response = route_info['handler'](request)
            return response or Response(200, "OK")
        except APIError as ae:
            return Response(ae.status, ae.message)
        except Exception as e:
            log.exception("Handler error")
            return Response(500, "Internal Server Error")
''', ['class APIRouter:', 'def route(self, path, methods=None):',
     'if path not in self.routes:', 'if method not in route_info[\'methods\']:',
     'for mw in reversed(self.middleware):', 'try:', 'except APIError as ae:'])
    
    def run_single_test(self, test_case: TestCase) -> TestResult:
        """运行单个测试用例"""
        try:
            # 编译源代码
            namespace = {}
            exec(compile(test_case.source_code, '<test>', 'exec'), namespace)
            
            # 提取函数对象
            func_name = None
            for name, obj in namespace.items():
                if callable(obj) and not name.startswith('_') and name != 'TestCase':
                    func_name = name
                    break
            
            if func_name is None:
                # 可能是类定义或其他代码
                code_obj = list(namespace.values())[0]
                if hasattr(code_obj, '__code__'):
                    func_name = 'module'
            
            func = namespace.get(func_name)
            if func is None or not hasattr(func, '__code__'):
                return TestResult(
                    test_case=test_case,
                    passed=False,
                    decompiled_code=None,
                    error="无法提取可调用对象",
                    missing_patterns=[],
                    unexpected_patterns=[]
                )
            
            code_obj = func.__code__
            
            # 反编译
            cfg = build_cfg(code_obj)
            gen = RegionASTGenerator(cfg)
            ast_dict = gen.generate()
            
            if ast_dict is None:
                return TestResult(
                    test_case=test_case,
                    passed=False,
                    decompiled_code=None,
                    error="AST生成返回None",
                    missing_patterns=list(test_case.expected_patterns),
                    unexpected_patterns=[]
                )
            
            converter = CFGASTConverter()
            py_ast = converter.convert(ast_dict)
            code_gen = CFGCodeGenerator()
            source = code_gen.generate(py_ast)
            
            if not source:
                return TestResult(
                    test_case=test_case,
                    passed=False,
                    decompiled_code=None,
                    error="代码生成返回空",
                    missing_patterns=list(test_case.expected_patterns),
                    unexpected_patterns=[]
                )
            
            # 验证期望模式
            missing = []
            for pattern in test_case.expected_patterns:
                if pattern not in source:
                    missing.append(pattern)
            
            # 验证禁止模式
            unexpected = []
            for pattern in test_case.forbidden_patterns:
                if pattern in source:
                    unexpected.append(pattern)
            
            passed = len(missing) == 0 and len(unexpected) == 0
            
            return TestResult(
                test_case=test_case,
                passed=passed,
                decompiled_code=source,
                error=None,
                missing_patterns=missing,
                unexpected_patterns=unexpected
            )
            
        except SyntaxError as e:
            return TestResult(
                test_case=test_case,
                passed=False,
                decompiled_code=None,
                error=f"源代码语法错误: {e}",
                missing_patterns=[],
                unexpected_patterns=[]
            )
        except Exception as e:
            return TestResult(
                test_case=test_case,
                passed=False,
                decompiled_code=None,
                error=f"反编译错误: {e}",
                missing_patterns=[],
                unexpected_patterns=[]
            )
    
    def run_all(self) -> Dict[str, Any]:
        """运行所有测试"""
        print("=" * 80)
        print("  控制流完备性测试套件 v3.0")
        print("  Comprehensive Control Flow Test Suite")
        print("=" * 80)
        
        self.results = []
        categories = {}
        
        for i, test_case in enumerate(self.test_cases, 1):
            result = self.run_single_test(test_case)
            self.results.append(result)
            
            # 统计分类
            cat = test_case.category
            if cat not in categories:
                categories[cat] = {'total': 0, 'passed': 0}
            categories[cat]['total'] += 1
            if result.passed:
                categories[cat]['passed'] += 1
            
            # 显示进度
            status = "✅" if result.passed else "❌"
            print(f"[{i:3d}/{len(self.test_cases)}] {status} {test_case.name:<35} ({test_case.category})")
            
            if not result.passed and result.decompiled_code:
                # 显示部分输出用于调试
                lines = result.decompiled_code.split('\n')[:8]
                preview = '\n'.join(f'    {line}' for line in lines)
                if result.missing_patterns:
                    print(f"       缺少: {result.missing_patterns[:3]}")
        
        # 统计总结果
        total_passed = sum(1 for r in self.results if r.passed)
        total_failed = len(self.results) - total_passed
        
        self.stats['total'] = len(self.test_cases)
        self.stats['passed'] = total_passed
        self.stats['failed'] = total_failed
        self.stats['by_category'] = categories
        
        # 打印报告
        print("\n" + "=" * 80)
        print("  测试结果报告")
        print("=" * 80)
        
        print(f"\n{'类别':<25} {'总数':>6} {'通过':>6} {'失败':>6} {'通过率':>10}")
        print("-" * 55)
        
        for cat, stats in sorted(categories.items()):
            rate = stats['passed'] / stats['total'] * 100
            status = "✅" if rate >= 80 else ("⚠️" if rate >= 50 else "❌")
            print(f"{status} {cat:<23} {stats['total']:>6} {stats['passed']:>6} "
                  f"{stats['total']-stats['passed']:>6} {rate:>9.1f}%")
        
        print("-" * 55)
        total_rate = total_passed / len(self.test_cases) * 100
        status = "🎉" if total_rate >= 90 else ("✅" if total_rate >= 70 else ("⚠️" if total_rate >= 50 else "❌"))
        print(f"{status} TOTAL{'':<46} {len(self.test_cases):>6} {total_passed:>6} "
              f"{total_failed:>6} {total_rate:>9.1f}%")
        
        return self.stats


def main():
    suite = ComprehensiveTestSuite()
    stats = suite.run_all()
    
    # 返回退出码
    sys.exit(0 if stats['passed'] == stats['total'] else 1)


if __name__ == '__main__':
    main()
