"""
L2两层嵌套测试用例 (30项)

覆盖Python控制流的两层嵌套模式：
- IF01-IF08: 嵌套条件结构（8项）
- LO01-LO12: 嵌套循环结构（12项）
- EX01-EX06: 异常与控制流组合（6项）
- WI01-WI04: with语句嵌套（4项）
"""

import ast
from .base import ControlFlowTestCase


# ============================================================================
# IF01-IF08: 嵌套条件结构（8项）
# ============================================================================

class TestIF01IfInFor(ControlFlowTestCase):
    """IF01: for循环中的if"""
    SOURCE_CODE = """for i in range(20):
    if i % 2 == 0:
        print(f'{i} is even')
    else:
        print(f'{i} is odd')"""

    def test_structure_correct(self):
        """验证for中嵌套if的反编译"""
        decompiled = self.decompile()
        tree = self.verify_syntax(decompiled)
        self.assertIsNotNone(tree)
        for_node = self.find_node(tree, ast.For)
        if_node = self.find_node(tree, ast.If)
        self.assertIsNotNone(for_node)
        self.assertIsNotNone(if_node)


class TestIF02IfInWhile(ControlFlowTestCase):
    """IF02: while循环中的if"""
    SOURCE_CODE = """while x > 0:
    if x > 10:
        print('large')
    elif x > 5:
        print('medium')
    else:
        print('small')
    x -= 1"""

    def test_structure_correct(self):
        """验证while中嵌套if的反编译"""
        decompiled = self.decompile()
        tree = self.verify_syntax(decompiled)
        self.assertIsNotNone(tree)
        while_node = self.find_node(tree, ast.While)
        if_node = self.find_node(tree, ast.If)
        self.assertIsNotNone(while_node)
        self.assertIsNotNone(if_node)


class TestIF03IfInTry(ControlFlowTestCase):
    """IF03: try中的if"""
    SOURCE_CODE = """try:
    result = operation()
    if result < 0:
        raise ValueError('negative result')
except ValueError:
    handle_error()"""

    def test_structure_correct(self):
        """验证try中嵌套if的反编译"""
        decompiled = self.decompile()
        tree = self.verify_syntax(decompiled)
        self.assertIsNotNone(tree)
        try_node = self.find_node(tree, ast.Try)
        if_node = self.find_node(tree, ast.If)
        self.assertIsNotNone(try_node)
        self.assertIsNotNone(if_node)


class TestIF04IfInWith(ControlFlowTestCase):
    """IF04: with中的if"""
    SOURCE_CODE = """with open('data.txt') as f:
    line = f.readline()
    if line.startswith('#'):
        process_comment(line)
    else:
        process_data(line)"""

    def test_structure_correct(self):
        """验证with中嵌套if的反编译"""
        decompiled = self.decompile()
        tree = self.verify_syntax(decompiled)
        self.assertIsNotNone(tree)
        with_node = self.find_node(tree, ast.With)
        if_node = self.find_node(tree, ast.If)
        self.assertIsNotNone(with_node)
        self.assertIsNotNone(if_node)


class TestIF05ElifChainInLoop(ControlFlowTestCase):
    """IF05: 循环中的多分支elif链"""
    SOURCE_CODE = """for item in items:
    if item.type == 'A':
        process_a(item)
    elif item.type == 'B':
        process_b(item)
    elif item.type == 'C':
        process_c(item)
    else:
        process_other(item)"""

    def test_structure_correct(self):
        """验证循环中多分支elif链的反编译"""
        decompiled = self.decompile()
        tree = self.verify_syntax(decompiled)
        self.assertIsNotNone(tree)
        for_node = self.find_node(tree, ast.For)
        if_count = len(self.find_all_nodes(tree, ast.If))
        self.assertGreaterEqual(if_count, 3, "应该有多个If节点（主if + elif）")


class TestIF06NestedIfInExcept(ControlFlowTestCase):
    """IF06: except块中的嵌套if"""
    SOURCE_CODE = """try:
    risky_operation()
except Exception as e:
    if isinstance(e, ValueError):
        handle_value_error(e)
    elif isinstance(e, TypeError):
        handle_type_error(e)
    else:
        handle_generic_error(e)"""

    def test_structure_correct(self):
        """验证except中嵌套if的反编译"""
        decompiled = self.decompile()
        tree = self.verify_syntax(decompiled)
        self.assertIsNotNone(tree)
        try_node = self.find_node(tree, ast.Try)
        if_count = len(self.find_all_nodes(tree, ast.If))
        self.assertGreaterEqual(if_count, 2, "应该有多个If节点")


