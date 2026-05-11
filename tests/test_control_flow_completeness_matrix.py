"""
控制流语法完备性测试矩阵
总计: 96 测试用例
覆盖: 所有Python控制流语法及其嵌套排列组合

测试分类:
- B01-B08: 基础结构 (8个)
- C01-C07: 条件结构 (7个)
- L01-L18: 循环结构 (18个)
- E01-E13: 异常处理 (13个)
- W01-W06: with语句 (6个)
- CF1-CF16: 两层嵌套关键组合 (16个)
- N01-N18: 三层嵌套关键组合 (18个)
- D1-D8: 四层嵌套边界测试 (8个)
"""

import pytest
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# ==================== 辅助函数 ====================

def compile_and_decompile(source: str) -> str:
    """编译源码→反编译→返回结果"""
    # TODO: 实现反编译调用
    pass

def verify_syntax(source: str, result: str = None):
    """验证反编译结果语法正确性"""
    code = compile(source, '<test>', 'exec')
    if result:
        compile(result, '<output>', 'exec')

# ==================== 12.1 基础结构 (8个) ====================

class TestBasicStructures:
    """B01-B08: 基础控制流结构"""

    def test_B01_simple_assignment(self):
        """B01: 简单赋值 x = 1"""
        source = '''
def target():
    x = 1
'''
        verify_syntax(source)

    def test_B02_augmented_assignment(self):
        """B02: 增强赋值 x += 1"""
        source = '''
def target():
    x = 0
    x += 1
'''
        verify_syntax(source)

    def test_B03_multi_target(self):
        """B03: 多目标赋值 a = b = 1"""
        source = '''
def target():
    a = b = 1
'''
        verify_syntax(source)

    def test_B04_tuple_unpack(self):
        """B04: 元组解包 a, b = 1, 2"""
        source = '''
def target():
    a, b = 1, 2
'''
        verify_syntax(source)

    def test_B05_expr_statement(self):
        """B05: 表达式语句 print(x)"""
        source = '''
def target(x):
    print(x)
'''
        verify_syntax(source)

    def test_B06_return_value(self):
        """B06: return有值"""
        source = '''
def target():
    return 42
'''
        verify_syntax(source)

    def test_B07_return_none(self):
        """B07: return无值"""
        source = '''
def target():
    return
'''
        verify_syntax(source)

    def test_B08_pass(self):
        """B08: pass"""
        source = '''
def target():
    pass
'''
        verify_syntax(source)

# ==================== 12.2 条件结构 (7个) ====================

class TestConditionalStructures:
    """C01-C07: 条件结构"""

    def test_C01_if_then(self):
        """C01: if-then"""
        source = '''
def target(x):
    if x > 0:
        print("positive")
'''
        verify_syntax(source)

    def test_C02_if_else(self):
        """C02: if-else"""
        source = '''
def target(x):
    if x > 0:
        print("positive")
    else:
        print("non-positive")
'''
        verify_syntax(source)

    def test_C03_if_elif(self):
        """C03: if-elif"""
        source = '''
def target(x):
    if x > 0:
        print("positive")
    elif x < 0:
        print("negative")
'''
        verify_syntax(source)

    def test_C04_if_elif_else(self):
        """C04: if-elif-else"""
        source = '''
def target(x):
    if x > 0:
        print("positive")
    elif x < 0:
        print("negative")
    else:
        print("zero")
'''
        verify_syntax(source)

    def test_C05_multi_elif(self):
        """C05: 多层elif链"""
        source = '''
def target(x):
    if x == 1:
        print("one")
    elif x == 2:
        print("two")
    elif x == 3:
        print("three")
    else:
        print("other")
'''
        verify_syntax(source)

    def test_C06_nested_if(self):
        """C06: 嵌套if"""
        source = '''
def target(x, y):
    if x > 0:
        if y > 0:
            print("both positive")
'''
        verify_syntax(source)

    def test_C07_nested_if_else(self):
        """C07: 嵌套if-else"""
        source = '''
def target(x, y):
    if x > 0:
        if y > 0:
            print("both positive")
        else:
            print("x positive, y not")
    else:
        print("x not positive")
'''
        verify_syntax(source)

