"""
L3三层深度嵌套组合测试用例 (16项)

覆盖Python控制流的三层嵌套关键组合模式：
- CO01-CO03: 循环-条件-跳转（3项）
- CO04-CO07: 循环-循环-跳转（4项）
- CO08-CO09: 循环-条件-循环（2项）
- CO10-CO11: 异常-循环-跳转/条件（2项）
- CO12-CO14: 循环-异常-条件（3项）
- CO15-CO16: 四层嵌套关键组合（2项）
"""

import ast
from .base import ControlFlowTestCase


# ============================================================================
# CO01-CO03: 循环-条件-跳转（3项）
# ============================================================================

class TestCO01ForIfBreak(ControlFlowTestCase):
    """CO01: for > if > break"""
    SOURCE_CODE = """def f(items, sentinel):
    for item in items:
        if item == sentinel:
            break
        print(item)
    return 'done'"""

    def test_structure_correct(self):
        decompiled = self.decompile()
        tree = self.verify_syntax(decompiled)
        self.assertIsNotNone(tree)
        for_node = self.find_node(tree, ast.For)
        self.assertIsNotNone(for_node, "应该包含for循环")
        break_node = self.find_node(tree, ast.Break)
        self.assertIsNotNone(break_node, "应该包含break")


class TestCO02ForIfContinue(ControlFlowTestCase):
    """CO02: for > if > continue"""
    SOURCE_CODE = """def f(items):
    result = []
    for item in items:
        if item < 0:
            continue
        result.append(item)
    return result"""

    def test_structure_correct(self):
        decompiled = self.decompile()
        tree = self.verify_syntax(decompiled)
        self.assertIsNotNone(tree)
        for_node = self.find_node(tree, ast.For)
        self.assertIsNotNone(for_node, "应该包含for循环")
        continue_node = self.find_node(tree, ast.Continue)
        self.assertIsNotNone(continue_node, "应该包含continue")


class TestCO03ForForBreak(ControlFlowTestCase):
    """CO03: for > for > break"""
    SOURCE_CODE = """def f(matrix, target):
    for row in matrix:
        for cell in row:
            if cell == target:
                return cell
            if cell < 0:
                break
    return None"""

    def test_structure_correct(self):
        decompiled = self.decompile()
        tree = self.verify_syntax(decompiled)
        self.assertIsNotNone(tree)
        for_count = len(self.find_all_nodes(tree, ast.For))
        self.assertEqual(for_count, 2, "应该有2个for循环")
        break_node = self.find_node(tree, ast.Break)
        self.assertIsNotNone(break_node, "应该包含break")


# ============================================================================
# CO04-CO07: 循环-循环-跳转（4项）
# ============================================================================

class TestCO04ForWhileBreak(ControlFlowTestCase):
    """CO04: for > while > break"""
    SOURCE_CODE = """def f(groups):
    for group in groups:
        n = len(group)
        while n > 0:
            if group[n - 1] is None:
                break
            n -= 1
    return 'processed'"""

    def test_structure_correct(self):
        decompiled = self.decompile()
        tree = self.verify_syntax(decompiled)
        self.assertIsNotNone(tree)
        for_node = self.find_node(tree, ast.For)
        while_node = self.find_node(tree, ast.While)
        self.assertIsNotNone(for_node, "应该包含for循环")
        self.assertIsNotNone(while_node, "应该包含while循环")


class TestCO05WhileIfBreak(ControlFlowTestCase):
    """CO05: while > if > break"""
    SOURCE_CODE = """def f(limit):
    n = 0
    while n < limit:
        if n > 100:
            break
        n += 1
    return n"""

    def test_structure_correct(self):
        decompiled = self.decompile()
        tree = self.verify_syntax(decompiled)
        self.assertIsNotNone(tree)
        while_node = self.find_node(tree, ast.While)
        self.assertIsNotNone(while_node, "应该包含while循环")
        break_node = self.find_node(tree, ast.Break)
        self.assertIsNotNone(break_node, "应该包含break")


