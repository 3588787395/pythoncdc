"""
L2两层嵌套测试用例 (48项)

覆盖Python控制流的两层嵌套组合矩阵：
- 外层×内层组合：if/for/while/try/with × if/for/while/try/with/break/continue
- 特殊组合：循环中条件性break/continue等

总计: 48项测试
"""

import ast
from tests.control_flow_matrix.base import ControlFlowTestCase


# ============================================================================
# 第一组: IF外层 (5项) - if > {for, while, try, with, if}
# ============================================================================

class TestL2_001_IfContainsFor(ControlFlowTestCase):
    """L2_001: if > for"""
    SOURCE_CODE = """if cond:
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


class TestL2_002_IfContainsWhile(ControlFlowTestCase):
    """L2_002: if > while"""
    SOURCE_CODE = """if cond:
    while x > 0:
        x -= 1"""

    def test_structure_correct(self):
        decompiled = self.decompile()
        tree = self.verify_syntax(decompiled)
        self.assertIsNotNone(tree)
        if_node = self.find_node(tree, ast.If)
        while_node = self.find_node(tree, ast.While)
        self.assertIsNotNone(if_node)
        self.assertIsNotNone(while_node)


class TestL2_003_IfContainsTry(ControlFlowTestCase):
    """L2_003: if > try"""
    SOURCE_CODE = """if cond:
    try:
        risky()
    except Error:
        handle()"""

    def test_structure_correct(self):
        decompiled = self.decompile()
        tree = self.verify_syntax(decompiled)
        self.assertIsNotNone(tree)
        if_node = self.find_node(tree, ast.If)
        try_node = self.find_node(tree, ast.Try)
        self.assertIsNotNone(if_node)
        self.assertIsNotNone(try_node)


class TestL2_004_IfContainsWith(ControlFlowTestCase):
    """L2_004: if > with"""
    SOURCE_CODE = """if cond:
    with lock:
        critical()"""

    def test_structure_correct(self):
        decompiled = self.decompile()
        tree = self.verify_syntax(decompiled)
        self.assertIsNotNone(tree)
        if_node = self.find_node(tree, ast.If)
        with_node = self.find_node(tree, ast.With)
        self.assertIsNotNone(if_node)
        self.assertIsNotNone(with_node)


class TestL2_005_IfContainsIf(ControlFlowTestCase):
    """L2_005: if > if (嵌套if)"""
    SOURCE_CODE = """if cond1:
    if cond2:
        x = 1"""

    def test_structure_correct(self):
        decompiled = self.decompile()
        tree = self.verify_syntax(decompiled)
        self.assertIsNotNone(tree)
        if_count = len(self.find_all_nodes(tree, ast.If))
        self.assertGreaterEqual(if_count, 2, "应该有2个嵌套的if")


# ============================================================================
# 第二组: FOR外层 (6项) - for > {if, for, while, try, break, continue}
# ============================================================================

class TestL2_006_ForContainsIf(ControlFlowTestCase):
    """L2_006: for > if"""
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


class TestL2_007_ForContainsFor(ControlFlowTestCase):
    """L2_007: for > for (嵌套for)"""
    SOURCE_CODE = """for i in range(5):
    for j in range(5):
        x = i * j"""

    def test_structure_correct(self):
        decompiled = self.decompile()
        tree = self.verify_syntax(decompiled)
        self.assertIsNotNone(tree)
        for_count = len(self.find_all_nodes(tree, ast.For))
        self.assertEqual(for_count, 2, "应该有2个嵌套for")


class TestL2_008_ForContainsWhile(ControlFlowTestCase):
    """L2_008: for > while"""
    SOURCE_CODE = """for i in range(5):
    j = 0
    while j < 5:
        j += 1"""

    def test_structure_correct(self):
        decompiled = self.decompile()
        tree = self.verify_syntax(decompiled)
        self.assertIsNotNone(tree)
        for_node = self.find_node(tree, ast.For)
        while_node = self.find_node(tree, ast.While)
        self.assertIsNotNone(for_node)
        self.assertIsNotNone(while_node)


class TestL2_009_ForContainsTry(ControlFlowTestCase):
    """L2_009: for > try"""
    SOURCE_CODE = """for i in range(10):
    try:
        process(i)
    except Error:
        log_error(i)"""

    def test_structure_correct(self):
        decompiled = self.decompile()
        tree = self.verify_syntax(decompiled)
        self.assertIsNotNone(tree)
        for_node = self.find_node(tree, ast.For)
        try_node = self.find_node(tree, ast.Try)
        self.assertIsNotNone(for_node)
        self.assertIsNotNone(try_node)


class TestL2_010_ForWithIfBreak(ControlFlowTestCase):
    """L2_010: for > if > break"""
    SOURCE_CODE = """for i in range(10):
    if i == 5:
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


