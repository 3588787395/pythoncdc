"""
L1表达式级控制流测试用例 (12项)

覆盖Python表达式中隐含的控制流结构：
- XP01-XP04: BoolOp表达式（4项）
- XP05-XP08: 三元表达式（4项）
- XP09-XP10: 链式比较（2项）
- XP11-XP12: 海象运算符（2项）
"""

import ast
from .base import ControlFlowTestCase


# ============================================================================
# XP01-XP04: BoolOp表达式（4项）
# ============================================================================

class TestXP01BoolOpAndAssign(ControlFlowTestCase):
    """XP01: x = a and b"""
    SOURCE_CODE = """def f(a, b):
    x = a and b
    return x"""

    def test_structure_correct(self):
        decompiled = self.decompile()
        tree = self.verify_syntax(decompiled)
        self.assertIsNotNone(tree)
        func_def = self.find_node(tree, ast.FunctionDef)
        self.assertIsNotNone(func_def, "应该包含函数定义")
        boolop = self.find_node(tree, ast.BoolOp)
        self.assertIsNotNone(boolop, "应该包含BoolOp节点")


class TestXP02BoolOpOrAssign(ControlFlowTestCase):
    """XP02: x = a or b"""
    SOURCE_CODE = """def f(a, b):
    x = a or b
    return x"""

    def test_structure_correct(self):
        decompiled = self.decompile()
        tree = self.verify_syntax(decompiled)
        self.assertIsNotNone(tree)
        func_def = self.find_node(tree, ast.FunctionDef)
        self.assertIsNotNone(func_def, "应该包含函数定义")


class TestXP03BoolOpChainAssign(ControlFlowTestCase):
    """XP03: x = a and b and c"""
    SOURCE_CODE = """def f(a, b, c):
    x = a and b and c
    return x"""

    def test_structure_correct(self):
        decompiled = self.decompile()
        tree = self.verify_syntax(decompiled)
        self.assertIsNotNone(tree)
        func_def = self.find_node(tree, ast.FunctionDef)
        self.assertIsNotNone(func_def, "应该包含函数定义")


class TestXP04BoolOpInIf(ControlFlowTestCase):
    """XP04: if a and b: pass"""
    SOURCE_CODE = """def f(a, b):
    if a and b:
        result = 1
    else:
        result = 0
    return result"""

    def test_structure_correct(self):
        decompiled = self.decompile()
        tree = self.verify_syntax(decompiled)
        self.assertIsNotNone(tree)
        if_node = self.find_node(tree, ast.If)
        self.assertIsNotNone(if_node, "应该包含if语句")
        boolop = self.find_node(tree, ast.BoolOp)
        self.assertIsNotNone(boolop, "应该包含BoolOp节点")


# ============================================================================
# XP05-XP08: 三元表达式（4项）
# ============================================================================

class TestXP05BasicTernaryAssign(ControlFlowTestCase):
    """XP05: x = a if c else b"""
    SOURCE_CODE = """def f(a, b, c):
    x = a if c else b
    return x"""

    def test_structure_correct(self):
        decompiled = self.decompile()
        tree = self.verify_syntax(decompiled)
        self.assertIsNotNone(tree)
        ifexp = self.find_node(tree, ast.IfExp)
        self.assertIsNotNone(ifexp, "应该包含IfExp三元表达式")


class TestXP06TernaryInReturn(ControlFlowTestCase):
    """XP06: return a if c else b"""
    SOURCE_CODE = """def f(a, b, c):
    return a if c else b"""

    def test_structure_correct(self):
        decompiled = self.decompile()
        tree = self.verify_syntax(decompiled)
        self.assertIsNotNone(tree)
        ifexp = self.find_node(tree, ast.IfExp)
        self.assertIsNotNone(ifexp, "应该包含IfExp三元表达式")


class TestXP07NestedTernary(ControlFlowTestCase):
    """XP07: x = (a if c1 else b) if c2 else d"""
    SOURCE_CODE = """def f(a, b, c1, c2, d):
    x = (a if c1 else b) if c2 else d
    return x"""

    def test_structure_correct(self):
        decompiled = self.decompile()
        tree = self.verify_syntax(decompiled)
        self.assertIsNotNone(tree)
        ifexp_count = len(self.find_all_nodes(tree, ast.IfExp))
        self.assertEqual(ifexp_count, 2, "应该有2个嵌套的IfExp三元表达式")


class TestXP08TernaryInExpression(ControlFlowTestCase):
    """XP08: 表达式中的三元运算"""
    SOURCE_CODE = """def f(x, y):
    result = (x if x > 0 else 0) + (y if y > 0 else 0)
    return result"""

    def test_structure_correct(self):
        decompiled = self.decompile()
        tree = self.verify_syntax(decompiled)
        self.assertIsNotNone(tree)
        ifexp_count = len(self.find_all_nodes(tree, ast.IfExp))
        self.assertEqual(ifexp_count, 2, "应该有2个IfExp三元表达式")


# ============================================================================
# XP09-XP10: 链式比较（2项）
# ============================================================================

class TestXP09ChainedCompareInIf(ControlFlowTestCase):
    """XP09: if 0 < x < 10: pass"""
    SOURCE_CODE = """def f(x):
    if 0 < x < 10:
        return 'in_range'
    return 'out_of_range'"""

    def test_structure_correct(self):
        decompiled = self.decompile()
        tree = self.verify_syntax(decompiled)
        self.assertIsNotNone(tree)
        compare = self.find_node(tree, ast.Compare)
        self.assertIsNotNone(compare, "应该包含比较节点")
        self.assertGreater(len(compare.ops), 1, "链式比较应有多个操作符")


class TestXP10ChainedCompareAssign(ControlFlowTestCase):
    """XP10: x = 0 < y < 10"""
    SOURCE_CODE = """def f(y):
    x = 0 < y < 10
    return x"""

    def test_structure_correct(self):
        decompiled = self.decompile()
        tree = self.verify_syntax(decompiled)
        self.assertIsNotNone(tree)
        compare = self.find_node(tree, ast.Compare)
        self.assertIsNotNone(compare, "应该包含比较节点")


# ============================================================================
# XP11-XP12: 海象运算符（2项）
# ============================================================================

class TestXP11WalrusInIf(ControlFlowTestCase):
    """XP11: if (n := len(d)) > 0: return n"""
    SOURCE_CODE = """def f(d):
    if (n := len(d)) > 0:
        return n
    return -1"""

    def test_structure_correct(self):
        decompiled = self.decompile()
        tree = self.verify_syntax(decompiled)
        self.assertIsNotNone(tree)
        named_expr = self.find_node(tree, ast.NamedExpr)
        self.assertIsNotNone(named_expr, "应该包含海象运算符NamedExpr")


class TestXP12WalrusInWhile(ControlFlowTestCase):
    """XP12: while (line := f.readline()) != '':"""
    SOURCE_CODE = """def f(readline):
    lines = []
    while (line := readline()) != '':
        lines.append(line)
    return lines"""

    def test_structure_correct(self):
        decompiled = self.decompile()
        tree = self.verify_syntax(decompiled)
        self.assertIsNotNone(tree)
        named_expr = self.find_node(tree, ast.NamedExpr)
        self.assertIsNotNone(named_expr, "应该包含海象运算符NamedExpr")


# 测试统计：总计12项
# XP01-XP04: 4项BoolOp表达式
# XP05-XP08: 4项三元表达式
# XP09-XP10: 2项链式比较
# XP11-XP12: 2项海象运算符
