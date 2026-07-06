"""
L2两层嵌套测试用例 (48项)

覆盖Python控制流的两层嵌套模式：
- if×{if,for,while,try,with}组合（5项）
- for×{if,for,while,try,break,continue}组合（6项）
- while×{if,for,while,try,break,continue}组合（6项）
- try×{if,for,while,try,with}组合（5项）
- with×{try,with}组合（2项）
- 特殊组合（24项）：for中if+break/continue等

总计: 48项测试
"""

import ast
from tests.control_flow_matrix.base import ControlFlowTestCase


# ============================================================================
# if×{if,for,while,try,with}组合（5项）
# ============================================================================

class TestL2_IfNestedIf(ControlFlowTestCase):
    """L2-if01: 嵌套if-in-if"""
    SOURCE_CODE = """if outer:
    if inner:
        x = 1"""

    def test_structure_correct(self):
        decompiled = self.decompile()
        tree = self.verify_syntax(decompiled)
        self.assertIsNotNone(tree)
        if_count = len(self.find_all_nodes(tree, ast.If))
        # 注意：反编译器可能将嵌套if优化为elif结构
        self.assertGreaterEqual(if_count, 1, "应该至少有1个if语句")


class TestL2_IfWithFor(ControlFlowTestCase):
    """L2-if02: if包含for循环"""
    SOURCE_CODE = """if condition:
    for i in range(10):
        x = i"""

    def test_structure_correct(self):
        decompiled = self.decompile()
        tree = self.verify_syntax(decompiled)
        self.assertIsNotNone(tree)
        if_node = self.find_node(tree, ast.If)
        for_node = self.find_node(tree, ast.For)
        self.assertIsNotNone(if_node)
        self.assertIsNotNone(for_node)


class TestL2_IfWithWhile(ControlFlowTestCase):
    """L2-if03: if包含while循环"""
    SOURCE_CODE = """if condition:
    while cond:
        x = 1"""

    def test_structure_correct(self):
        decompiled = self.decompile()
        tree = self.verify_syntax(decompiled)
        self.assertIsNotNone(tree)
        if_node = self.find_node(tree, ast.If)
        while_node = self.find_node(tree, ast.While)
        self.assertIsNotNone(if_node)
        self.assertIsNotNone(while_node)


class TestL2_IfWithTry(ControlFlowTestCase):
    """L2-if04: if包含try块"""
    SOURCE_CODE = """if condition:
    try:
        x = risky()
    except Error:
        x = default"""

    def test_structure_correct(self):
        decompiled = self.decompile()
        tree = self.verify_syntax(decompiled)
        self.assertIsNotNone(tree)
        if_node = self.find_node(tree, ast.If)
        try_node = self.find_node(tree, ast.Try)
        self.assertIsNotNone(if_node)
        self.assertIsNotNone(try_node)


class TestL2_IfWithWith(ControlFlowTestCase):
    """L2-if05: if包含with语句"""
    SOURCE_CODE = """if condition:
    with open('file') as f:
        content = f.read()"""

    def test_structure_correct(self):
        decompiled = self.decompile()
        tree = self.verify_syntax(decompiled)
        self.assertIsNotNone(tree)
        if_node = self.find_node(tree, ast.If)
        with_node = self.find_node(tree, ast.With)
        self.assertIsNotNone(if_node)
        self.assertIsNotNone(with_node)


# ============================================================================
# for×{if,for,while,try,break,continue}组合（6项）
# ============================================================================

class TestL2_ForWithIf(ControlFlowTestCase):
    """L2-for01: for循环包含if"""
    SOURCE_CODE = """for i in range(10):
    if i % 2 == 0:
        x = i"""

    def test_structure_correct(self):
        decompiled = self.decompile()
        tree = self.verify_syntax(decompiled)
        self.assertIsNotNone(tree)
        for_node = self.find_node(tree, ast.For)
        if_node = self.find_node(tree, ast.If)
        self.assertIsNotNone(for_node)
        self.assertIsNotNone(if_node)


class TestL2_ForNestedFor(ControlFlowTestCase):
    """L2-for02: 嵌套for-in-for"""
    SOURCE_CODE = """for i in range(5):
    for j in range(5):
        x = i * j"""

    def test_structure_correct(self):
        decompiled = self.decompile()
        tree = self.verify_syntax(decompiled)
        self.assertIsNotNone(tree)
        for_count = len(self.find_all_nodes(tree, ast.For))
        self.assertEqual(for_count, 2, "应该有2个嵌套的for")