class TestCO06WhileIfContinue(ControlFlowTestCase):
    """CO06: while > if > continue"""
    SOURCE_CODE = """def f(limit):
    n = 0
    while n < limit:
        n += 1
        if n % 3 == 0:
            continue
        print(n)
    return n"""

    def test_structure_correct(self):
        decompiled = self.decompile()
        tree = self.verify_syntax(decompiled)
        self.assertIsNotNone(tree)
        while_node = self.find_node(tree, ast.While)
        self.assertIsNotNone(while_node, "应该包含while循环")
        continue_node = self.find_node(tree, ast.Continue)
        self.assertIsNotNone(continue_node, "应该包含continue")


class TestCO07WhileForBreak(ControlFlowTestCase):
    """CO07: while > for > break"""
    SOURCE_CODE = """def f(data_queue):
    while data_queue:
        batch = data_queue.pop(0)
        for item in batch:
            if item is None:
                break
            process(item)"""

    def test_structure_correct(self):
        decompiled = self.decompile()
        tree = self.verify_syntax(decompiled)
        self.assertIsNotNone(tree)
        while_node = self.find_node(tree, ast.While)
        for_node = self.find_node(tree, ast.For)
        self.assertIsNotNone(while_node, "应该包含while循环")
        self.assertIsNotNone(for_node, "应该包含for循环")


# ============================================================================
# CO08-CO09: 循环-条件-循环（2项）
# ============================================================================

class TestCO08ForIfForBreak(ControlFlowTestCase):
    """CO08: for > if > for > break"""
    SOURCE_CODE = """def f(data, sentinel):
    for group in data:
        if len(group) > 0:
            for item in group:
                if item == sentinel:
                    break
                print(item)
    return 'done'"""

    def test_structure_correct(self):
        decompiled = self.decompile()
        tree = self.verify_syntax(decompiled)
        self.assertIsNotNone(tree)
        for_count = len(self.find_all_nodes(tree, ast.For))
        self.assertEqual(for_count, 2, "应该有2个for循环")
        break_node = self.find_node(tree, ast.Break)
        self.assertIsNotNone(break_node, "应该包含break")


class TestCO09WhileIfWhileBreak(ControlFlowTestCase):
    """CO09: while > if > while > break"""
    SOURCE_CODE = """def f(tasks, threshold):
    while tasks:
        task = tasks.pop()
        if task.size > threshold:
            while task.size > threshold:
                task.subdivide()
                if task.size <= threshold:
                    break
        process(task)"""

    def test_structure_correct(self):
        decompiled = self.decompile()
        tree = self.verify_syntax(decompiled)
        self.assertIsNotNone(tree)
        while_count = len(self.find_all_nodes(tree, ast.While))
        self.assertEqual(while_count, 2, "应该有2个while循环")
        break_node = self.find_node(tree, ast.Break)
        self.assertIsNotNone(break_node, "应该包含break")


# ============================================================================
# CO10-CO11: 异常-循环-跳转/条件（2项）
# ============================================================================

class TestCO10TryForBreak(ControlFlowTestCase):
    """CO10: try > for > break"""
    SOURCE_CODE = """def f(items, max_val):
    try:
        for item in items:
            if item > max_val:
                break
            accumulator(item)
    except OverflowError:
        reset()
    return 'complete'"""

    def test_structure_correct(self):
        decompiled = self.decompile()
        tree = self.verify_syntax(decompiled)
        self.assertIsNotNone(tree)
        try_node = self.find_node(tree, ast.Try)
        for_node = self.find_node(tree, ast.For)
        self.assertIsNotNone(try_node, "应该包含try")
        self.assertIsNotNone(for_node, "应该包含for循环")


class TestCO11TryWhileContinue(ControlFlowTestCase):
    """CO11: try > while > continue"""
    SOURCE_CODE = """def f(queue):
    try:
        while queue:
            task = queue.pop()
            if not task.valid:
                continue
            process(task)
    except QueueEmpty:
        pass
    return len(queue)"""

    def test_structure_correct(self):
        decompiled = self.decompile()
        tree = self.verify_syntax(decompiled)
        self.assertIsNotNone(tree)
        try_node = self.find_node(tree, ast.Try)
        while_node = self.find_node(tree, ast.While)
        self.assertIsNotNone(try_node, "应该包含try")
        self.assertIsNotNone(while_node, "应该包含while循环")


# ============================================================================
# CO12-CO14: 循环-异常-条件（3项）
# ============================================================================