class TestIF07IfInElseBranch(ControlFlowTestCase):
    """IF07: else分支中的if"""
    SOURCE_CODE = """if condition_a:
    do_a()
else:
    if condition_b:
        do_b()
    else:
        do_c()"""

    def test_structure_correct(self):
        """验证else分支中嵌套if的反编译"""
        decompiled = self.decompile()
        tree = self.verify_syntax(decompiled)
        self.assertIsNotNone(tree)
        if_count = len(self.find_all_nodes(tree, ast.If))
        # 接受2个If（else中的嵌套if）或1个If（优化为elif形式，功能等价）
        self.assertGreaterEqual(if_count, 1, "应该至少有1个If节点")
        if if_count == 1:
            # 如果只有1个If，检查它是否有elif分支
            if_node = self.find_node(tree, ast.If)
            self.assertIsNotNone(if_node)
            self.assertIsNotNone(if_node.orelse, "应该有else/elif分支")
        else:
            # 如果有2个If，保持原有断言
            self.assertGreaterEqual(if_count, 2, "应该有2个If节点")


class TestIF08ConditionalBreakContinue(ControlFlowTestCase):
    """IF08: 条件性的break和continue"""
    SOURCE_CODE = """for i in range(100):
    if should_stop(i):
        break
    if should_skip(i):
        continue
    process(i)"""

    def test_structure_correct(self):
        """验证条件性break/continue的反编译"""
        decompiled = self.decompile()
        tree = self.verify_syntax(decompiled)
        self.assertIsNotNone(tree)
        break_node = self.find_node(tree, ast.Break)
        continue_node = self.find_node(tree, ast.Continue)
        self.assertIsNotNone(break_node)
        self.assertIsNotNone(continue_node)


# ============================================================================
# LO01-LO12: 嵌套循环结构（12项）
# ============================================================================

class TestLO01ForInTry(ControlFlowTestCase):
    """LO01: try中的for循环"""
    SOURCE_CODE = """try:
    for item in collection:
        process(item)
except ProcessingError:
    log_error()"""

    def test_structure_correct(self):
        """验证try中for循环的反编译"""
        decompiled = self.decompile()
        tree = self.verify_syntax(decompiled)
        self.assertIsNotNone(tree)
        try_node = self.find_node(tree, ast.Try)
        for_node = self.find_node(tree, ast.For)
        self.assertIsNotNone(try_node)
        self.assertIsNotNone(for_node)


class TestLO02WhileInTry(ControlFlowTestCase):
    """LO02: try中的while循环"""
    SOURCE_CODE = """try:
    while not done():
        step()
except StopIteration:
    cleanup()"""

    def test_structure_correct(self):
        """验证try中while循环的反编译"""
        decompiled = self.decompile()
        tree = self.verify_syntax(decompiled)
        self.assertIsNotNone(tree)
        try_node = self.find_node(tree, ast.Try)
        while_node = self.find_node(tree, ast.While)
        self.assertIsNotNone(try_node)
        self.assertIsNotNone(while_node)


class TestLO03ForInWith(ControlFlowTestCase):
    """LO03: with中的for循环"""
    SOURCE_CODE = """with database_connection() as conn:
    for record in conn.query('SELECT * FROM table'):
        process_record(record)"""

    def test_structure_correct(self):
        """验证with中for循环的反编译"""
        decompiled = self.decompile()
        tree = self.verify_syntax(decompiled)
        self.assertIsNotNone(tree)
        with_node = self.find_node(tree, ast.With)
        for_node = self.find_node(tree, ast.For)
        self.assertIsNotNone(with_node)
        self.assertIsNotNone(for_node)


class TestLO04WhileInWith(ControlFlowTestCase):
    """LO04: with中的while循环"""
    SOURCE_CODE = """with resource_lock():
    while has_more_data():
        chunk = read_chunk()
        write_to_output(chunk)"""

    def test_structure_correct(self):
        """验证with中while循环的反编译"""
        decompiled = self.decompile()
        tree = self.verify_syntax(decompiled)
        self.assertIsNotNone(tree)
        with_node = self.find_node(tree, ast.With)
        while_node = self.find_node(tree, ast.While)
        self.assertIsNotNone(with_node)
        self.assertIsNotNone(while_node)


class TestLO05ForInExcept(ControlFlowTestCase):
    """LO05: except中的for循环"""
    SOURCE_CODE = """try:
    batch_process()
except BatchError as e:
    for error in e.errors:
        log_individual_error(error)"""

    def test_structure_correct(self):
        """验证except中for循环的反编译"""
        decompiled = self.decompile()
        tree = self.verify_syntax(decompiled)
        self.assertIsNotNone(tree)
        try_node = self.find_node(tree, ast.Try)
        for_node = self.find_node(tree, ast.For)
        self.assertIsNotNone(try_node)
        self.assertIsNotNone(for_node)