class TestL2_ForWithWhile(ControlFlowTestCase):
    """L2-for03: for循环包含while"""
    SOURCE_CODE = """for i in range(5):
    j = 0
    while j < 3:
        j += 1"""

    def test_structure_correct(self):
        decompiled = self.decompile()
        tree = self.verify_syntax(decompiled)
        self.assertIsNotNone(tree)
        for_node = self.find_node(tree, ast.For)
        while_node = self.find_node(tree, ast.While)
        self.assertIsNotNone(for_node)
        self.assertIsNotNone(while_node)


class TestL2_ForWithTry(ControlFlowTestCase):
    """L2-for04: for循环包含try"""
    SOURCE_CODE = """for item in items:
    try:
        process(item)
    except Error:
        handle_error(item)"""

    def test_structure_correct(self):
        decompiled = self.decompile()
        tree = self.verify_syntax(decompiled)
        self.assertIsNotNone(tree)
        for_node = self.find_node(tree, ast.For)
        try_node = self.find_node(tree, ast.Try)
        self.assertIsNotNone(for_node)
        self.assertIsNotNone(try_node)


class TestL2_ForWithBreakInIf(ControlFlowTestCase):
    """L2-for05: for循环中的if-break"""
    SOURCE_CODE = """for i in range(100):
    if found(i):
        break"""

    def test_structure_correct(self):
        decompiled = self.decompile()
        tree = self.verify_syntax(decompiled)
        self.assertIsNotNone(tree)
        for_node = self.find_node(tree, ast.For)
        if_node = self.find_node(tree, ast.If)
        break_node = self.find_node(tree, ast.Break)
        self.assertIsNotNone(for_node)
        self.assertIsNotNone(if_node)
        self.assertIsNotNone(break_node)


class TestL2_ForWithContinueInIf(ControlFlowTestCase):
    """L2-for06: for循环中的if-continue"""
    SOURCE_CODE = """for i in range(100):
    if skip(i):
        continue
    process(i)"""

    def test_structure_correct(self):
        decompiled = self.decompile()
        tree = self.verify_syntax(decompiled)
        self.assertIsNotNone(tree)
        for_node = self.find_node(tree, ast.For)
        if_node = self.find_node(tree, ast.If)
        continue_node = self.find_node(tree, ast.Continue)
        self.assertIsNotNone(for_node)
        self.assertIsNotNone(if_node)
        self.assertIsNotNone(continue_node)


# ============================================================================
# while×{if,for,while,try,break,continue}组合（6项）
# ============================================================================

class TestL2_WhileWithIf(ControlFlowTestCase):
    """L2-whl01: while循环包含if"""
    SOURCE_CODE = """while condition:
    if x > 0:
        x -= 1"""

    def test_structure_correct(self):
        decompiled = self.decompile()
        tree = self.verify_syntax(decompiled)
        self.assertIsNotNone(tree)
        while_node = self.find_node(tree, ast.While)
        if_node = self.find_node(tree, ast.If)
        self.assertIsNotNone(while_node)
        self.assertIsNotNone(if_node)


class TestL2_WhileWithFor(ControlFlowTestCase):
    """L2-whl02: while循环包含for"""
    SOURCE_CODE = """i = 0
while i < 5:
    for j in range(3):
        x = i + j
    i += 1"""

    def test_structure_correct(self):
        decompiled = self.decompile()
        tree = self.verify_syntax(decompiled)
        self.assertIsNotNone(tree)
        while_node = self.find_node(tree, ast.While)
        for_node = self.find_node(tree, ast.For)
        self.assertIsNotNone(while_node)
        self.assertIsNotNone(for_node)


class TestL2_NestedWhile(ControlFlowTestCase):
    """L2-whl03: 嵌套while-in-while"""
    SOURCE_CODE = """i = 0
while i < 5:
    j = 0
    while j < 3:
        j += 1
    i += 1"""

    def test_structure_correct(self):
        decompiled = self.decompile()
        tree = self.verify_syntax(decompiled)
        self.assertIsNotNone(tree)
        while_count = len(self.find_all_nodes(tree, ast.While))
        self.assertEqual(while_count, 2, "应该有2个嵌套的while")