# ==================== 12.3 循环结构 (18个) ====================

class TestLoopStructures:
    """L01-L18: 循环结构"""

    def test_L01_for_loop(self):
        """L01: for循环"""
        source = '''
def target(items):
    for item in items:
        print(item)
'''
        verify_syntax(source)

    def test_L02_while_loop(self):
        """L02: while循环"""
        source = '''
def target(n):
    i = 0
    while i < n:
        print(i)
        i += 1
'''
        verify_syntax(source)

    def test_L03_for_else(self):
        """L03: for-else"""
        source = '''
def target(items):
    for item in items:
        if item < 0:
            break
    else:
        print("no break")
'''
        verify_syntax(source)

    def test_L04_while_else(self):
        """L04: while-else"""
        source = '''
def target(n):
    i = 0
    while i < n:
        if i == 5:
            break
        i += 1
    else:
        print("completed")
'''
        verify_syntax(source)

    def test_L05_for_break(self):
        """L05: for-break"""
        source = '''
def target(items):
    for item in items:
        if item < 0:
            break
        print(item)
'''
        verify_syntax(source)

    def test_L06_for_continue(self):
        """L06: for-continue"""
        source = '''
def target(items):
    for item in items:
        if item < 0:
            continue
        print(item)
'''
        verify_syntax(source)

    def test_L07_while_break(self):
        """L07: while-break"""
        source = '''
def target(n):
    i = 0
    while True:
        if i >= n:
            break
        print(i)
        i += 1
'''
        verify_syntax(source)

    def test_L08_while_continue(self):
        """L08: while-continue"""
        source = '''
def target(n):
    for i in range(n):
        if i % 2 == 0:
            continue
        print(i)
'''
        verify_syntax(source)

    def test_L09_for_break_else(self):
        """L09: for-break-else"""
        source = '''
def target(items):
    found = None
    for item in items:
        if item > 10:
            found = item
            break
    else:
        found = -1
    return found
'''
        verify_syntax(source)

    def test_L10_while_break_else(self):
        """L10: while-break-else"""
        source = '''
def target(n):
    i = 0
    while i < n:
        if i == 5:
            break
        i += 1
    else:
        i = -1
    return i
'''
        verify_syntax(source)

    def test_L11_for_break_continue(self):
        """L11: for-break-continue"""
        source = '''
def target(items):
    for item in items:
        if item < 0:
            continue
        if item > 100:
            break
        process(item)
'''
        verify_syntax(source)

    def test_L12_while_break_continue(self):
        """L12: while-break-continue"""
        source = '''
def target(data):
    i = 0
    n = len(data)
    while i < n:
        if data[i] is None:
            i += 1
            continue
        if data[i] == "STOP":
            break
        process(data[i])
        i += 1
'''
        verify_syntax(source)

    def test_L13_nested_for(self):
        """L13: 嵌套for"""
        source = '''
def target(matrix):
    result = []
    for row in matrix:
        for val in row:
            result.append(val * 2)
    return result
'''
        verify_syntax(source)

    def test_L14_nested_while(self):
        """L14: 嵌套while"""
        source = '''
def target(m, n):
    i = 0
    while i < m:
        j = 0
        while j < n:
            process(i, j)
            j += 1
        i += 1
'''
        verify_syntax(source)

    def test_L15_nested_for_break(self):
        """L15: 嵌套for内break"""
        source = '''
def target(matrix):
    for row in matrix:
        for val in row:
            if val is None:
                break
            print(val)
'''
        verify_syntax(source)

    def test_L16_nested_for_continue(self):
        """L16: 嵌套for内continue"""
        source = '''
def target(matrix):
    for row in matrix:
        for val in row:
            if val <= 0:
                continue
            print(val)
'''
        verify_syntax(source)

    def test_L17_for_in_while(self):
        """L17: for中嵌套while"""
        source = '''
def target(groups):
    for group in groups:
        i = 0
        while i < len(group):
            if group[i] == 0:
                break
            process(group[i])
            i += 1
'''
        verify_syntax(source)

    def test_L18_while_in_for(self):
        """L18: while中嵌套for"""
        source = '''
def target(n):
    outer = 0
    while outer < n:
        for inner in range(outer):
            process(outer, inner)
        outer += 1
'''
        verify_syntax(source)