class TestL2_011_ForWithIfContinue(ControlFlowTestCase):
    """L2_011: for > if > continue"""
    SOURCE_CODE = """for i in range(10):
    if i % 2 == 0:
        continue"""

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
# 第三组: WHILE外层 (6项) - while > {if, for, while, try, break, continue}
# ============================================================================

class TestL2_012_WhileContainsIf(ControlFlowTestCase):
    """L2_012: while > if"""
    SOURCE_CODE = """while cond:
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


class TestL2_013_WhileContainsFor(ControlFlowTestCase):
    """L2_013: while > for"""
    SOURCE_CODE = """while cond:
    for i in range(5):
        x = i"""

    def test_structure_correct(self):
        decompiled = self.decompile()
        tree = self.verify_syntax(decompiled)
        self.assertIsNotNone(tree)
        while_node = self.find_node(tree, ast.While)
        for_node = self.find_node(tree, ast.For)
        self.assertIsNotNone(while_node)
        self.assertIsNotNone(for_node)


class TestL2_014_WhileContainsWhile(ControlFlowTestCase):
    """L2_014: while > while (嵌套while)"""
    SOURCE_CODE = """i = 0
while i < 5:
    j = 0
    while j < 5:
        j += 1
    i += 1"""

    def test_structure_correct(self):
        decompiled = self.decompile()
        tree = self.verify_syntax(decompiled)
        self.assertIsNotNone(tree)
        while_count = len(self.find_all_nodes(tree, ast.While))
        self.assertEqual(while_count, 2, "应该有2个嵌套while")


class TestL2_015_WhileContainsTry(ControlFlowTestCase):
    """L2_015: while > try"""
    SOURCE_CODE = """while cond:
    try:
        operation()
    except Error:
        handle()"""

    def test_structure_correct(self):
        decompiled = self.decompile()
        tree = self.verify_syntax(decompiled)
        self.assertIsNotNone(tree)
        while_node = self.find_node(tree, ast.While)
        try_node = self.find_node(tree, ast.Try)
        self.assertIsNotNone(while_node)
        self.assertIsNotNone(try_node)


class TestL2_016_WhileWithIfBreak(ControlFlowTestCase):
    """L2_016: while > if > break"""
    SOURCE_CODE = """while True:
    if done:
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


class TestL2_017_WhileWithIfContinue(ControlFlowTestCase):
    """L2_017: while > if > continue"""
    SOURCE_CODE = """while cond:
    if skip:
        continue"""

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
# 第四组: TRY外层 (5项) - try > {if, for, while, try, with}
# ============================================================================

class TestL2_018_TryContainsIf(ControlFlowTestCase):
    """L2_018: try > if"""
    SOURCE_CODE = """try:
    if x > 0:
        raise ValueError()
except ValueError:
    pass"""

    def test_structure_correct(self):
        decompiled = self.decompile()
        tree = self.verify_syntax(decompiled)
        self.assertIsNotNone(tree)
        try_node = self.find_node(tree, ast.Try)
        if_node = self.find_node(tree, ast.If)
        self.assertIsNotNone(try_node)
        self.assertIsNotNone(if_node)