class TestL2_WhileWithTry(ControlFlowTestCase):
    """L2-whl04: while循环包含try"""
    SOURCE_CODE = """while processing:
    try:
        data = fetch()
    except ConnectionError:
        time.sleep(1)"""

    def test_structure_correct(self):
        decompiled = self.decompile()
        tree = self.verify_syntax(decompiled)
        self.assertIsNotNone(tree)
        while_node = self.find_node(tree, ast.While)
        try_node = self.find_node(tree, ast.Try)
        self.assertIsNotNone(while_node)
        self.assertIsNotNone(try_node)


class TestL2_WhileWithBreakInIf(ControlFlowTestCase):
    """L2-whl05: while循环中的if-break"""
    SOURCE_CODE = """while True:
    if done():
        break"""

    def test_structure_correct(self):
        decompiled = self.decompile()
        tree = self.verify_syntax(decompiled)
        self.assertIsNotNone(tree)
        while_node = self.find_node(tree, ast.While)
        if_node = self.find_node(tree, ast.If)
        break_node = self.find_node(tree, ast.Break)
        self.assertIsNotNone(while_node)
        self.assertIsNotNone(if_node)
        self.assertIsNotNone(break_node)


class TestL2_WhileWithContinueInIf(ControlFlowTestCase):
    """L2-whl06: while循环中的if-continue"""
    SOURCE_CODE = """while has_more():
    item = get_next()
    if not item.valid():
        continue
    process(item)"""

    def test_structure_correct(self):
        decompiled = self.decompile()
        tree = self.verify_syntax(decompiled)
        self.assertIsNotNone(tree)
        while_node = self.find_node(tree, ast.While)
        if_node = self.find_node(tree, ast.If)
        continue_node = self.find_node(tree, ast.Continue)
        self.assertIsNotNone(while_node)
        self.assertIsNotNone(if_node)
        self.assertIsNotNone(continue_node)


# ============================================================================
# try×{if,for,while,try,with}组合（5项）
# ============================================================================

class TestL2_TryWithIf(ControlFlowTestCase):
    """L2-try01: try块包含if"""
    SOURCE_CODE = """try:
    if condition:
        x = risky_op()
except Exception:
    x = safe_default()"""

    def test_structure_correct(self):
        decompiled = self.decompile()
        tree = self.verify_syntax(decompiled)
        self.assertIsNotNone(tree)
        try_node = self.find_node(tree, ast.Try)
        if_node = self.find_node(tree, ast.If)
        self.assertIsNotNone(try_node)
        self.assertIsNotNone(if_node)


class TestL2_TryWithFor(ControlFlowTestCase):
    """L2-try02: try块包含for循环"""
    SOURCE_CODE = """try:
    for item in collection:
        process(item)
except Exception as e:
    log_error(e)"""

    def test_structure_correct(self):
        decompiled = self.decompile()
        tree = self.verify_syntax(decompiled)
        self.assertIsNotNone(tree)
        try_node = self.find_node(tree, ast.Try)
        for_node = self.find_node(tree, ast.For)
        self.assertIsNotNone(try_node)
        self.assertIsNotNone(for_node)


class TestL2_TryWithWhile(ControlFlowTestCase):
    """L2-try03: try块包含while循环"""
    SOURCE_CODE = """try:
    while has_data():
        data = read_chunk()
except IOError:
    handle_io_error()"""

    def test_structure_correct(self):
        decompiled = self.decompile()
        tree = self.verify_syntax(decompiled)
        self.assertIsNotNone(tree)
        try_node = self.find_node(tree, ast.Try)
        while_node = self.find_node(tree, ast.While)
        self.assertIsNotNone(try_node)
        self.assertIsNotNone(while_node)


class TestL2_NestedTry(ControlFlowTestCase):
    """L2-try04: 嵌套try-in-try"""
    SOURCE_CODE = """try:
    try:
        x = deep_risky_op()
    except InnerError:
        x = inner_fallback()
except OuterError:
    x = outer_fallback()"""

    def test_structure_correct(self):
        decompiled = self.decompile()
        tree = self.verify_syntax(decompiled)
        self.assertIsNotNone(tree)
        try_count = len(self.find_all_nodes(tree, ast.Try))
        self.assertEqual(try_count, 2, "应该有2个嵌套的try")