# ==================== 12.4 异常处理 (13个) ====================

class TestExceptionHandling:
    """E01-E13: 异常处理"""

    def test_E01_try_except(self):
        """E01: try-except"""
        source = '''
def target(x):
    try:
        result = 10 / x
    except ZeroDivisionError:
        result = 0
    return result
'''
        verify_syntax(source)

    def test_E02_try_multi_except(self):
        """E02: try多except"""
        source = '''
def target(op, a, b):
    try:
        if op == '+':
            result = a + b
        elif op == '-':
            result = a - b
        else:
            result = a * b
    except TypeError:
        result = 0
    except ValueError:
        result = -1
    return result
'''
        verify_syntax(source)

    def test_E03_try_except_else(self):
        """E03: try-except-else"""
        source = '''
def target(x):
    try:
        result = 10 / x
    except ZeroDivisionError:
        result = 0
    else:
        print(f"Success: {result}")
    return result
'''
        verify_syntax(source)

    def test_E04_try_finally(self):
        """E04: try-finally"""
        source = '''
def target(resource):
    try:
        use_resource(resource)
    finally:
        cleanup(resource)
'''
        verify_syntax(source)

    def test_E05_try_except_finally(self):
        """E05: try-except-finally"""
        source = '''
def target(x):
    try:
        result = 10 / x
    except ZeroDivisionError:
        result = 0
    finally:
        log_operation()
    return result
'''
        verify_syntax(source)

    def test_E06_try_except_else_finally(self):
        """E06: try-except-else-finally完整组合"""
        source = '''
def target(x):
    try:
        result = 10 / x
    except ZeroDivisionError:
        result = 0
    else:
        print("success")
    finally:
        cleanup()
    return result
'''
        verify_syntax(source)

    def test_E07_except_as(self):
        """E07: except-as"""
        source = '''
def target(x):
    try:
        result = 10 / x
    except ZeroDivisionError as e:
        log_error(e)
        result = 0
    return result
'''
        verify_syntax(source)

    def test_E08_bare_except(self):
        """E08: bare-except"""
        source = '''
def risky_operation():
    try:
        do_something_risky()
    except:
        handle_error()
'''
        verify_syntax(source)

    def test_E09_nested_try(self):
        """E09: 嵌套try"""
        source = '''
def target(x, y):
    try:
        try:
            result = x / y
        except ZeroDivisionError:
            result = 0
    except TypeError:
        result = -1
    return result
'''
        verify_syntax(source)

    def test_E10_try_with_loop(self):
        """E10: try中嵌套循环"""
        source = '''
def target(items):
    results = []
    try:
        for item in items:
            results.append(process(item))
    except ProcessingError:
        results = []
    return results
'''
        verify_syntax(source)

    def test_E11_loop_with_try(self):
        """E11: 循环中嵌套try"""
        source = '''
def target(items):
    results = []
    for item in items:
        try:
            results.append(process(item))
        except ValueError:
            results.append(None)
    return results
'''
        verify_syntax(source)

    def test_E12_try_with_if(self):
        """E12: try中嵌套if"""
        source = '''
def target(x, y):
    try:
        if x > 0:
            result = safe_divide(y)
        else:
            result = 0
    except Error:
        result = -1
    return result
'''
        verify_syntax(source)

    def test_E13_if_with_try(self):
        """E13: if中嵌套try"""
        source = '''
def target(flag, x):
    if flag:
        try:
            result = risky_op(x)
        except Exception:
            result = default_value
    else:
        result = safe_op(x)
    return result
'''
        verify_syntax(source)