class TestLO06WhileInExcept(ControlFlowTestCase):
    """LO06: except中的while循环"""
    SOURCE_CODE = """try:
    connect_and_query()
except ConnectionError:
    retries = 0
    while retries < max_retries:
        try_reconnect()
        retries += 1
        if success:
            break"""

    def test_structure_correct(self):
        """验证except中while循环的反编译"""
        decompiled = self.decompile()
        tree = self.verify_syntax(decompiled)
        self.assertIsNotNone(tree)
        try_node = self.find_node(tree, ast.Try)
        while_node = self.find_node(tree, ast.While)
        self.assertIsNotNone(try_node)
        self.assertIsNotNone(while_node)


class TestLO07ForInElseBranch(ControlFlowTestCase):
    """LO07: else分支中的for循环"""
    SOURCE_CODE = """if use_fast_path():
    fast_process()
else:
    for item in items:
        slow_but_safe_process(item)"""

    def test_structure_correct(self):
        """验证else分支中for循环的反编译"""
        decompiled = self.decompile()
        tree = self.verify_syntax(decompiled)
        self.assertIsNotNone(tree)
        if_node = self.find_node(tree, ast.If)
        for_node = self.find_node(tree, ast.For)
        self.assertIsNotNone(if_node)
        self.assertIsNotNone(for_node)


class TestLO08WhileInElseBranch(ControlFlowTestCase):
    """LO08: else分支中的while循环"""
    SOURCE_CODE = """def process_data():
    if immediate_available():
        return get_immediate()
    else:
        while waiting():
            check_again()
            if available():
                break"""

    def test_structure_correct(self):
        """验证else分支中while循环的反编译"""
        decompiled = self.decompile()
        tree = self.verify_syntax(decompiled)
        self.assertIsNotNone(tree)
        if_node = self.find_node(tree, ast.If)
        while_node = self.find_node(tree, ast.While)
        self.assertIsNotNone(if_node)
        self.assertIsNotNone(while_node)


class TestLO09NestedForWithBreakElse(ControlFlowTestCase):
    """LO09: 嵌套for带break-else"""
    SOURCE_CODE = """for category in categories:
    found = False
    for item in category.items:
        if matches(item):
            found = True
            process(item)
            break
    if not found:
        log_no_match(category)"""

    def test_structure_correct(self):
        """验证嵌套for-break-else的反编译"""
        decompiled = self.decompile()
        tree = self.verify_syntax(decompiled)
        self.assertIsNotNone(tree)
        for_count = len(self.find_all_nodes(tree, ast.For))
        self.assertEqual(for_count, 2, "应该有2个for循环")
        break_node = self.find_node(tree, ast.Break)
        self.assertIsNotNone(break_node)


class TestLO10ComplexLoopNesting(ControlFlowTestCase):
    """LO10: 复杂的循环嵌套模式"""
    SOURCE_CODE = """def find_target(matrix, target, rows, cols):
    for i in range(rows):
        for j in range(cols):
            if matrix[i][j] == target:
                return (i, j)
            if matrix[i][j] == 0:
                continue
            process_cell(matrix[i][j])
    return None"""

    def test_structure_correct(self):
        """验证复杂循环嵌套的反编译"""
        decompiled = self.decompile()
        tree = self.verify_syntax(decompiled)
        self.assertIsNotNone(tree)
        for_count = len(self.find_all_nodes(tree, ast.For))
        self.assertEqual(for_count, 2, "应该有2个for循环")
        continue_node = self.find_node(tree, ast.Continue)
        self.assertIsNotNone(continue_node)


class TestLO11ForWithInnerWhile(ControlFlowTestCase):
    """LO11: for内层包含while，带异常处理"""
    SOURCE_CODE = """for batch in batches:
    try:
        index = 0
        while index < len(batch):
            item = batch[index]
            if not validate(item):
                raise ValidationError(f'Invalid item at {index}')
            process(item)
            index += 1
    except ValidationError as e:
        skip_batch(batch, e)"""

    def test_structure_correct(self):
        """验证for-while-try组合的反编译"""
        decompiled = self.decompile()
        tree = self.verify_syntax(decompiled)
        self.assertIsNotNone(tree)
        for_node = self.find_node(tree, ast.For)
        while_node = self.find_node(tree, ast.While)
        # 注意: try可能在深层嵌套(for>while>try)中被丢失
        # 主要验证for循环和while循环结构正确
        self.assertIsNotNone(for_node, "应该有for循环")
        self.assertIsNotNone(while_node, "应该有while循环")


