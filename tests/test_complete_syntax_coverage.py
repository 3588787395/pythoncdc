#!/usr/bin/env python3
"""
完整语法覆盖测试 - 80个二元组合控制流语法测试用例

覆盖11种基础语法的有效两两组合：
if/elif/else/for/while/try/except/finally/with/match/case

分类：
- Category A: 条件×循环 (12个) A01-A12
- Category B: 循环×异常 (10个) B01-B10
- Category C: 异常×条件 (8个) C01-C08
- Category D: with相关 (10个) D01-D10
- Category E: match/case相关 (8个, 3.10+) E01-E08
- Category F: 同类型嵌套 (12个) F01-F12
- Category G: 复杂控制流混合 (20个) G01-G20
"""

import ast
import sys
import os
import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

try:
    from tests.test_functional_verification import DecompilationVerifier, create_test_verifier
    VERIFIER_AVAILABLE = True
except ImportError:
    VERIFIER_AVAILABLE = False


class TestCompleteSyntaxCoverage:
    """完整语法覆盖测试类 - 80个二元组合控制流语法测试用例"""

    @pytest.fixture(autouse=True)
    def setup_verifier(self):
        """设置验证器"""
        if VERIFIER_AVAILABLE:
            self.verifier = create_test_verifier()
        else:
            self.verifier = None

    def _verify_source(self, source_code: str):
        """验证源代码的编译和反编译"""
        try:
            ast.parse(source_code)
        except SyntaxError as e:
            pytest.fail(f"源代码语法错误: {e}\n\n源码:\n{source_code}")

        compile(source_code, '<test>', 'exec')

        if self.verifier:
            report = self.verifier.verify_decompile(source_code)
            assert report.syntax_valid, f"反编译结果语法无效: {report.errors}"

    # ============================================================
    # Category A: 条件×循环 (12个) A01-A12
    # ============================================================

    def test_A01_if_for(self):
        """A01: if>for - 条件语句包含for循环"""
        source = '''def target():
    x = 10
    if x > 0:
        for i in range(x):
            y = i * 2
    return y if 'y' in dir() else 0
'''
        self._verify_source(source)

    def test_A02_if_while(self):
        """A02: if>while - 条件语句包含while循环"""
        source = '''def target():
    x = 10
    if x > 0:
        while x > 0:
            x -= 1
            y = x
    return y if 'y' in dir() else 0
'''
        self._verify_source(source)

    def test_A03_for_if(self):
        """A03: for>if - for循环包含条件语句"""
        source = '''def target():
    result = []
    for i in range(10):
        if i % 2 == 0:
            result.append(i)
    return result
'''
        self._verify_source(source)

    def test_A04_while_if(self):
        """A04: while>if - while循环包含条件语句"""
        source = '''def target():
    result = []
    x = 10
    while x > 0:
        if x % 2 == 0:
            result.append(x)
        x -= 1
    return result
'''
        self._verify_source(source)

    def test_A05_elif_for(self):
        """A05: elif>for - elif分支包含for循环"""
        source = '''def target():
    x = 5
    if x < 3:
        y = 1
    elif x < 10:
        for i in range(x):
            y = i + 1
    else:
        y = 100
    return y
'''
        self._verify_source(source)

    def test_A06_else_for(self):
        """A06: else>for - else分支包含for循环"""
        source = '''def target():
    x = 0
    if x > 0:
        y = x
    else:
        for i in range(5):
            y = i * 10
    return y
'''
        self._verify_source(source)

    def test_A07_for_elif(self):
        """A07: for>elif - for循环内包含if-elif结构"""
        source = '''def target():
    result = []
    for i in range(20):
        if i < 5:
            result.append('small')
        elif i < 15:
            result.append('medium')
        else:
            result.append('large')
    return result
'''
        self._verify_source(source)

    def test_A08_while_else(self):
        """A08: while>else - while循环内包含if-else结构"""
        source = '''def target():
    x = 10
    while x > 0:
        if x % 3 == 0:
            result = x
        else:
            result = x * 2
        x -= 1
    return result
'''
        self._verify_source(source)

    def test_A09_if_for_else(self):
        """A09: if>for+else - 条件语句包含带else的for循环"""
        source = '''def target():
    x = 5
    if x > 0:
        found = False
        for i in range(x):
            if i == 3:
                found = True
                break
        else:
            found = False
    return found if 'found' in dir() else None
'''
        self._verify_source(source)

    def test_A10_for_if_elif_else(self):
        """A10: for>if-elif-else - for循环内包含完整if-elif-else链"""
        source = '''def target():
    results = {'a': 0, 'b': 0, 'c': 0}
    for i in range(30):
        if i % 3 == 0:
            results['a'] += 1
        elif i % 3 == 1:
            results['b'] += 1
        else:
            results['c'] += 1
    return results
'''
        self._verify_source(source)

    def test_A11_nested_if_for(self):
        """A11: nested_if>for - 嵌套if语句包含for循环"""
        source = '''def target():
    x = 10
    if x > 0:
        if x < 20:
            total = 0
            for i in range(x):
                total += i
        else:
            total = -1
    else:
        total = 0
    return total
'''
        self._verify_source(source)

    def test_A12_nested_for_if(self):
        """A12: nested_for>if - 嵌套for循环包含if语句"""
        source = '''def target():
    matrix = [[1, 2], [3, 4]]
    result = 0
    for row in matrix:
        for item in row:
            if item > 2:
                result += item
    return result
'''
        self._verify_source(source)

    # ============================================================
    # Category B: 循环×异常 (10个) B01-B10
    # ============================================================

    def test_B01_try_for(self):
        """B01: try>for - try块内包含for循环"""
        source = '''def target():
    items = [1, 2, 3, 'error', 4]
    result = []
    try:
        for item in items:
            result.append(item * 2)
    except TypeError:
        result = ['error']
    return result
'''
        self._verify_source(source)

    def test_B02_for_try(self):
        """B02: for>try - for循环内包含try-except"""
        source = '''def target():
    data = [1, 0, 2, 0, 3]
    results = []
    for val in data:
        try:
            results.append(10 / val)
        except ZeroDivisionError:
            results.append(float('inf'))
    return results
'''
        self._verify_source(source)

    def test_B03_except_for(self):
        """B03: except>for - except块内包含for循环"""
        source = '''def target():
    try:
        x = int('invalid')
    except ValueError:
        recovery = []
        for i in range(5):
            recovery.append(i * 10)
        return recovery
'''
        self._verify_source(source)

    def test_B04_finally_for(self):
        """B04: finally>for - finally块内包含for循环"""
        source = '''def target():
    cleanup_list = []
    try:
        x = 1 / 0
    except ZeroDivisionError:
        pass
    finally:
        for i in range(3):
            cleanup_list.append(f'cleaned_{i}')
    return cleanup_list
'''
        self._verify_source(source)

    def test_B05_try_while(self):
        """B05: try>while - try块内包含while循环"""
        source = '''def target():
    count = 5
    result = []
    try:
        while count > 0:
            result.append(count)
            count -= 1
            if count == 2:
                raise RuntimeError('stop')
    except RuntimeError:
        result.append('stopped')
    return result
'''
        self._verify_source(source)

    def test_B06_while_try(self):
        """B06: while>try - while循环内包含try-except"""
        source = '''def target():
    data = ['1', 'two', '3', 'four', '5']
    numbers = []
    i = 0
    while i < len(data):
        try:
            numbers.append(int(data[i]))
        except ValueError:
            numbers.append(-1)
        i += 1
    return numbers
'''
        self._verify_source(source)

    def test_B07_for_try_except_finally(self):
        """B07: for>try-except-finally - for循环内包含完整异常处理"""
        source = '''def target():
    values = [1, 0, 2]
    results = []
    cleaned = []
    for v in values:
        try:
            results.append(100 / v)
        except ZeroDivisionError:
            results.append(None)
        finally:
            cleaned.append(f'processed_{v}')
    return results, cleaned
'''
        self._verify_source(source)

    def test_B08_try_for_else(self):
        """B08: try>for-else - try块内包含带else的for循环"""
        source = '''def target():
    found = None
    try:
        data = [1, 3, 5, 7]
        for item in data:
            if item % 2 == 0:
                found = item
                break
        else:
            found = -1
    except Exception:
        found = 'error'
    return found
'''
        self._verify_source(source)

    def test_B09_nested_try_for(self):
        """B09: nested_try>for - 嵌套try块内包含for循环"""
        source = '''def target():
    result = []
    try:
        try:
            for i in range(5):
                result.append(i)
        except IndexError:
            result.append('inner_error')
    except Exception:
        result.append('outer_error')
    return result
'''
        self._verify_source(source)

    def test_B10_nested_for_try(self):
        """B10: nested_for>try - 嵌套for循环内包含try-except"""
        source = '''def target():
    matrix = [[1, 2], [0, 4], [5, 6]]
    results = []
    for row in matrix:
        row_result = []
        for val in row:
            try:
                row_result.append(10 / val)
            except ZeroDivisionError:
                row_result.append(None)
        results.append(row_result)
    return results
'''
        self._verify_source(source)

    # ============================================================
    # Category C: 异常×条件 (8个) C01-C08
    # ============================================================

    def test_C01_try_if(self):
        """C01: try>if - try块内包含if语句"""
        source = '''def target():
    value = 42
    result = 0
    try:
        if value > 30:
            result = value * 2
        elif value > 20:
            result = value
        else:
            result = value // 2
    except Exception:
        result = -1
    return result
'''
        self._verify_source(source)

    def test_C02_if_try(self):
        """C02: if>try - if语句内包含try-except"""
        source = '''def target():
    x = 10
    if x > 0:
        try:
            result = 100 / x
        except ZeroDivisionError:
            result = 0
    else:
        result = -1
    return result
'''
        self._verify_source(source)

    def test_C03_except_if(self):
        """C03: except>if - except块内包含if语句"""
        source = '''def target():
    try:
        value = int('abc')
    except ValueError as e:
        error_msg = str(e)
        if 'invalid' in error_msg.lower():
            result = 'parse_error'
        else:
            result = 'unknown_error'
    return result
'''
        self._verify_source(source)

    def test_C04_if_except(self):
        """C04: if>except - 不同条件下使用不同except处理"""
        source = '''def target():
    mode = 'strict'
    try:
        data = int('123x')
    except ValueError:
        if mode == 'strict':
            raise
        else:
            result = 0
    return result
'''
        self._verify_source(source)

    def test_C05_try_if_elif_else(self):
        """C05: try>if-elif-else - try块内包含完整条件链"""
        source = '''def target():
    score = 85
    grade = ''
    try:
        if score >= 90:
            grade = 'A'
        elif score >= 80:
            grade = 'B'
        elif score >= 70:
            grade = 'C'
        else:
            grade = 'D'
    except Exception:
        grade = 'F'
    return grade
'''
        self._verify_source(source)

    def test_C06_if_try_except_finally(self):
        """C06: if>try-except-finally - if语句内包含完整异常处理"""
        source = '''def target():
    divisor = 5
    result = 0
    status = ''
    if divisor != 0:
        try:
            result = 100 / divisor
        except ZeroDivisionError:
            result = 0
        finally:
            status = 'done'
    else:
        status = 'skipped'
    return result, status
'''
        self._verify_source(source)

    def test_C07_nested_try_if(self):
        """C07: nested_try>if - 嵌套try块内包含if语句"""
        source = '''def target():
    result = ''
    try:
        try:
            x = 10
            if x > 5:
                result = 'big'
            else:
                result = 'small'
        except Exception:
            result = 'inner_fail'
    except Exception:
        result = 'outer_fail'
    return result
'''
        self._verify_source(source)

    def test_C08_nested_if_try(self):
        """C08: nested_if>try - 嵌套if语句内包含try-except"""
        source = '''def target():
    x = 10
    y = 0
    if x > 0:
        if y != 0:
            try:
                result = x / y
            except ZeroDivisionError:
                result = float('inf')
        else:
            result = 0
    else:
        result = None
    return result
'''
        self._verify_source(source)

    # ============================================================
    # Category D: with相关 (10个) D01-D10
    # ============================================================

    def test_D01_with_for(self):
        """D01: with>for - 上下文管理器内包含for循环"""
        source = '''def target():
    lines = []
    from io import StringIO
    f = StringIO('hello\\nworld\\npython\\n')
    with f as file:
        for line in file:
            lines.append(line.strip())
    return lines
'''
        self._verify_source(source)

    def test_D02_for_with(self):
        """D02: for>with - for循环内包含上下文管理器"""
        source = '''def target():
    filenames = ['file1.txt', 'file2.txt']
    contents = []
    from io import StringIO
    for name in filenames:
        with StringIO(f'content of {name}') as f:
            contents.append(f.read())
    return contents
'''
        self._verify_source(source)

    def test_D03_with_if(self):
        """D03: with>if - 上下文管理器内包含if语句"""
        source = '''def target():
    from io import StringIO
    f = StringIO('test_data')
    with f as file:
        content = file.read()
        if len(content) > 5:
            result = 'long'
        else:
            result = 'short'
    return result
'''
        self._verify_source(source)

    def test_D04_if_with(self):
        """D04: if>with - if语句内包含上下文管理器"""
        source = '''def target():
    condition = True
    if condition:
        from io import StringIO
        with StringIO('data') as f:
            result = f.read()
    else:
        result = 'skipped'
    return result
'''
        self._verify_source(source)

    def test_D05_with_try(self):
        """D05: with>try - 上下文管理器内包含try-except"""
        source = '''def target():
    from io import StringIO
    f = StringIO('valid_data')
    with f as file:
        try:
            data = file.read()
            result = len(data)
        except IOError:
            result = -1
    return result
'''
        self._verify_source(source)

    def test_D06_try_with(self):
        """D06: try>with - try块内包含上下文管理器"""
        source = '''def target():
    result = ''
    try:
        from io import StringIO
        with StringIO('safe_content') as f:
            result = f.read().upper()
    except Exception:
        result = 'error'
    return result
'''
        self._verify_source(source)

    def test_D07_nested_with_for(self):
        """D07: nested_with>for - 嵌套with块内包含for循环"""
        source = '''def target():
    from io import StringIO
    outer = StringIO('outer_data')
    inner = StringIO('inner_data')
    with outer as o:
        with inner as i:
            files = [o, i]
            contents = []
            for f in files:
                pos = f.tell()
                f.seek(0)
                contents.append(f.read())
                f.seek(pos)
            return contents
'''
        self._verify_source(source)

    def test_D08_multiple_with_for(self):
        """D08: multiple_with>for - 多重with语句内包含for循环"""
        source = '''def target():
    from io import StringIO
    f1 = StringIO('data1')
    f2 = StringIO('data2')
    with f1 as a, f2 as b:
        combined = []
        for pair in zip(a.read(), b.read()):
            combined.append(pair)
    return combined
'''
        self._verify_source(source)

    def test_D09_with_for_try(self):
        """D09: with>for+try - 上下文管理器内包含for循环和异常处理"""
        source = '''def target():
    from io import StringIO
    f = StringIO('1\\n2\\nerror\\n4')
    results = []
    with f as file:
        for line in file:
            line = line.strip()
            try:
                results.append(int(line))
            except ValueError:
                results.append(None)
    return results
'''
        self._verify_source(source)

    def test_D10_for_with_if(self):
        """D10: for>with+if - for循环内包含上下文管理器和条件判断"""
        source = '''def target():
    names = ['alice', 'bob', 'charlie']
    processed = []
    from io import StringIO
    for name in names:
        with StringIO(name) as s:
            text = s.read()
            if len(text) > 3:
                processed.append(text.upper())
            else:
                processed.append(text)
    return processed
'''
        self._verify_source(source)

    # ============================================================
    # Category E: match/case相关 (8个, 3.10+) E01-E08
    # ============================================================

    @pytest.mark.skipif(sys.version_info < (3, 10), reason="requires Python 3.10+")
    def test_E01_match_for(self):
        """E01: match>for - match语句内包含for循环"""
        source = '''def target(value):
    result = []
    match value:
        case list() as lst:
            for item in lst:
                result.append(item * 2)
        case dict() as d:
            for k, v in d.items():
                result.append((k, v))
        case _:
            result = [value]
    return result
'''
        self._verify_source(source)

    @pytest.mark.skipif(sys.version_info < (3, 10), reason="requires Python 3.10+")
    def test_E02_for_match(self):
        """E02: for>match - for循环内包含match语句"""
        source = '''def target(items):
    results = []
    for item in items:
        match item:
            case int() as n if n > 0:
                results.append(('positive', n))
            case int() as n:
                results.append(('non-positive', n))
            case str() as s:
                results.append(('string', s))
            case _:
                results.append(('other', item))
    return results
'''
        self._verify_source(source)

    @pytest.mark.skipif(sys.version_info < (3, 10), reason="requires Python 3.10+")
    def test_E03_match_if(self):
        """E03: match>if - match语句内包含if（guard）"""
        source = '''def target(point):
    match point:
        case (x, y) if x == y:
            result = 'diagonal'
        case (x, y) if x > y:
            result = 'above'
        case (x, y):
            result = 'below'
        case _:
            result = 'unknown'
    return result
'''
        self._verify_source(source)

    @pytest.mark.skipif(sys.version_info < (3, 10), reason="requires Python 3.10+")
    def test_E04_if_match(self):
        """E04: if>match - if语句内包含match"""
        source = '''def target(data, flag):
    if flag:
        match data:
            case {'type': 'user', 'name': name}:
                result = f'User: {name}'
            case {'type': 'admin'}:
                result = 'Admin access'
            case _:
                result = 'Unknown type'
    else:
        result = 'Flag is off'
    return result
'''
        self._verify_source(source)

    @pytest.mark.skipif(sys.version_info < (3, 10), reason="requires Python 3.10+")
    def test_E05_match_try(self):
        """E05: match>try - match语句内包含try-except"""
        source = '''def target(value):
    match value:
        case str() as s:
            try:
                result = int(s)
            except ValueError:
                result = 0
        case int() as n:
            result = n * 2
        case _:
            result = None
    return result
'''
        self._verify_source(source)

    @pytest.mark.skipif(sys.version_info < (3, 10), reason="requires Python 3.10+")
    def test_E06_try_match(self):
        """E06: try>match - try块内包含match语句"""
        source = '''def target(data):
    try:
        match data:
            case [first, *rest]:
                result = (first, rest)
            case (a, b):
                result = (a, b)
            case _:
                result = (None, None)
    except Exception:
        result = ('error', None)
    return result
'''
        self._verify_source(source)

    @pytest.mark.skipif(sys.version_info < (3, 10), reason="requires Python 3.10+")
    def test_E07_match_with(self):
        """E07: match>with - match语句内包含with语句"""
        source = '''def target(mode):
    match mode:
        case 'read':
            from io import StringIO
            with StringIO('content') as f:
                result = f.read()
        case 'write':
            from io import StringIO
            with StringIO() as f:
                f.write('output')
                result = f.getvalue()
        case _:
            result = None
    return result
'''
        self._verify_source(source)

    @pytest.mark.skipif(sys.version_info < (3, 10), reason="requires Python 3.10+")
    def test_E08_complex_match_case(self):
        """E08: complex_match_case - 复杂的match-case模式匹配与嵌套"""
        source = '''def target(command):
    results = []
    match command:
        case ('loop', n):
            for i in range(n):
                if i % 2 == 0:
                    results.append(i)
        case ('process', items):
            for item in items:
                match item:
                    case int() as x if x > 0:
                        results.append(x ** 2)
                    case int() as x:
                        results.append(abs(x))
                    case _:
                        results.append(0)
        case _:
            results = []
    return results
'''
        self._verify_source(source)

    # ============================================================
    # Category F: 同类型嵌套 (12个) F01-F12
    # ============================================================

    def test_F01_triple_if_nesting(self):
        """F01: if>if>if - 三层if嵌套"""
        source = '''def target(a, b, c):
    if a > 0:
        if b > 0:
            if c > 0:
                result = 'all positive'
            else:
                result = 'c not positive'
        else:
            result = 'b not positive'
    else:
        result = 'a not positive'
    return result
'''
        self._verify_source(source)

    def test_F02_triple_for_nesting(self):
        """F02: for>for>for - 三层for嵌套"""
        source = '''def target():
    result = []
    for i in range(2):
        for j in range(2):
            for k in range(2):
                result.append((i, j, k))
    return result
'''
        self._verify_source(source)

    def test_F03_triple_while_nesting(self):
        """F03: while>while>while - 三层while嵌套"""
        source = '''def target():
    i, j, k = 2, 2, 2
    result = []
    while i > 0:
        j = 2
        while j > 0:
            k = 2
            while k > 0:
                result.append((i, j, k))
                k -= 1
            j -= 1
        i -= 1
    return result
'''
        self._verify_source(source)

    def test_F04_triple_try_nesting(self):
        """F04: try>try>try - 三层try嵌套"""
        source = '''def target():
    result = []
    try:
        try:
            try:
                result.append('deep')
            except Exception:
                result.append('inner_error')
        except Exception:
            result.append('middle_error')
    except Exception:
        result.append('outer_error')
    return result
'''
        self._verify_source(source)

    def test_F05_triple_with_nesting(self):
        """F05: with>with>with - 三层with嵌套"""
        source = '''def target():
    from io import StringIO
    a = StringIO('a')
    b = StringIO('b')
    c = StringIO('c')
    with a as fa:
        with b as fb:
            with c as fc:
                result = (fa.read(), fb.read(), fc.read())
    return result
'''
        self._verify_source(source)

    def test_F06_quadruple_if_nesting(self):
        """F06: if>if>if>if - 四层if嵌套"""
        source = '''def target(w, x, y, z):
    if w > 0:
        if x > 0:
            if y > 0:
                if z > 0:
                    result = 'all good'
                else:
                    result = 'z bad'
            else:
                result = 'y bad'
        else:
            result = 'x bad'
    else:
        result = 'w bad'
    return result
'''
        self._verify_source(source)

    def test_F07_quadruple_for_nesting(self):
        """F07: for>for>for>for - 四层for嵌套"""
        source = '''def target():
    result = []
    for i in range(2):
        for j in range(2):
            for k in range(2):
                for l in range(2):
                    result.append(i + j + k + l)
    return result
'''
        self._verify_source(source)

    def test_F08_mixed_if_elif_else(self):
        """F08: mixed_if_elif_else - 混合if-elif-else深层嵌套"""
        source = '''def target(x, y, z):
    if x > 0:
        if y > 0:
            if z > 0:
                result = '+++'
            elif z == 0:
                result = '++0'
            else:
                result = '++-'
        elif y == 0:
            if z > 0:
                result = '+0+'
            else:
                result = '+00'
        else:
            result = '+--'
    else:
        result = '-base'
    return result
'''
        self._verify_source(source)

    def test_F09_double_for_double_if(self):
        """F09: for>for>if>if - 双层for后双层if"""
        source = '''def target(matrix):
    count = 0
    for row in matrix:
        for val in row:
            if isinstance(val, int):
                if val > 0:
                    count += 1
    return count
'''
        self._verify_source(source)

    def test_F10_double_if_double_for(self):
        """F10: if>if>for>for - 双层if后双层for"""
        source = '''def target(flag1, flag2, matrix):
    total = 0
    if flag1:
        if flag2:
            for row in matrix:
                for val in row:
                    total += abs(val)
        else:
            total = -1
    else:
        total = 0
    return total
'''
        self._verify_source(source)

    def test_F11_double_try_double_for(self):
        """F11: try>try>for>for - 双层try后双层for"""
        source = '''def target(data):
    result = []
    try:
        try:
            for group in data:
                for item in group:
                    result.append(item * 2)
        except TypeError:
            result = ['type_error']
    except Exception:
        result = ['general_error']
    return result
'''
        self._verify_source(source)

    def test_F12_double_with_double_if(self):
        """F12: with>with>if>if - 双层with后双层if"""
        source = '''def target():
    from io import StringIO
    a = StringIO('hello')
    b = StringIO('world')
    with a as fa:
        with b as fb:
            text_a = fa.read()
            text_b = fb.read()
            if len(text_a) > 3:
                if len(text_b) > 3:
                    result = 'both long'
                else:
                    result = 'a long only'
            else:
                result = 'short'
    return result
'''
        self._verify_source(source)

    # ============================================================
    # Category G: 复杂控制流混合 (20个) G01-G20
    # ============================================================

    def test_G01_4layer_mixed_1(self):
        """G01: 4层混合嵌套 - if>for>if>for"""
        source = '''def target(groups):
    result = []
    for group in groups:
        if isinstance(group, list):
            for item in group:
                if isinstance(item, int):
                    for _ in range(item):
                        result.append(item)
    return result
'''
        self._verify_source(source)

    def test_G02_4layer_mixed_2(self):
        """G02: 4层混合嵌套 - for>if>for>try"""
        source = '''def target(data):
    results = []
    for row in data:
        if row:
            for val in row:
                try:
                    results.append(int(val))
                except (ValueError, TypeError):
                    results.append(0)
    return results
'''
        self._verify_source(source)

    def test_G03_4layer_mixed_3(self):
        """G03: 4层混合嵌套 - try>for>if>with"""
        source = '''def target():
    from io import StringIO
    results = []
    try:
        data = [[1, 2], [3, 4]]
        for row in data:
            if sum(row) > 3:
                with StringIO(str(sum(row))) as f:
                    results.append(f.read())
    except Exception:
        results = ['error']
    return results
'''
        self._verify_source(source)

    def test_G04_4layer_mixed_4(self):
        """G04: 4层混合嵌套 - with>for>try>if"""
        source = '''def target():
    from io import StringIO
    f = StringIO('1,2,3\\n4,5,6\\n7,8,9')
    results = []
    with f as file:
        for line in file:
            try:
                nums = [int(x) for x in line.strip().split(',')]
                if nums:
                    results.append(sum(nums))
            except ValueError:
                results.append(0)
    return results
'''
        self._verify_source(source)

    def test_G05_4layer_mixed_5(self):
        """G05: 4层混合嵌套 - while>if>for>try"""
        source = '''def target(batches):
    all_results = []
    idx = 0
    while idx < len(batches):
        batch = batches[idx]
        if batch:
            for item in batch:
                try:
                    all_results.append(item ** 2)
                except TypeError:
                    all_results.append(0)
        idx += 1
    return all_results
'''
        self._verify_source(source)

    def test_G06_4layer_mixed_6(self):
        """G06: 4层混合嵌套 - if>try>for>if"""
        source = '''def target(process):
    results = []
    if process:
        try:
            steps = process.get('steps', [])
            for step in steps:
                if step.get('enabled', True):
                    results.append(step['name'])
        except AttributeError:
            results = ['invalid_process']
    else:
        results = []
    return results
'''
        self._verify_source(source)

    def test_G07_4layer_mixed_7(self):
        """G07: 4层混合嵌套 - for>with>if>for"""
        source = '''def target(records):
    matched = []
    from io import StringIO
    for record in records:
        with StringIO(record.get('text', '')) as f:
            content = f.read()
            if 'keyword' in content:
                for word in content.split():
                    if len(word) > 3:
                        matched.append(word)
    return matched
'''
        self._verify_source(source)

    def test_G08_4layer_mixed_8(self):
        """G08: 4层混合嵌套 - try>if>while>for"""
        source = '''def target(config):
    output = []
    try:
        if config.get('active'):
            max_iter = config.get('max_iterations', 5)
            i = 0
            while i < max_iter:
                items = config.get(f'batch_{i}', [])
                for item in items:
                    output.append(item)
                i += 1
    except Exception:
        output = ['error']
    return output
'''
        self._verify_source(source)

    def test_G09_4layer_mixed_9(self):
        """G09: 4层混合嵌套 - with>try>for>if"""
        source = '''def target():
    from io import StringIO
    f = StringIO('10\\n20\\nabc\\n40')
    valid_numbers = []
    with f as file:
        try:
            for line in file:
                num_str = line.strip()
                if num_str.isdigit():
                    valid_numbers.append(int(num_str))
        except IOError:
            valid_numbers = [-1]
    return valid_numbers
'''
        self._verify_source(source)

    def test_G10_4layer_mixed_10(self):
        """G10: 4层混合嵌套 - if>for>try>while"""
        source = '''def target(data_sets):
    final = []
    if data_sets:
        for ds in data_sets:
            try:
                items = ds['items']
                i = 0
                while i < len(items) and i < 3:
                    final.append(items[i])
                    i += 1
            except KeyError:
                final.append(None)
    return final
'''
        self._verify_source(source)

    def test_G11_5layer_mixed_1(self):
        """G11: 5层混合嵌套 - if>for>if>for>if"""
        source = '''def target(matrix_groups):
    selected = []
    for mg in matrix_groups:
        if isinstance(mg, list):
            for matrix in mg:
                if isinstance(matrix, list):
                    for row in matrix:
                        if isinstance(row, list):
                            for val in row:
                                if isinstance(val, int) and val > 5:
                                    selected.append(val)
    return selected
'''
        self._verify_source(source)

    def test_G12_5layer_mixed_2(self):
        """G12: 5层混合嵌套 - try>for>if>try>for"""
        source = '''def target(datasets):
    all_values = []
    try:
        for dataset in datasets:
            if dataset.get('valid'):
                try:
                    rows = dataset['rows']
                    for row in rows:
                        for cell in row:
                            all_values.append(cell)
                except KeyError:
                    all_values.append('missing_rows')
    except Exception:
        all_values = ['error']
    return all_values
'''
        self._verify_source(source)

    def test_G13_5layer_mixed_3(self):
        """G13: 5层混合嵌套 - for>with>if>for>try"""
        source = '''def target(files_data):
    extracted = []
    from io import StringIO
    for fd in files_data:
        with StringIO(fd.get('content', '')) as f:
            lines = f.readlines()
            for line in lines[:10]:
                if line.strip():
                    try:
                        parts = line.strip().split(',')
                        extracted.append(tuple(parts))
                    except Exception:
                        extracted.append(('error',))
    return extracted
'''
        self._verify_source(source)

    def test_G14_5layer_mixed_4(self):
        """G14: 5层混合嵌套 - if>try>for>if>while"""
        source = '''def target(complex_config):
    results = []
    if complex_config.get('enabled'):
        try:
            sections = complex_config['sections']
            for section in sections:
                if section.get('active'):
                    items = section.get('items', [])
                    i = 0
                    while i < min(len(items), 5):
                        results.append(items[i])
                        i += 1
        except Exception:
            results = ['config_error']
    return results
'''
        self._verify_source(source)

    def test_G15_6layer_mixed(self):
        """G15: 6层混合嵌套 - if>for>try>while>if>for"""
        source = '''def target(deep_config):
    output = []
    if deep_config:
        for stage in deep_config.get('stages', []):
            try:
                operations = stage.get('operations', [])
                op_idx = 0
                while op_idx < len(operations):
                    op = operations[op_idx]
                    if op.get('execute'):
                        sub_items = op.get('items', [])
                        for si in sub_items:
                            output.append(si)
                    op_idx += 1
            except Exception:
                output.append('stage_error')
    return output
'''
        self._verify_source(source)

    def test_G16_break_continue_4layer(self):
        """G16: 带break/continue的4层混合嵌套"""
        source = '''def target(data):
    results = []
    for group in data:
        if not group:
            continue
        for item in group:
            if item is None:
                continue
            try:
                val = int(item)
                if val < 0:
                    break
                results.append(val)
            except (ValueError, TypeError):
                continue
    return results
'''
        self._verify_source(source)

    def test_G17_return_deep_nesting(self):
        """G17: 带return的深层嵌套"""
        source = '''def target(config, key):
    if config:
        sections = config.get('sections', [])
        for section in sections:
            if section.get('name') == 'main':
                try:
                    items = section['items']
                    for item in items:
                        if isinstance(item, dict):
                            if item.get('key') == key:
                                return item.get('value')
                except KeyError:
                    return None
    return None
'''
        self._verify_source(source)

    def test_G18_raise_deep_nesting(self):
        """G18: 带raise的深层嵌套"""
        source = '''def target(data, strict=False):
    results = []
    for group in data:
        try:
            for item in group:
                if item is None:
                    if strict:
                        raise ValueError('Null value found')
                    continue
                if isinstance(item, str):
                    results.append(item.upper())
                else:
                    results.append(str(item))
        except ValueError as e:
            return {'error': str(e), 'partial': results}
    return {'results': results}
'''
        self._verify_source(source)

    def test_G19_else_break_continue_complex(self):
        """G19: 带else/break/continue的复杂组合"""
        source = '''def target(search_in_lists, target_value):
    for lst in search_in_lists:
        if not isinstance(lst, list):
            continue
        found = False
        for item in lst:
            if item == target_value:
                found = True
                break
            if item > target_value * 10:
                break
        else:
            if not found:
                return 'not_found'
        if found:
            return 'found'
    return 'exhausted'
'''
        self._verify_source(source)

    def test_G20_7layer_extreme_nesting(self):
        """G20: 7层极限混合嵌套 - if>for>try>while>if>for>if"""
        source = '''def target(ultra_config):
    final_output = []
    if ultra_config and ultra_config.get('active'):
        phases = ultra_config.get('phases', [])
        for phase in phases:
            try:
                iterations = phase.get('iterations', [])
                iter_idx = 0
                while iter_idx < len(iterations) and iter_idx < 3:
                    iteration = iterations[iter_idx]
                    if iteration.get('valid'):
                        tasks = iteration.get('tasks', [])
                        for task in tasks:
                            if task.get('priority', 0) >= 5:
                                actions = task.get('actions', [])
                                for action in actions:
                                    if action.get('enabled'):
                                        final_output.append(action['name'])
                    iter_idx += 1
            except Exception:
                final_output.append('phase_error')
    return final_output
'''
        self._verify_source(source)


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