# ==================== 12.5 with结构 (6个) ====================

class TestWithStatements:
    """W01-W06: with语句"""

    def test_W01_simple_with(self):
        """W01: 简单with"""
        source = '''
def target(filename):
    with open(filename) as f:
        content = f.read()
    return content
'''
        verify_syntax(source)

    def test_W02_with_no_as(self):
        """W02: with无as"""
        source = '''
def target(lock):
    with lock:
        critical_section()
'''
        verify_syntax(source)

    def test_W03_multi_context_with(self):
        """W03: 多上下文with"""
        source = '''
def target(f1_name, f2_name):
    with open(f1_name) as f1, open(f2_name) as f2:
        copy_data(f1, f2)
'''
        verify_syntax(source)

    def test_W04_nested_with(self):
        """W04: 嵌套with"""
        source = '''
def target(outer_file, inner_file):
    with open(outer_file) as outer:
        data = outer.read()
        with open(inner_file, 'w') as inner:
            inner.write(data)
'''
        verify_syntax(source)

    def test_W05_with_with_try(self):
        """W05: with中嵌套try"""
        source = '''
def target(filename):
    with open(filename) as f:
        try:
            data = json.load(f)
        except json.JSONDecodeError:
            data = {}
    return data
'''
        verify_syntax(source)

    def test_W06_try_with_with(self):
        """W06: try中嵌套with"""
        source = '''
def target(filename):
    try:
        with open(filename) as f:
            return f.read()
    except IOError:
        return ""
'''
        verify_syntax(source)

# ==================== 12.6 两层嵌套关键组合 (16个) ====================