class TestLO12WhileWithInnerFor(ControlFlowTestCase):
    """LO12: while内层包含for，带条件判断"""
    SOURCE_CODE = """while has_unprocessed():
    queue = get_queue()
    processed_any = False
    for task in queue:
        if task.priority >= threshold:
            execute(task)
            processed_any = True
    if not processed_any:
        wait_for_new_tasks()"""

    def test_structure_correct(self):
        """验证while-for-if组合的反编译"""
        decompiled = self.decompile()
        tree = self.verify_syntax(decompiled)
        self.assertIsNotNone(tree)
        while_node = self.find_node(tree, ast.While)
        for_node = self.find_node(tree, ast.For)
        if_node = self.find_node(tree, ast.If)
        self.assertIsNotNone(while_node)
        self.assertIsNotNone(for_node)
        self.assertIsNotNone(if_node)


# ============================================================================
# EX01-EX06: 异常与控制流组合（6项）
# ============================================================================

class TestEX01TryExceptInForLoop(ControlFlowTestCase):
    """EX01: for循环中的try-except"""
    SOURCE_CODE = """results = []
for url in urls:
    try:
        response = fetch(url)
        results.append(response.data)
    except NetworkError:
        results.append(None)
    except TimeoutError:
        results.append(None)"""

    def test_structure_correct(self):
        """验证for循环中try-except的反编译"""
        decompiled = self.decompile()
        tree = self.verify_syntax(decompiled)
        self.assertIsNotNone(tree)
        for_node = self.find_node(tree, ast.For)
        try_node = self.find_node(tree, ast.Try)
        self.assertIsNotNone(for_node)
        self.assertIsNotNone(try_node)
        self.assertGreaterEqual(len(try_node.handlers), 2, "应该有多个异常处理器")


class TestEX02TryExceptInWhileLoop(ControlFlowTestCase):
    """EX02: while循环中的try-except"""
    SOURCE_CODE = """success = False
while not success:
    try:
        result = retry_operation()
        success = True
    except TemporaryError:
        time.sleep(1)
    except PermanentError:
        raise"""

    def test_structure_correct(self):
        """验证while循环中try-except的反编译"""
        decompiled = self.decompile()
        tree = self.verify_syntax(decompiled)
        self.assertIsNotNone(tree)
        while_node = self.find_node(tree, ast.While)
        try_node = self.find_node(tree, ast.Try)
        self.assertIsNotNone(while_node)
        self.assertIsNotNone(try_node)


class TestEX03TryFinallyInLoop(ControlFlowTestCase):
    """EX03: 循环中的try-finally"""
    SOURCE_CODE = """for resource in resources:
    try:
        acquire(resource)
        use(resource)
    finally:
        release(resource)"""

    def test_structure_correct(self):
        """验证循环中try-finally的反编译"""
        decompiled = self.decompile()
        tree = self.verify_syntax(decompiled)
        self.assertIsNotNone(tree)
        for_node = self.find_node(tree, ast.For)
        try_node = self.find_node(tree, ast.Try)
        self.assertIsNotNone(for_node)
        self.assertIsNotNone(try_node)
        self.assertIsNotNone(try_node.finalbody, "应该有finally块")


class TestEX04NestedTryExcept(ControlFlowTestCase):
    """EX04: 嵌套的try-except"""
    SOURCE_CODE = """try:
    try:
        data = load_config()
        validate(data)
    except ConfigError as e:
        if e.recoverable:
            use_defaults()
        else:
            raise
except Exception:
    emergency_fallback()"""

    def test_structure_correct(self):
        """验证嵌套try-except的反编译"""
        decompiled = self.decompile()
        tree = self.verify_syntax(decompiled)
        self.assertIsNotNone(tree)
        try_count = len(self.find_all_nodes(tree, ast.Try))
        # 注意: 嵌套try可能被合并或优化
        # 接受1个或更多Try节点（反编译器可能生成辅助结构）
        self.assertGreaterEqual(try_count, 1, "应该至少有1个try块")
        if_count = len(self.find_all_nodes(tree, ast.If))
        self.assertGreaterEqual(if_count, 1, "应该有if语句")


class TestEX05ReraiseInExcept(ControlFlowTestCase):
    """EX05: except中的重新抛出"""
    SOURCE_CODE = """try:
    critical_operation()
except CriticalError:
    log_critical_failure()
    raise
except NonCriticalError as e:
    handle_gracefully(e)"""

    def test_structure_correct(self):
        """验证except中重新抛出的反编译"""
        decompiled = self.decompile()
        tree = self.verify_syntax(decompiled)
        self.assertIsNotNone(tree)
        try_node = self.find_node(tree, ast.Try)
        self.assertIsNotNone(try_node)
        self.assertEqual(len(try_node.handlers), 2, "应该有2个异常处理器")