class TestL2_019_TryContainsFor(ControlFlowTestCase):
    """L2_019: try > for"""
    SOURCE_CODE = """try:
    for i in range(10):
        process(i)
except Error:
    pass"""

    def test_structure_correct(self):
        decompiled = self.decompile()
        tree = self.verify_syntax(decompiled)
        self.assertIsNotNone(tree)
        try_node = self.find_node(tree, ast.Try)
        for_node = self.find_node(tree, ast.For)
        self.assertIsNotNone(try_node)
        self.assertIsNotNone(for_node)


class TestL2_020_TryContainsWhile(ControlFlowTestCase):
    """L2_020: try > while"""
    SOURCE_CODE = """try:
    while not done():
        step()
except StopIteration:
    pass"""

    def test_structure_correct(self):
        decompiled = self.decompile()
        tree = self.verify_syntax(decompiled)
        self.assertIsNotNone(tree)
        try_node = self.find_node(tree, ast.Try)
        while_node = self.find_node(tree, ast.While)
        self.assertIsNotNone(try_node)
        self.assertIsNotNone(while_node)


class TestL2_021_TryContainsTry(ControlFlowTestCase):
    """L2_021: try > try (嵌套try)"""
    SOURCE_CODE = """try:
    try:
        inner_op()
    except InnerError:
        pass
except OuterError:
    pass"""

    def test_structure_correct(self):
        decompiled = self.decompile()
        tree = self.verify_syntax(decompiled)
        self.assertIsNotNone(tree)
        try_count = len(self.find_all_nodes(tree, ast.Try))
        self.assertGreaterEqual(try_count, 2, "应该有2个嵌套try")


class TestL2_022_TryContainsWith(ControlFlowTestCase):
    """L2_022: try > with"""
    SOURCE_CODE = """try:
    with open('file') as f:
        data = f.read()
except IOError:
    data = ''"""

    def test_structure_correct(self):
        decompiled = self.decompile()
        tree = self.verify_syntax(decompiled)
        self.assertIsNotNone(tree)
        try_node = self.find_node(tree, ast.Try)
        with_node = self.find_node(tree, ast.With)
        self.assertIsNotNone(try_node)
        self.assertIsNotNone(with_node)


# ============================================================================
# 第五组: WITH外层 (2项) - with > {try, with}
# ============================================================================

class TestL2_023_WithContainsTry(ControlFlowTestCase):
    """L2_023: with > try"""
    SOURCE_CODE = """with resource():
    try:
        operation()
    except Error:
        handle()"""

    def test_structure_correct(self):
        decompiled = self.decompile()
        tree = self.verify_syntax(decompiled)
        self.assertIsNotNone(tree)
        with_node = self.find_node(tree, ast.With)
        try_node = self.find_node(tree, ast.Try)
        self.assertIsNotNone(with_node)
        self.assertIsNotNone(try_node)


class TestL2_024_WithContainsWith(ControlFlowTestCase):
    """L2_024: with > with (嵌套with)"""
    SOURCE_CODE = """with open('f1.txt') as f1:
    with open('f2.txt') as f2:
        combined = f1.read() + f2.read()"""

    def test_structure_correct(self):
        decompiled = self.decompile()
        tree = self.verify_syntax(decompiled)
        self.assertIsNotNone(tree)
        with_count = len(self.find_all_nodes(tree, ast.With))
        self.assertGreaterEqual(with_count, 1, "应该有with语句")


# ============================================================================
# 第六组: 特殊组合 - FOR中IF+Break/Continue (6项)
# ============================================================================

class TestL2_025_ForIfBreakSimple(ControlFlowTestCase):
    """L2_025: for + if + break (简单条件)"""
    SOURCE_CODE = """for i in range(100):
    if i == 50:
        break"""

    def test_structure_correct(self):
        decompiled = self.decompile()
        tree = self.verify_syntax(decompiled)
        self.assertIsNotNone(tree)
        self.assertIsNotNone(self.find_node(tree, ast.Break))