class TestCO12ForTryExcept(ControlFlowTestCase):
    """CO12: for > try > except"""
    SOURCE_CODE = """def f(urls):
    results = []
    for url in urls:
        try:
            data = fetch(url)
            results.append(data)
        except NetworkError:
            results.append(None)
    return results"""

    def test_structure_correct(self):
        decompiled = self.decompile()
        tree = self.verify_syntax(decompiled)
        self.assertIsNotNone(tree)
        for_node = self.find_node(tree, ast.For)
        try_node = self.find_node(tree, ast.Try)
        self.assertIsNotNone(for_node, "应该包含for循环")
        self.assertIsNotNone(try_node, "应该包含try")


class TestCO13WhileTryExcept(ControlFlowTestCase):
    """CO13: while > try > except"""
    SOURCE_CODE = """def f(retries):
    success = False
    while not success and retries > 0:
        try:
            result = risky_call()
            success = True
        except TemporaryError:
            retries -= 1
    return success"""

    def test_structure_correct(self):
        decompiled = self.decompile()
        tree = self.verify_syntax(decompiled)
        self.assertIsNotNone(tree)
        while_node = self.find_node(tree, ast.While)
        try_node = self.find_node(tree, ast.Try)
        self.assertIsNotNone(while_node, "应该包含while循环")
        self.assertIsNotNone(try_node, "应该包含try")


class TestCO14ForForIfBreak(ControlFlowTestCase):
    """CO14: for > for > if > break"""
    SOURCE_CODE = """def f(matrix, sentinel):
    found = False
    for row in matrix:
        for cell in row:
            if cell == sentinel:
                found = True
                break
        if found:
            break
    return found"""

    def test_structure_correct(self):
        decompiled = self.decompile()
        tree = self.verify_syntax(decompiled)
        self.assertIsNotNone(tree)
        for_count = len(self.find_all_nodes(tree, ast.For))
        self.assertEqual(for_count, 2, "应该有2个for循环")
        break_count = len(self.find_all_nodes(tree, ast.Break))
        self.assertGreaterEqual(break_count, 2, "应该至少包含2个break")


# ============================================================================
# CO15-CO16: 四层嵌套关键组合（2项）
# ============================================================================

class TestCO15ForIfTryExcept(ControlFlowTestCase):
    """CO15: for > if > try > except"""
    SOURCE_CODE = """def f(records):
    valid_count = 0
    for record in records:
        if record.is_active():
            try:
                validate(record)
                valid_count += 1
            except ValidationError:
                mark_invalid(record)
    return valid_count"""

    def test_structure_correct(self):
        decompiled = self.decompile()
        tree = self.verify_syntax(decompiled)
        self.assertIsNotNone(tree)
        for_node = self.find_node(tree, ast.For)
        try_node = self.find_node(tree, ast.Try)
        if_node = self.find_node(tree, ast.If)
        self.assertIsNotNone(for_node, "应该包含for循环")
        self.assertIsNotNone(try_node, "应该包含try")


class TestCO16TryForIfBreak(ControlFlowTestCase):
    """CO16: try > for > if > break"""
    SOURCE_CODE = """def f(items, max_size):
    total = 0
    try:
        for item in items:
            if total > max_size:
                break
            total += item.size
            save_item(item)
    except StorageError:
        rollback()
    return total"""

    def test_structure_correct(self):
        decompiled = self.decompile()
        tree = self.verify_syntax(decompiled)
        self.assertIsNotNone(tree)
        try_node = self.find_node(tree, ast.Try)
        for_node = self.find_node(tree, ast.For)
        break_node = self.find_node(tree, ast.Break)
        self.assertIsNotNone(try_node, "应该包含try")
        self.assertIsNotNone(for_node, "应该包含for循环")
        self.assertIsNotNone(break_node, "应该包含break")


# 测试统计：总计16项
# CO01-CO03: 3项 循环-条件-跳转
# CO04-CO07: 4项 循环-循环-跳转
# CO08-CO09: 2项 循环-条件-循环
# CO10-CO11: 2项 异常-循环-跳转/条件
# CO12-CO14: 3项 循环-异常-条件
# CO15-CO16: 2项 四层嵌套组合