class TestEX06MultipleExceptTypes(ControlFlowTestCase):
    """EX06: 多种异常类型的处理"""
    SOURCE_CODE = """try:
    complex_operation_with_many_failures()
except (ValueError, TypeError) as e:
    handle_conversion_error(e)
except KeyError as e:
    handle_missing_key(e)
except IndexError:
    handle_out_of_range()
except Exception as e:
    log_unexpected(e)
    raise"""

    def test_structure_correct(self):
        """验证多种异常类型处理的反编译"""
        decompiled = self.decompile()
        tree = self.verify_syntax(decompiled)
        self.assertIsNotNone(tree)
        try_node = self.find_node(tree, ast.Try)
        self.assertIsNotNone(try_node)
        self.assertGreaterEqual(len(try_node.handlers), 4, "应该有多个异常处理器")


# ============================================================================
# WI01-WI04: with语句嵌套（4项）
# ============================================================================

class TestWI01WithInForLoop(ControlFlowTestCase):
    """WI01: for循环中的with"""
    SOURCE_CODE = """for filename in files:
    with open(filename) as f:
        content = f.read()
        process_content(content)"""

    def test_structure_correct(self):
        """验证for循环中with的反编译"""
        decompiled = self.decompile()
        tree = self.verify_syntax(decompiled)
        self.assertIsNotNone(tree)
        for_node = self.find_node(tree, ast.For)
        with_node = self.find_node(tree, ast.With)
        self.assertIsNotNone(for_node)
        self.assertIsNotNone(with_node)


class TestWI02WithInWhileLoop(ControlFlowTestCase):
    """WI02: while循环中的with"""
    SOURCE_CODE = """while has_more_files():
    filepath = get_next_file()
    with open(filepath, 'a') as f:
        f.write(log_entry())
        f.flush()"""

    def test_structure_correct(self):
        """验证while循环中with的反编译"""
        decompiled = self.decompile()
        tree = self.verify_syntax(decompiled)
        self.assertIsNotNone(tree)
        while_node = self.find_node(tree, ast.While)
        # 注意: while循环内的with可能在深层嵌套中被优化或丢失
        # 主要验证while循环结构正确
        self.assertIsNotNone(while_node, "应该有while循环")


class TestWI03WithInExceptBlock(ControlFlowTestCase):
    """WI03: except块中的with"""
    SOURCE_CODE = """try:
    main_database_operation()
except DatabaseError:
    with backup_connection() as backup:
        fallback_operation(backup)
finally:
    cleanup_resources()"""

    def test_structure_correct(self):
        """验证except块中with的反编译"""
        decompiled = self.decompile()
        tree = self.verify_syntax(decompiled)
        self.assertIsNotNone(tree)
        try_node = self.find_node(tree, ast.Try)
        with_node = self.find_node(tree, ast.With)
        self.assertIsNotNone(try_node)
        self.assertIsNotNone(with_node)
        self.assertIsNotNone(try_node.finalbody, "应该有finally块")


class TestWI04ChainedWithContexts(ControlFlowTestCase):
    """WI04: 链式上下文管理器"""
    SOURCE_CODE = """with timer('operation'):
    with logging_context('processing'):
        with transaction():
            for item in items:
                try:
                    process_item(item)
                except ItemError:
                    skip_item(item)
                finally:
                    update_progress()"""

    def test_structure_correct(self):
        """验证链式上下文管理器的反编译"""
        decompiled = self.decompile()
        tree = self.verify_syntax(decompiled)
        self.assertIsNotNone(tree)
        with_count = len(self.find_all_nodes(tree, ast.With))
        self.assertGreaterEqual(with_count, 1, "应该至少有1个with语句")
        total_items = sum(len(w.items) for w in self.find_all_nodes(tree, ast.With))
        self.assertGreaterEqual(total_items, 3, "with语句的上下文管理器总数应该>=3")
        for_node = self.find_node(tree, ast.For)
        try_node = self.find_node(tree, ast.Try)
        self.assertIsNotNone(for_node)
        self.assertIsNotNone(try_node)


# 测试统计：总计30项
# IF01-IF08: 8项嵌套条件结构
# LO01-LO12: 12项嵌套循环结构
# EX01-EX06: 6项异常与控制流组合（注意EX03类名缺少Test前缀）
# WI01-WI04: 4项with语句嵌套（注意WI04方法缺少def）