class TestL2_026_ForIfBreakComplexCondition(ControlFlowTestCase):
    """L2_026: for + if(break) 复杂条件"""
    SOURCE_CODE = """for item in items:
    if item.priority == 'critical' and item.status == 'pending':
        process_critical(item)
        break"""

    def test_structure_correct(self):
        decompiled = self.decompile()
        tree = self.verify_syntax(decompiled)
        self.assertIsNotNone(tree)
        self.assertIsNotNone(self.find_node(tree, ast.Break))


class TestL2_027_ForIfBreakInElseBranch(ControlFlowTestCase):
    """L2_027: for + if-else + break在else中"""
    SOURCE_CODE = """for i in range(100):
    if found_match(i):
        process(i)
    else:
        if no_more_candidates():
            break"""

    def test_structure_correct(self):
        decompiled = self.decompile()
        tree = self.verify_syntax(decompiled)
        self.assertIsNotNone(tree)
        self.assertIsNotNone(self.find_node(tree, ast.Break))


class TestL2_028_ForIfContinueSimple(ControlFlowTestCase):
    """L2_028: for + if + continue (简单条件)"""
    SOURCE_CODE = """for i in range(100):
    if i % 2 == 0:
        continue
    print(i)"""

    def test_structure_correct(self):
        decompiled = self.decompile()
        tree = self.verify_syntax(decompiled)
        self.assertIsNotNone(tree)
        self.assertIsNotNone(self.find_node(tree, ast.Continue))


class TestL2_029_ForIfContinueComplexCondition(ControlFlowTestCase):
    """L2_029: for + if(continue) 复杂条件"""
    SOURCE_CODE = """for item in queue:
    if not item.is_valid() or item.is_duplicate():
        continue
    process_valid_item(item)"""

    def test_structure_correct(self):
        decompiled = self.decompile()
        tree = self.verify_syntax(decompiled)
        self.assertIsNotNone(tree)
        self.assertIsNotNone(self.find_node(tree, ast.Continue))


class TestL2_030_ForIfBothBreakAndContinue(ControlFlowTestCase):
    """L2_030: for + if(break) + if(continue) 组合"""
    SOURCE_CODE = """for i in range(1000):
    if should_skip(i):
        continue
    if should_stop(i):
        break
    process(i)"""

    def test_structure_correct(self):
        decompiled = self.decompile()
        tree = self.verify_syntax(decompiled)
        self.assertIsNotNone(tree)
        self.assertIsNotNone(self.find_node(tree, ast.Break))
        self.assertIsNotNone(self.find_node(tree, ast.Continue))


# ============================================================================
# 第七组: 特殊组合 - WHILE中IF+Break/Continue (6项)
# ============================================================================

class TestL2_031_WhileIfBreakSimple(ControlFlowTestCase):
    """L2_031: while + if + break (简单条件)"""
    SOURCE_CODE = """while True:
    data = fetch_data()
    if data is None:
        break
    process(data)"""

    def test_structure_correct(self):
        decompiled = self.decompile()
        tree = self.verify_syntax(decompiled)
        self.assertIsNotNone(tree)
        self.assertIsNotNone(self.find_node(tree, ast.Break))


class TestL2_032_WhileIfBreakComplexCondition(ControlFlowTestCase):
    """L2_032: while + if(break) 复杂条件"""
    SOURCE_CODE = """while has_work():
    task = get_next_task()
    if task is None or task.cancelled:
        break
    execute(task)"""

    def test_structure_correct(self):
        decompiled = self.decompile()
        tree = self.verify_syntax(decompiled)
        self.assertIsNotNone(tree)
        self.assertIsNotNone(self.find_node(tree, ast.Break))


class TestL2_033_WhileIfBreakInNestedCondition(ControlFlowTestCase):
    """L2_033: while + 嵌套if + break"""
    SOURCE_CODE = """while processing:
    result = check_status()
    if result.success:
        if result.complete:
            break
        else:
            continue_processing()
    else:
        handle_error(result)"""

    def test_structure_correct(self):
        decompiled = self.decompile()
        tree = self.verify_syntax(decompiled)
        self.assertIsNotNone(tree)
        self.assertIsNotNone(self.find_node(tree, ast.Break))