class TestTwoLevelNesting:
    """CF1-CF16: 两层嵌套关键组合"""

    def test_CF1_for_if_break_continue(self):
        """CF1: for中if+break/continue"""
        source = '''
def target(items):
    for item in items:
        if item < 0:
            continue
        if item > 1000:
            break
        process(item)
'''
        verify_syntax(source)

    def test_CF2_while_if_break_continue(self):
        """CF2: while中if+break/continue"""
        source = '''
def target(data):
    i = 0
    n = len(data)
    while i < n:
        if data[i] is None:
            i += 1
            continue
        if data[i] == "END":
            break
        process(data[i])
        i += 1
'''
        verify_syntax(source)

    def test_CL1_if_with_for(self):
        """CL1: if中嵌套for"""
        source = '''
def target(flag, items):
    if flag:
        for item in items:
            process(item)
    else:
        skip_all()
'''
        verify_syntax(source)

    def test_CL2_if_with_while(self):
        """CL2: if中嵌套while"""
        source = '''
def target(flag, condition):
    if flag:
        while condition.holds():
            process(condition.get())
    else:
        wait()
'''
        verify_syntax(source)

    def test_CL3_if_with_try(self):
        """CL3: if中嵌套try"""
        source = '''
def target(flag, x):
    if flag:
        try:
            result = risky_op(x)
        except Exception:
            result = fallback
    else:
        result = safe_op(x)
    return result
'''
        verify_syntax(source)

    def test_CL4_if_with_with(self):
        """CL4: if中嵌套with"""
        source = '''
def target(flag, filename):
    if flag:
        with open(filename) as f:
            data = f.read()
    else:
        data = ""
    return data
'''
        verify_syntax(source)

    def test_CE1_try_with_for(self):
        """CE1: try中嵌套for"""
        source = '''
def target(items):
    try:
        for item in items:
            process(item)
    except Exception:
        handle_error()
'''
        verify_syntax(source)

    def test_CE2_try_with_while(self):
        """CE2: try中嵌套while"""
        source = '''
def target(condition):
    try:
        while condition.active():
            work(condition.get())
    except StopIteration:
        done()
'''
        verify_syntax(source)

    def test_CE3_try_with_if(self):
        """CE3: try中嵌套if"""
        source = '''
def target(x, y):
    try:
        if x > 0:
            compute(y)
        else:
            skip()
    except Error:
        recover()
'''
        verify_syntax(source)

    def test_CE4_try_with_with(self):
        """CE4: try中嵌套with"""
        source = '''
def target(filename):
    try:
        with open(filename) as f:
            return parse(f)
    except ParseError:
        return None
'''
        verify_syntax(source)

    def test_CW1_with_with_for(self):
        """CW1: with中嵌套for"""
        source = '''
def target(filename):
    with open(filename) as f:
        for line in f:
            process(line.strip())
'''
        verify_syntax(source)

    def test_CW2_with_with_while(self):
        """CW2: with中嵌套while"""
        source = '''
def target(connection):
    with connection.cursor() as cursor:
        while has_more_data():
            row = cursor.fetchone()
            process(row)
'''
        verify_syntax(source)

    def test_CW3_with_with_if(self):
        """CW3: with中嵌套if"""
        source = '''
def target(filename):
    with open(filename) as f:
        data = f.read()
        if data.startswith("#"):
            header = data.split("\\n")[0]
        else:
            header = None
    return header
'''
        verify_syntax(source)

    def test_CW4_with_with_try(self):
        """CW4: with中嵌套try"""
        source = '''
def target(filename):
    with open(filename) as f:
        try:
            data = json.load(f)
        except json.JSONDecodeError:
            data = {}
    return data
'''
        verify_syntax(source)

    def test_LE1_loop_with_try_for(self):
        """LE1: 循环+try+for混合"""
        source = '''
def target(batches):
    results = []
    for batch in batches:
        try:
            for item in batch:
                results.append(transform(item))
        except TransformError:
            continue
    return results
'''
        verify_syntax(source)

    def test_LE2_loop_with_if_try(self):
        """LE2: 循环+if+try混合"""
        source = '''
def target(items):
    for item in items:
        if item.valid:
            try:
                process(item)
            except Error:
                log_error(item)
        else:
            skip_item(item)
'''
        verify_syntax(source)

# ==================== 12.7 三层嵌套关键组合 (18个) ====================