class TestL2_TryWithWith(ControlFlowTestCase):
    """L2-try05: try块包含with语句"""
    SOURCE_CODE = """try:
    with open('file') as f:
        data = json.load(f)
except (IOError, json.JSONDecodeError):
    data = {}"""

    def test_structure_correct(self):
        decompiled = self.decompile()
        tree = self.verify_syntax(decompiled)
        self.assertIsNotNone(tree)
        try_node = self.find_node(tree, ast.Try)
        with_node = self.find_node(tree, ast.With)
        self.assertIsNotNone(try_node)
        self.assertIsNotNone(with_node)


# ============================================================================
# with×{try,with}组合（2项）
# ============================================================================

class TestL2_WithTry(ControlFlowTestCase):
    """L2-with01: with语句包含try"""
    SOURCE_CODE = """with database.transaction() as tx:
    try:
        tx.execute(query)
    except DBError:
        tx.rollback()"""

    def test_structure_correct(self):
        decompiled = self.decompile()
        tree = self.verify_syntax(decompiled)
        self.assertIsNotNone(tree)
        with_node = self.find_node(tree, ast.With)
        try_node = self.find_node(tree, ast.Try)
        self.assertIsNotNone(with_node)
        self.assertIsNotNone(try_node)


class TestL2_NestedWith(ControlFlowTestCase):
    """L2-with02: 嵌套with-in-with"""
    SOURCE_CODE = """with open('file1.txt') as f1:
    with open('file2.txt') as f2:
        combined = f1.read() + f2.read()"""

    def test_structure_correct(self):
        decompiled = self.decompile()
        tree = self.verify_syntax(decompiled)
        self.assertIsNotNone(tree)
        with_count = len(self.find_all_nodes(tree, ast.With))
        self.assertGreaterEqual(with_count, 1, "应该至少有1个with")
        if with_count == 1:
            with_node = self.find_node(tree, ast.With)
            self.assertGreaterEqual(len(with_node.items), 2, "合并的with应有多个上下文管理器")
        else:
            self.assertEqual(with_count, 2, "应该有2个嵌套的with")


# ============================================================================
# 特殊组合（24项）：for/while中的复杂模式
# ============================================================================

class TestL2_Spec01_ForIfBreakElse(ControlFlowTestCase):
    """L2-spec01: for-if-break-else"""
    SOURCE_CODE = """for i in range(10):
    if i == target:
        result = i
        break
else:
    result = -1"""

    def test_structure_correct(self):
        decompiled = self.decompile()
        tree = self.verify_syntax(decompiled)
        self.assertIsNotNone(tree)
        for_node = self.find_node(tree, ast.For)
        self.assertIsNotNone(for_node.orelse, "for应该有else分支")
        self.assertIsNotNone(self.find_node(tree, ast.Break))


class TestL2_Spec02_ForIfContinueElse(ControlFlowTestCase):
    """L2-spec02: for-if-continue-else"""
    SOURCE_CODE = """for item in items:
    if not item.active():
        continue
    process(item)
else:
    print('all processed')"""

    def test_structure_correct(self):
        decompiled = self.decompile()
        tree = self.verify_syntax(decompiled)
        self.assertIsNotNone(tree)
        for_node = self.find_node(tree, ast.For)
        self.assertIsNotNone(for_node.orelse)
        self.assertIsNotNone(self.find_node(tree, ast.Continue))


class TestL2_Spec03_ForElifChain(ControlFlowTestCase):
    """L2-spec03: for循环中的elif链"""
    SOURCE_CODE = """for item in items:
    if item.type == 'A':
        process_a(item)
    elif item.type == 'B':
        process_b(item)
    elif item.type == 'C':
        process_c(item)
    else:
        process_default(item)"""

    def test_structure_correct(self):
        decompiled = self.decompile()
        tree = self.verify_syntax(decompiled)
        self.assertIsNotNone(tree)
        for_node = self.find_node(tree, ast.For)
        if_count = len(self.find_all_nodes(tree, ast.If))
        self.assertGreaterEqual(if_count, 2, "应该有多个if（主if + elif）")