class TestL2_034_WhileIfContinueSimple(ControlFlowTestCase):
    """L2_034: while + if + continue (简单条件)"""
    SOURCE_CODE = """while items_remain():
    item = get_next_item()
    if not item.is_relevant():
        continue
    process_item(item)"""

    def test_structure_correct(self):
        decompiled = self.decompile()
        tree = self.verify_syntax(decompiled)
        self.assertIsNotNone(tree)
        self.assertIsNotNone(self.find_node(tree, ast.Continue))


class TestL2_035_WhileIfContinueComplexCondition(ControlFlowTestCase):
    """L2_035: while + if(continue) 复杂条件"""
    SOURCE_CODE = """while not completed():
    event = wait_for_event()
    if event.type == 'timeout' and event.retriable:
        retry_count += 1
        continue
    handle_event(event)"""

    def test_structure_correct(self):
        decompiled = self.decompile()
        tree = self.verify_syntax(decompiled)
        self.assertIsNotNone(tree)
        self.assertIsNotNone(self.find_node(tree, ast.Continue))


class TestL2_036_WhileIfBothBreakAndContinue(ControlFlowTestCase):
    """L2_036: while + if(break) + if(continue) 组合"""
    SOURCE_CODE = """while True:
    line = read_line()
    if line is None:
        break
    if line.startswith('#'):
        continue
    parse_line(line)"""

    def test_structure_correct(self):
        decompiled = self.decompile()
        tree = self.verify_syntax(decompiled)
        self.assertIsNotNone(tree)
        self.assertIsNotNone(self.find_node(tree, ast.Break))
        self.assertIsNotNone(self.find_node(tree, ast.Continue))


# ============================================================================
# 第八组: 特殊组合 - IF中FOR/WHILE (6项)
# ============================================================================

class TestL2_037_IfThenFor(ControlFlowTestCase):
    """L2_037: if-then分支包含for"""
    SOURCE_CODE = """if mode == 'batch':
    for item in batch:
        process(item)
else:
    process_single(item)"""

    def test_structure_correct(self):
        decompiled = self.decompile()
        tree = self.verify_syntax(decompiled)
        self.assertIsNotNone(tree)
        if_node = self.find_node(tree, ast.If)
        for_node = self.find_node(tree, ast.For)
        self.assertIsNotNone(if_node)
        self.assertIsNotNone(for_node)


class TestL2_038_IfElseFor(ControlFlowTestCase):
    """L2_038: if-else分支包含for"""
    SOURCE_CODE = """if use_fast_path():
    fast_process()
else:
    for item in items:
        slow_process(item)"""

    def test_structure_correct(self):
        decompiled = self.decompile()
        tree = self.verify_syntax(decompiled)
        self.assertIsNotNone(tree)
        if_node = self.find_node(tree, ast.If)
        for_node = self.find_node(tree, ast.For)
        self.assertIsNotNone(if_node)
        self.assertIsNotNone(for_node)


class TestL2_039_IfElifForChain(ControlFlowTestCase):
    """L2_039: if-elif链中的多个for"""
    SOURCE_CODE = """if mode == 'fast':
    for item in fast_queue:
        process_fast(item)
elif mode == 'normal':
    for item in normal_queue:
        process_normal(item)
else:
    for item in slow_queue:
        process_slow(item)"""

    def test_structure_correct(self):
        decompiled = self.decompile()
        tree = self.verify_syntax(decompiled)
        self.assertIsNotNone(tree)
        for_count = len(self.find_all_nodes(tree, ast.For))
        self.assertGreaterEqual(for_count, 2, "应该有多个for循环")