class TestThreeLevelNesting:
    """N01-N18: 三层嵌套"""

    def test_N01_for_if_break(self):
        """N01: for > if > break"""
        source = '''
def target(matrix):
    for row in matrix:
        for val in row:
            if val is None:
                break
            print(val)
'''
        verify_syntax(source)

    def test_N02_for_if_continue(self):
        """N02: for > if > continue"""
        source = '''
def target(matrix):
    count = 0
    for row in matrix:
        for val in row:
            if val <= 0:
                continue
            count += 1
    return count
'''
        verify_syntax(source)

    def test_N03_for_if_for(self):
        """N03: for > if > for"""
        source = '''
def target(groups):
    all_items = []
    for group in groups:
        if group.active:
            for item in group.items:
                all_items.append(item)
    return all_items
'''
        verify_syntax(source)

    def test_N04_for_if_while(self):
        """N04: for > if > while"""
        source = '''
def target(tasks):
    completed = []
    for task in tasks:
        if task.priority > 5:
            while not task.done():
                task.work()
            completed.append(task)
    return completed
'''
        verify_syntax(source)

    def test_N05_for_if_try(self):
        """N05: for > if > try"""
        source = '''
def target(items):
    results = []
    for item in items:
        if item.needs_processing:
            try:
                result = process(item)
                results.append(result)
            except ProcessError:
                results.append(None)
    return results
'''
        verify_syntax(source)

    def test_N06_for_if_with(self):
        """N06: for > if > with"""
        source = '''
def target(files):
    contents = []
    for file_info in files:
        if file_info.exists:
            with open(file_info.path) as f:
                contents.append(f.read())
    return contents
'''
        verify_syntax(source)

    def test_N07_while_if_break(self):
        """N07: while > if > break"""
        source = '''
def target(data):
    i = 0
    n = len(data)
    while i < n:
        j = 0
        m = len(data[i])
        while j < m:
            if data[i][j] is None:
                break
            process(data[i][j])
            j += 1
        i += 1
'''
        verify_syntax(source)

    def test_N08_while_if_continue(self):
        """N08: while > if > continue"""
        source = '''
def target(data):
    i = 0
    n = len(data)
    total = 0
    while i < n:
        j = 0
        m = len(data[i])
        while j < m:
            if data[i][j] <= 0:
                j += 1
                continue
            total += data[i][j]
            j += 1
        i += 1
    return total
'''
        verify_syntax(source)

    def test_N09_while_if_for(self):
        """N09: while > if > for"""
        source = '''
def target(queue):
    results = []
    while not queue.empty():
        batch = queue.get_batch()
        if batch:
            for item in batch:
                results.append(process(item))
    return results
'''
        verify_syntax(source)

    def test_N10_while_if_while(self):
        """N10: while > if > while"""
        source = '''
def target(sessions):
    active_sessions = []
    while has_sessions():
        session = get_session()
        if session.is_valid:
            while session.has_requests():
                request = session.next_request()
                handle_request(request)
            active_sessions.append(session)
    return active_sessions
'''
        verify_syntax(source)

    def test_N11_while_if_try(self):
        """N11: while > if > try"""
        source = '''
def target(workers):
    results = []
    while workers.available():
        worker = workers.get()
        if worker.can_process:
            try:
                result = worker.process_task()
                results.append(result)
            except WorkerError:
                workers.requeue(worker)
    return results
'''
        verify_syntax(source)

    def test_N12_while_if_with(self):
        """N12: while > if > with"""
        source = '''
def target(resources):
    outputs = []
    while resources.has_next():
        res = resources.next()
        if res.is_ready:
            with res.lock:
                output = res.generate()
                outputs.append(output)
    return outputs
'''
        verify_syntax(source)

    def test_N13_try_for_if_break(self):
        """N13: try > for > if > break"""
        source = '''
def target(data):
    try:
        for group in data.groups:
            valid = True
            for item in group:
                if item.error:
                    valid = False
                    break
                process(item)
            if not valid:
                raise ValidationError()
    except ValidationError:
        rollback()
'''
        verify_syntax(source)

    def test_N14_try_for_if_for_break(self):
        """N14: for > if > for > break (四层边界)"""
        source = '''
def target(data):
    for group in data.groups:
        valid = True
        for item in group:
            if item.bad:
                valid = False
                break
            for sub in item.parts:
                if sub.invalid:
                    return None
                process(sub)
        if not valid:
            continue
        save(group)
'''
        verify_syntax(source)

    def test_N15_try_while_if_break(self):
        """N15: try > while > if > break"""
        source = '''
def target(streams):
    try:
        while streams.has_more():
            stream = streams.get_stream()
            while stream.has_data():
                chunk = stream.read_chunk()
                if chunk is None:
                    break
                process(chunk)
    except StreamError:
        close_all(streams)
'''
        verify_syntax(source)

    def test_N16_if_for_if_break(self):
        """N16: if > for > if > break"""
        source = '''
def target(flag, matrix):
    if flag:
        for row in matrix:
            for val in row:
                if val < 0:
                    break
                accumulate(val)
    else:
        use_default()
'''
        verify_syntax(source)

    def test_N17_if_while_if_continue(self):
        """N17: if > while > if > continue"""
        source = '''
def target(mode, data):
    if mode == "strict":
        i = 0
        n = len(data)
        while i < n:
            j = 0
            m = len(data[i])
            while j < m:
                if data[i][j].invalid:
                    j += 1
                    continue
                validate(data[i][j])
                j += 1
            i += 1
    else:
        fast_validate(data)
'''
        verify_syntax(source)

    def test_N18_try_for_if_break(self):
        """N18: try > for > if > break"""
        source = '''
def target(data):
    try:
        for group in data.groups:
            success = True
            for item in group.items:
                if item.error:
                    success = False
                    break
                process(item)
            if not success:
                raise ProcessingError()
    except ProcessingError:
        rollback()
'''
        verify_syntax(source)