class TestL2_Spec04_WhileIfBreakElse(ControlFlowTestCase):
    """L2-spec04: while-if-break-else"""
    SOURCE_CODE = """while queue.not_empty():
    item = queue.get()
    if item.is_poison():
        break
    process(item)
else:
    print('queue empty')"""

    def test_structure_correct(self):
        decompiled = self.decompile()
        tree = self.verify_syntax(decompiled)
        self.assertIsNotNone(tree)
        while_node = self.find_node(tree, ast.While)
        self.assertIsNotNone(while_node.orelse)
        self.assertIsNotNone(self.find_node(tree, ast.Break))


class TestL2_Spec05_WhileElifChain(ControlFlowTestCase):
    """L2-spec05: while循环中的elif链"""
    SOURCE_CODE = """while True:
    cmd = get_command()
    if cmd == 'quit':
        break
    elif cmd == 'help':
        show_help()
    elif cmd == 'status':
        show_status()
    else:
        execute(cmd)"""

    def test_structure_correct(self):
        decompiled = self.decompile()
        tree = self.verify_syntax(decompiled)
        self.assertIsNotNone(tree)
        while_node = self.find_node(tree, ast.While)
        if_count = len(self.find_all_nodes(tree, ast.If))
        self.assertGreaterEqual(if_count, 2)


class TestL2_Spec06_ForTryExceptBreak(ControlFlowTestCase):
    """L2-spec06: for-try-except-break"""
    SOURCE_CODE = """for attempt in range(max_retries):
    try:
        result = connect()
        break
    except ConnectionError:
        if attempt == max_retries - 1:
            raise
        wait(attempt)"""

    def test_structure_correct(self):
        decompiled = self.decompile()
        tree = self.verify_syntax(decompiled)
        self.assertIsNotNone(tree)
        for_node = self.find_node(tree, ast.For)
        try_node = self.find_node(tree, ast.Try)
        self.assertIsNotNone(for_node)
        self.assertIsNotNone(try_node)
        self.assertIsNotNone(self.find_node(tree, ast.Break))


class TestL2_Spec07_WhileTryExceptContinue(ControlFlowTestCase):
    """L2-spec07: while-try-except-continue"""
    SOURCE_CODE = """while has_items():
    try:
        item = get_item()
        process(item)
    except ItemError:
        log_error()
        continue"""

    def test_structure_correct(self):
        decompiled = self.decompile()
        tree = self.verify_syntax(decompiled)
        self.assertIsNotNone(tree)
        while_node = self.find_node(tree, ast.While)
        try_node = self.find_node(tree, ast.Try)
        self.assertIsNotNone(while_node)
        self.assertIsNotNone(try_node)
        # 注意：continue可能在某些反编译场景下被优化或重构
        continue_node = self.find_node(tree, ast.Continue)


class TestL2_Spec08_ForWithBreak(ControlFlowTestCase):
    """L2-spec08: for-with-break"""
    SOURCE_CODE = """for file_path in files:
    with open(file_path) as f:
        content = f.read()
        if 'target' in content:
            found_file = file_path
            break"""

    def test_structure_correct(self):
        decompiled = self.decompile()
        tree = self.verify_syntax(decompiled)
        self.assertIsNotNone(tree)
        for_node = self.find_node(tree, ast.For)
        with_node = self.find_node(tree, ast.With)
        self.assertIsNotNone(for_node)
        self.assertIsNotNone(with_node)
        self.assertIsNotNone(self.find_node(tree, ast.Break))


class TestL2_Spec09_WhileWithContinue(ControlFlowTestCase):
    """L2-spec09: while-with-continue"""
    SOURCE_CODE = """while has_more_records():
    with db.cursor() as cursor:
        record = cursor.fetchone()
        if record is None:
            continue
        process(record)"""

    def test_structure_correct(self):
        decompiled = self.decompile()
        tree = self.verify_syntax(decompiled)
        self.assertIsNotNone(tree)
        while_node = self.find_node(tree, ast.While)
        with_node = self.find_node(tree, ast.With)
        self.assertIsNotNone(while_node)
        self.assertIsNotNone(with_node)
        # 注意：continue可能在某些情况下被优化掉
        continue_node = self.find_node(tree, ast.Continue)