class TestL2_040_IfThenWhile(ControlFlowTestCase):
    """L2_040: if-then分支包含while"""
    SOURCE_CODE = """if needs_retry():
    while attempts < max_attempts:
        attempt_operation()
        attempts += 1
        if success:
            break
else:
    give_up()"""

    def test_structure_correct(self):
        decompiled = self.decompile()
        tree = self.verify_syntax(decompiled)
        self.assertIsNotNone(tree)
        if_node = self.find_node(tree, ast.If)
        while_node = self.find_node(tree, ast.While)
        self.assertIsNotNone(if_node)
        self.assertIsNotNone(while_node)


class TestL2_041_IfElseWhile(ControlFlowTestCase):
    """L2_041: if-else分支包含while"""
    SOURCE_CODE = """if use_polling():
    while not ready():
        poll()
else:
    wait_for_callback()"""

    def test_structure_correct(self):
        decompiled = self.decompile()
        tree = self.verify_syntax(decompiled)
        self.assertIsNotNone(tree)
        if_node = self.find_node(tree, ast.If)
        while_node = self.find_node(tree, ast.While)
        self.assertIsNotNone(if_node)
        self.assertIsNotNone(while_node)


class TestL2_042_NestedIfWithLoopAndBreak(ControlFlowTestCase):
    """L2_042: 嵌套if中包含循环和break"""
    SOURCE_CODE = """if outer_cond:
    if inner_cond:
        for i in range(10):
            if target_found(i):
                result = i
                break
    else:
        handle_alternative()"""

    def test_structure_correct(self):
        decompiled = self.decompile()
        tree = self.verify_syntax(decompiled)
        self.assertIsNotNone(tree)
        if_count = len(self.find_all_nodes(tree, ast.If))
        self.assertGreaterEqual(if_count, 2, "应该有多个if")
        for_node = self.find_node(tree, ast.For)
        self.assertIsNotNone(for_node)
        self.assertIsNotNone(self.find_node(tree, ast.Break))


# ============================================================================
# 第九组: 特殊组合 - TRY中循环+Break/Continue (6项)
# ============================================================================

class TestL2_043_TryForWithBreak(ControlFlowTestCase):
    """L2_043: try > for + break"""
    SOURCE_CODE = """try:
    for item in collection:
        if item.error:
            raise ItemError(item)
        process(item)
except ItemError:
    log_error()
    break  # 注意: 这个break应该在for内，不在except中"""

    def test_structure_correct(self):
        decompiled = self.decompile()
        tree = self.verify_syntax(decompiled)
        self.assertIsNotNone(tree)
        try_node = self.find_node(tree, ast.Try)
        for_node = self.find_node(tree, ast.For)
        self.assertIsNotNone(try_node)
        self.assertIsNotNone(for_node)


class TestL2_044_TryWhileWithBreak(ControlFlowTestCase):
    """L2_044: try > while + break"""
    SOURCE_CODE = """try:
    while not done:
        step()
        if error_occurred:
            raise OperationError()
except OperationError:
    cleanup()
    # break可能在while内部通过异常间接实现"""

    def test_structure_correct(self):
        decompiled = self.decompile()
        tree = self.verify_syntax(decompiled)
        self.assertIsNotNone(tree)
        try_node = self.find_node(tree, ast.Try)
        while_node = self.find_node(tree, ast.While)
        self.assertIsNotNone(try_node)
        self.assertIsNotNone(while_node)


class TestL2_045_TryForWithContinue(ControlFlowTestCase):
    """L2_045: try > for + continue (通过异常跳过)"""
    SOURCE_CODE = """results = []
for item in items:
    try:
        validated = validate_and_process(item)
        results.append(validated)
    except ValidationError as e:
        log_warning(e)
        continue  # 跳过无效项目
    finally:
        update_progress()"""

    def test_structure_correct(self):
        decompiled = self.decompile()
        tree = self.verify_syntax(decompiled)
        self.assertIsNotNone(tree)
        for_node = self.find_node(tree, ast.For)
        try_node = self.find_node(tree, ast.Try)
        self.assertIsNotNone(for_node)
        self.assertIsNotNone(try_node)