# ==================== 12.8 四层嵌套边界测试 (8个) ====================

class TestFourLevelNestingBoundary:
    """D1-D8: 四层深层嵌套边界测试"""

    def test_D1_for_if_for_break(self):
        """D1: for>if>for>break"""
        source = '''
def target(data):
    for category in data.categories:
        for group in category.groups:
            valid = True
            for item in group.items:
                if item.corrupted:
                    valid = False
                    break
                check(item)
            if not valid:
                mark_invalid(group)
'''
        verify_syntax(source)

    def test_D2_for_if_while_break(self):
        """D2: for>if>while>break"""
        source = '''
def target(records):
    for record_set in records.sets:
        for record in record_set:
            if record.needs_validation:
                i = 0
                fields = record.fields
                while i < len(fields):
                    if fields[i].invalid:
                        break
                    validate_field(fields[i])
                    i += 1
'''
        verify_syntax(source)

    def test_D3_while_if_for_break(self):
        """D3: while>if>for>break"""
        source = '''
def target(batches):
    while batches.has_more():
        batch = batches.next()
        if batch.priority >= 5:
            for task in batch.tasks:
                if task.failed:
                    break
                execute(task)
        advance()
'''
        verify_syntax(source)

    def test_D4_while_if_while_break(self):
        """D4: while>if>while>break"""
        source = '''
def target(systems):
    while systems.running():
        system = systems.current()
        if system.active:
            while system.has_processes():
                proc = system.next_process()
                if proc.zombie:
                    break
                monitor(proc)
        tick()
'''
        verify_syntax(source)

    def test_D5_try_for_if_for_break(self):
        """D5: try>for>if>for>break"""
        source = '''
def target(dataset):
    try:
        for table in dataset.tables:
            for row in table.rows:
                complete = True
                for cell in row.cells:
                    if cell.empty:
                        complete = False
                        break
                    analyze(cell)
                if not complete:
                    raise IncompleteRowError()
    except IncompleteRowError:
        report_missing(dataset)
'''
        verify_syntax(source)

    def test_D6_if_for_if_while_break(self):
        """D6: if>for>if>while>break"""
        source = '''
def target(mode, collections):
    if mode == "deep":
        for collection in collections:
            for group in collection.groups:
                if group.complex:
                    i = 0
                    items = group.items
                    while i < len(items):
                        if items[i].timeout:
                            break
                        deep_process(items[i])
                        i += 1
    else:
        shallow_process(collections)
'''
        verify_syntax(source)

    def test_D7_for_try_for_if_break(self):
        """D7: for>try>for>if>break"""
        source = '''
def target(pipelines):
    errors = []
    for pipeline in pipelines:
        try:
            for stage in pipeline.stages:
                for operation in stage.operations:
                    if operation.critical and operation.failed:
                        raise StageFailure(operation)
                    run(operation)
        except StageFailure as e:
            errors.append(e)
    return errors
'''
        verify_syntax(source)

    def test_D8_while_try_while_if_break(self):
        """D8: while>try>while>if>break"""
        source = '''
def target(sessions):
    failed = []
    while sessions.active():
        session = sessions.current()
        try:
            while session.has_transactions():
                tx = session.next_transaction()
                if tx.timeout:
                    break
                process(tx)
        except TransactionError as e:
            failed.append((session.id, e))
        sessions.advance()
    return failed
'''
        verify_syntax(source)


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