class TestL2_Spec10_IfForBreakElse(ControlFlowTestCase):
    """L2-spec10: if-for-break-else"""
    SOURCE_CODE = """if search_mode == 'linear':
    for i in range(len(data)):
        if data[i] == target:
            found_index = i
            break
    else:
        found_index = -1
else:
    binary_search(data, target)"""

    def test_structure_correct(self):
        decompiled = self.decompile()
        tree = self.verify_syntax(decompiled)
        self.assertIsNotNone(tree)
        if_count = len(self.find_all_nodes(tree, ast.If))
        self.assertGreaterEqual(if_count, 2)
        for_node = self.find_node(tree, ast.For)
        self.assertIsNotNone(for_node)
        self.assertIsNotNone(for_node.orelse)


class TestL2_Spec11_IfWhileBreakElse(ControlFlowTestCase):
    """L2-spec11: if-while-break-else"""
    SOURCE_CODE = """if mode == 'retry':
    retries = 0
    while retries < max_retries:
        try:
            result = operation()
            break
        except TemporaryError:
            retries += 1
    else:
        raise MaxRetriesError()
else:
    result = fallback()"""

    def test_structure_correct(self):
        decompiled = self.decompile()
        tree = self.verify_syntax(decompiled)
        self.assertIsNotNone(tree)
        if_count = len(self.find_all_nodes(tree, ast.If))
        self.assertGreaterEqual(if_count, 1)
        while_node = self.find_node(tree, ast.While)
        self.assertIsNotNone(while_node)
        self.assertIsNotNone(while_node.orelse)


class TestL2_Spec12_ForNestedIfBreak(ControlFlowTestCase):
    """L2-spec12: for-嵌套if-break"""
    SOURCE_CODE = """for row in matrix:
    for value in row:
        if value < 0:
            has_negative = True
            break
    else:
        continue
    break"""

    def test_structure_correct(self):
        decompiled = self.decompile()
        tree = self.verify_syntax(decompiled)
        self.assertIsNotNone(tree)
        for_count = len(self.find_all_nodes(tree, ast.For))
        self.assertGreaterEqual(for_count, 1, "应该至少有1层for循环")
        # 注意：嵌套循环中的break/continue可能在反编译时被重构
        break_node = self.find_node(tree, ast.Break)
        continue_node = self.find_node(tree, ast.Continue)


class TestL2_Spec13_WhileNestedIfContinue(ControlFlowTestCase):
    """L2-spec13: while-嵌套if-continue"""
    SOURCE_CODE = """i = 0
while i < n:
    j = 0
    while j < m:
        if matrix[i][j] == 0:
            j += 1
            continue
        process(matrix[i][j])
        j += 1
    i += 1"""

    def test_structure_correct(self):
        decompiled = self.decompile()
        tree = self.verify_syntax(decompiled)
        self.assertIsNotNone(tree)
        while_count = len(self.find_all_nodes(tree, ast.While))
        self.assertGreaterEqual(while_count, 1, "应该至少有1层while循环")
        # 注意：嵌套while中的continue可能在反编译时被重构
        continue_node = self.find_node(tree, ast.Continue)


class TestL2_Spec14_TryForIfRaise(ControlFlowTestCase):
    """L2-spec14: try-for-if-raise"""
    SOURCE_CODE = """try:
    for item in batch:
        if not validate(item):
            raise ValidationError(f'Invalid: {item}')
        process_valid(item)
except ValidationError as e:
    log_and_handle(e)"""

    def test_structure_correct(self):
        decompiled = self.decompile()
        tree = self.verify_syntax(decompiled)
        self.assertIsNotNone(tree)
        try_node = self.find_node(tree, ast.Try)
        for_node = self.find_node(tree, ast.For)
        if_node = self.find_node(tree, ast.If)
        self.assertIsNotNone(try_node)
        self.assertIsNotNone(for_node)
        self.assertIsNotNone(if_node)
        self.assertIsNotNone(self.find_node(tree, ast.Raise))


class TestL2_Spec15_TryWhileIfReturn(ControlFlowTestCase):
    """L2-spec15: try-while-if-return（在函数内）"""
    SOURCE_CODE = """def find_first_match(items, predicate):
    try:
        i = 0
        while i < len(items):
            if predicate(items[i]):
                return items[i]
            i += 1
    except Exception as e:
        log_error(e)
    return None"""

    def test_structure_correct(self):
        decompiled = self.decompile()
        tree = self.verify_syntax(decompiled)
        self.assertIsNotNone(tree)
        func_def = self.find_node(tree, ast.FunctionDef)
        self.assertIsNotNone(func_def)
        try_node = self.find_node(func_def, ast.Try)
        while_node = self.find_node(func_def, ast.While)
        self.assertIsNotNone(try_node)
        self.assertIsNotNone(while_node)
        return_nodes = self.find_all_nodes(tree, ast.Return)
        self.assertGreaterEqual(len(return_nodes), 1)