class TestL2_046_TryExceptForWithReraise(ControlFlowTestCase):
    """L2_046: try-except > for + reraise"""
    SOURCE_CODE = """try:
    for url in urls:
        try:
            response = fetch(url)
            results.append(response.data)
        except NetworkError:
            skipped.append(url)
            continue
        except TimeoutError:
            raise StopProcessing(f'Timeout at {url}')
except StopProcessing as e:
    final_error = e
    break  # 终止外层处理"""

    def test_structure_correct(self):
        decompiled = self.decompile()
        tree = self.verify_syntax(decompiled)
        self.assertIsNotNone(tree)
        try_count = len(self.find_all_nodes(tree, ast.Try))
        self.assertGreaterEqual(try_count, 2, "应该有嵌套的try")
        for_node = self.find_node(tree, ast.For)
        self.assertIsNotNone(for_node)


class TestL2_047_TryFinallyForWithCleanup(ControlFlowTestCase):
    """L2_047: try-finally > for + cleanup"""
    SOURCE_CODE = """resources = []
try:
    for source in sources:
        res = acquire_resource(source)
        resources.append(res)
        try:
            use_resource(res)
        except ResourceError:
            release_resource(res)
            resources.remove(res)
            continue
finally:
    for res in resources:
        cleanup_resource(res)"""

    def test_structure_correct(self):
        decompiled = self.decompile()
        tree = self.verify_syntax(decompiled)
        self.assertIsNotNone(tree)
        try_count = len(self.find_all_nodes(tree, ast.Try))
        self.assertGreaterEqual(try_count, 2, "应该有嵌套的try")
        for_count = len(self.find_all_nodes(tree, ast.For))
        self.assertGreaterEqual(for_count, 1, "应该有for循环")


class TestL2_048_ComplexTryLoopExceptionPattern(ControlFlowTestCase):
    """L2_048: 复杂try-循环-异常模式"""
    SOURCE_CODE = """success = False
attempts = 0
max_attempts = 3

try:
    while attempts < max_attempts and not success:
        attempts += 1
        try:
            result = perform_operation_with_timeout(timeout=30)
            success = True
        except TimeoutError:
            if attempts < max_attempts:
                print(f'Retry {attempts}/{max_attempts}')
                continue
            else:
                raise MaxRetriesExceeded(attempts)
        except TemporaryError as e:
            log_temporary_error(e)
            time.sleep(2 ** attempts)  # 指数退避
            continue
        except PermanentError as e:
            raise  # 立即传播永久错误
        
finally:
    log_attempt_summary(attempts, success)
    cleanup_resources()

if not success:
    raise OperationFailedError(f'Failed after {attempts} attempts')"""

    def test_structure_correct(self):
        decompiled = self.decompile()
        tree = self.verify_syntax(decompiled)
        self.assertIsNotNone(tree)
        try_count = len(self.find_all_nodes(tree, ast.Try))
        self.assertGreaterEqual(try_count, 2, "应该有嵌套的try结构")
        while_node = self.find_node(tree, ast.While)
        self.assertIsNotNone(while_node, "应该有主重试循环")
        if_count = len(self.find_all_nodes(tree, ast.If))
        self.assertGreaterEqual(if_count, 1, "应该有条件判断")


# 测试统计：总计48项
# 第一组(IF外层): 5项 (L2_001-L2_005)
# 第二组(FOR外层): 6项 (L2_006-L2_011)
# 第三组(WHILE外层): 6项 (L2_012-L2_017)
# 第四组(TRY外层): 5项 (L2_018-L2_022)
# 第五组(WITH外层): 2项 (L2_023-L2_024)
# 第六组(FOR特殊): 6项 (L2_025-L2_030)
# 第七组(WHILE特殊): 6项 (L2_031-L2_036)
# 第八组(IF特殊): 6项 (L2_037-L2_042)
# 第九组(TRY特殊): 6项 (L2_043-L2_048)