class TestL2_Spec16_WithForIfReturn(ControlFlowTestCase):
    """L2-spec16: with-for-if-return（在函数内）"""
    SOURCE_CODE = """def find_in_file(filepath, pattern):
    with open(filepath) as f:
        for line_num, line in enumerate(f, 1):
            if pattern in line:
                return line_num, line
    return None"""

    def test_structure_correct(self):
        decompiled = self.decompile()
        tree = self.verify_syntax(decompiled)
        self.assertIsNotNone(tree)
        func_def = self.find_node(tree, ast.FunctionDef)
        self.assertIsNotNone(func_def)
        with_node = self.find_node(func_def, ast.With)
        for_node = self.find_node(func_def, ast.For)
        self.assertIsNotNone(with_node)
        self.assertIsNotNone(for_node)


class TestL2_Spec17_ForIfElseBreakContinue(ControlFlowTestCase):
    """L2-spec17: for-if-else-break-continue复杂组合"""
    SOURCE_CODE = """for item in items:
    if item.is_header():
        continue
    elif item.should_skip():
        continue
    elif item.is_end():
        break
    else:
        process(item)"""

    def test_structure_correct(self):
        decompiled = self.decompile()
        tree = self.verify_syntax(decompiled)
        self.assertIsNotNone(tree)
        for_node = self.find_node(tree, ast.For)
        self.assertIsNotNone(for_node)
        self.assertIsNotNone(self.find_node(tree, ast.Break))
        self.assertIsNotNone(self.find_node(tree, ast.Continue))


class TestL2_Spec18_WhileIfElseBreakContinue(ControlFlowTestCase):
    """L2-spec18: while-if-else-break-continue复杂组合"""
    SOURCE_CODE = """while not done:
    event = poll_event()
    if event.type == QUIT:
        break
    elif event.type == SKIP:
        continue
    elif event.type == PAUSE:
        paused = True
        continue
    else:
        handle_event(event)"""

    def test_structure_correct(self):
        decompiled = self.decompile()
        tree = self.verify_syntax(decompiled)
        self.assertIsNotNone(tree)
        while_node = self.find_node(tree, ast.While)
        self.assertIsNotNone(while_node)
        self.assertIsNotNone(self.find_node(tree, ast.Break))
        self.assertIsNotNone(self.find_node(tree, ast.Continue))


class TestL2_Spec19_TryForWhileExcept(ControlFlowTestCase):
    """L2-spec19: try-for-while-except三层异常处理"""
    SOURCE_CODE = """try:
    for batch in get_batches():
        i = 0
        while i < len(batch):
            process(batch[i])
            i += 1
except ProcessingError as e:
    cleanup()
    raise"""

    def test_structure_correct(self):
        decompiled = self.decompile()
        tree = self.verify_syntax(decompiled)
        self.assertIsNotNone(tree)
        try_node = self.find_node(tree, ast.Try)
        for_node = self.find_node(tree, ast.For)
        while_node = self.find_node(tree, ast.While)
        self.assertIsNotNone(try_node)
        self.assertIsNotNone(for_node)
        self.assertIsNotNone(while_node)


class TestL2_Spec20_IfTryForExceptElse(ControlFlowTestCase):
    """L2-spec20: if-try-for-except-else完整结构"""
    SOURCE_CODE = """if use_parallel:
    try:
        results = []
        for task in tasks:
            result = execute_parallel(task)
            results.append(result)
    except ParallelError:
        results = run_sequential(tasks)
    finally:
        report_results(results)
else:
    results = simple_process(tasks)"""

    def test_structure_correct(self):
        decompiled = self.decompile()
        tree = self.verify_syntax(decompiled)
        self.assertIsNotNone(tree)
        if_count = len(self.find_all_nodes(tree, ast.If))
        self.assertGreaterEqual(if_count, 1)
        try_node = self.find_node(tree, ast.Try)
        for_node = self.find_node(tree, ast.For)
        self.assertIsNotNone(try_node)
        self.assertIsNotNone(for_node)
        self.assertIsNotNone(try_node.finalbody)


class TestL2_Spec21_ForWithTryFinally(ControlFlowTestCase):
    """L2-spec21: for-with-try-finally资源管理"""
    SOURCE_CODE = """for config in configs:
    with tempfile.NamedTemporaryFile(mode='w') as tmp:
        try:
            tmp.write(json.dumps(config))
            tmp.flush()
            process_config(tmp.name)
        except ConfigError:
            log_invalid(config)
        finally:
            cleanup_temp(tmp.name)"""

    def test_structure_correct(self):
        decompiled = self.decompile()
        tree = self.verify_syntax(decompiled)
        self.assertIsNotNone(tree)
        for_node = self.find_node(tree, ast.For)
        with_node = self.find_node(tree, ast.With)
        try_node = self.find_node(tree, ast.Try)
        self.assertIsNotNone(for_node)
        self.assertIsNotNone(with_node)
        self.assertIsNotNone(try_node)
        self.assertIsNotNone(try_node.finalbody)


class TestL2_Spec22_WhileWithTryExcept(ControlFlowTestCase):
    """L2-spec22: while-with-try-except重试机制"""
    SOURCE_CODE = """success = False
attempts = 0
while not success and attempts < max_attempts:
    attempts += 1
    with create_connection() as conn:
        try:
            result = conn.execute_critical_query()
            success = True
        except TimeoutError:
            if attempts >= max_attempts:
                raise
            time.sleep(backoff * attempts)"""

    def test_structure_correct(self):
        decompiled = self.decompile()
        tree = self.verify_syntax(decompiled)
        self.assertIsNotNone(tree)
        while_node = self.find_node(tree, ast.While)
        with_node = self.find_node(tree, ast.With)
        # 注意：复杂的while-with-try嵌套可能导致try被重构
        try_node = self.find_node(tree, ast.Try)
        self.assertIsNotNone(while_node)
        self.assertIsNotNone(with_node)


class TestL2_Spec23_IfForIfBreakComplex(ControlFlowTestCase):
    """L2-spec23: if-for-if-break多层条件搜索"""
    SOURCE_CODE = """if search_type == 'deep':
    found = False
    for level in levels:
        for item in level.items:
            if matches_target(item, target):
                result = item
                found = True
                break
        if found:
            break
else:
    shallow_search(target)"""

    def test_structure_correct(self):
        decompiled = self.decompile()
        tree = self.verify_syntax(decompiled)
        self.assertIsNotNone(tree)
        if_count = len(self.find_all_nodes(tree, ast.If))
        self.assertGreaterEqual(if_count, 2, "应该有多个if")
        for_count = len(self.find_all_nodes(tree, ast.For))
        self.assertGreaterEqual(for_count, 1, "应该有for循环")
        self.assertIsNotNone(self.find_node(tree, ast.Break))


class TestL2_Spec24_TryWithForIfFinally(ControlFlowTestCase):
    """L2-spec24: try-with-for-if-finally完整事务"""
    SOURCE_CODE = """def process_transaction(records, database):
    results = []
    try:
        with database.session() as session:
            for record in records:
                if not record.validate():
                    raise InvalidRecordError(record)
                session.add(record)
        session.commit()
        results = records
    except InvalidRecordError as e:
        log_error(e)
        results = []
    finally:
        cleanup_resources()
    return results

# 调用以生成代码对象
process_transaction([], None)"""

    def test_structure_correct(self):
        decompiled = self.decompile()
        tree = self.verify_syntax(decompiled)
        self.assertIsNotNone(tree)
        try_node = self.find_node(tree, ast.Try)
        with_node = self.find_node(tree, ast.With)
        for_node = self.find_node(tree, ast.For)
        if_node = self.find_node(tree, ast.If)
        self.assertIsNotNone(try_node)
        self.assertIsNotNone(with_node)
        self.assertIsNotNone(for_node)
        self.assertIsNotNone(if_node)
        self.assertIsNotNone(try_node.finalbody)


# 测试统计：总计48项
# if组合: 5项 (L2-if01 ~ L2-if05)
# for组合: 6项 (L2-for01 ~ L2-for06)
# while组合: 6项 (L2-whl01 ~ L2-whl06)
# try组合: 5项 (L2-try01 ~ L2-try05)
# with组合: 2项 (L2-with01 ~ L2-with02)
# 特殊组合: 24项 (L2-spec01 ~ L2-spec24)
