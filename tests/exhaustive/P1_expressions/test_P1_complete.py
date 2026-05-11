"""
P1表达式完备性测试用例 (14项)

覆盖Python表达式的各种语法：
- BO01-BO04: BoolOp表达式（4项）
- CC01-CC03: 链式比较（3项）
- T01-T04: 三元表达式（4项）
- S07: Walrus运算符（1项）
- 其他表达式（2项）：not运算、布尔短路

总计: 14项测试
"""

import ast
from tests.control_flow_matrix.base import ControlFlowTestCase


# ============================================================================
# BO01-BO04: BoolOp表达式（4项）
# ============================================================================

class TestBO01_SimpleAnd(ControlFlowTestCase):
    """BO01: 简单and"""
    SOURCE_CODE = "x = a and b"

    def test_structure_correct(self):
        decompiled = self.decompile()
        tree = self.verify_syntax(decompiled)
        self.assertIsNotNone(tree)
        boolop = self.find_node(tree, ast.BoolOp)
        self.assertIsNotNone(boolop, "应该包含BoolOp(and)节点")


class TestBO02_SimpleOr(ControlFlowTestCase):
    """BO02: 简单or"""
    SOURCE_CODE = "x = a or b"

    def test_structure_correct(self):
        decompiled = self.decompile()
        tree = self.verify_syntax(decompiled)
        self.assertIsNotNone(tree)
        boolop = self.find_node(tree, ast.BoolOp)
        self.assertIsNotNone(boolop, "应该包含BoolOp(or)节点")


class TestBO03_CompoundAndOr(ControlFlowTestCase):
    """BO03: 复合and-or"""
    SOURCE_CODE = "x = a and b or c"

    def test_structure_correct(self):
        decompiled = self.decompile()
        tree = self.verify_syntax(decompiled)
        self.assertIsNotNone(tree)
        boolop_count = len(self.find_all_nodes(tree, ast.BoolOp))
        self.assertGreaterEqual(boolop_count, 1, "应该至少有1个BoolOp节点")


class TestBO04_ConditionAndOr(ControlFlowTestCase):
    """BO04: 条件中的and/or"""
    SOURCE_CODE = """if a and b or c:
    x = 1"""

    def test_structure_correct(self):
        decompiled = self.decompile()
        tree = self.verify_syntax(decompiled)
        self.assertIsNotNone(tree)
        if_node = self.find_node(tree, ast.If)
        self.assertIsNotNone(if_node, "应该包含if语句")
        # 检查条件中是否有BoolOp
        test_expr = if_node.test
        has_boolop = isinstance(test_expr, ast.BoolOp) or any(
            isinstance(node, ast.BoolOp) for node in ast.walk(test_expr)
        )
        self.assertTrue(has_boolop, "if条件应该包含BoolOp")


# ============================================================================
# CC01-CC03: 链式比较（3项）
# ============================================================================

class TestCC01_SimpleChained(ControlFlowTestCase):
    """CC01: 简单链式比较"""
    SOURCE_CODE = "x = 1 < 2 < 3"

    def test_structure_correct(self):
        decompiled = self.decompile()
        tree = self.verify_syntax(decompiled)
        self.assertIsNotNone(tree)
        # 链式比较在AST中表示为Compare节点
        compare = self.find_node(tree, ast.Compare)
        self.assertIsNotNone(compare, "应该包含Compare节点")
        # 链式比较应有多个操作符
        self.assertGreaterEqual(len(compare.ops), 2, "链式比较应有多个操作符")


class TestCC02_ChainedInCondition(ControlFlowTestCase):
    """CC02: 链式比较在条件中"""
    SOURCE_CODE = """if 1 < 2 < 3:
    x = 1"""

    def test_structure_correct(self):
        decompiled = self.decompile()
        tree = self.verify_syntax(decompiled)
        self.assertIsNotNone(tree)
        if_node = self.find_node(tree, ast.If)
        self.assertIsNotNone(if_node)
        compare = self.find_node(if_node, ast.Compare)
        self.assertIsNotNone(compare, "if条件应包含链式比较")
        self.assertGreaterEqual(len(compare.ops), 2)


class TestCC03_ChainedInExpression(ControlFlowTestCase):
    """CC03: 链式比较在表达式中"""
    SOURCE_CODE = "x = (1 < 2 < 3)"

    def test_structure_correct(self):
        decompiled = self.decompile()
        tree = self.verify_syntax(decompiled)
        self.assertIsNotNone(tree)
        compare = self.find_node(tree, ast.Compare)
        self.assertIsNotNone(compare, "应该包含Compare节点")
        self.assertGreaterEqual(len(compare.ops), 2, "应该是链式比较")


# ============================================================================
# T01-T04: 三元表达式（4项）
# ============================================================================

class TestT01_BasicTernary(ControlFlowTestCase):
    """T01: 基本三元"""
    SOURCE_CODE = "x = 1 if cond else 2"

    def test_structure_correct(self):
        decompiled = self.decompile()
        tree = self.verify_syntax(decompiled)
        self.assertIsNotNone(tree)
        ifexp = self.find_node(tree, ast.IfExp)
        self.assertIsNotNone(ifexp, "应该包含IfExp(三元表达式)节点")


class TestT02_TernaryInAssignment(ControlFlowTestCase):
    """T02: 三元在赋值中"""
    SOURCE_CODE = "x = y = 1 if cond else 2"

    def test_structure_correct(self):
        decompiled = self.decompile()
        tree = self.verify_syntax(decompiled)
        self.assertIsNotNone(tree)
        ifexp = self.find_node(tree, ast.IfExp)
        self.assertIsNotNone(ifexp, "应该包含IfExp节点")


class TestT03_NestedTernary(ControlFlowTestCase):
    """T03: 三元嵌套"""
    SOURCE_CODE = "x = 1 if c1 else (2 if c2 else 3)"

    def test_structure_correct(self):
        decompiled = self.decompile()
        tree = self.verify_syntax(decompiled)
        self.assertIsNotNone(tree)
        ifexp_count = len(self.find_all_nodes(tree, ast.IfExp))
        self.assertGreaterEqual(ifexp_count, 2, "应该有嵌套的IfExp节点")


class TestT04_TernaryWithBoolOp(ControlFlowTestCase):
    """T04: 三元与BoolOp结合"""
    SOURCE_CODE = "x = (a and b) if cond else c"

    def test_structure_correct(self):
        decompiled = self.decompile()
        tree = self.verify_syntax(decompiled)
        self.assertIsNotNone(tree)
        ifexp = self.find_node(tree, ast.IfExp)
        self.assertIsNotNone(ifexp, "应该包含IfExp节点")
        # 检查是否包含BoolOp
        has_boolop = any(isinstance(node, ast.BoolOp) for node in ast.walk(ifexp))
        self.assertTrue(has_boolop, "三元表达式应与BoolOp结合")


# ============================================================================
# S07: Walrus运算符（1项）
# ============================================================================

class TestS07_WalrusInCondition(ControlFlowTestCase):
    """S07: walrus在条件中"""
    SOURCE_CODE = """def fn(s):
    if (n := len(s)) > 10:
        x = n"""

    def test_correct(self):
        decompiled = self.decompile()
        tree = self.verify_syntax(decompiled)
        self.assertIsNotNone(tree)
        # Walrus运算符在AST中表示为NamedExpr
        named_expr = self.find_node(tree, ast.NamedExpr)
        self.assertIsNotNone(named_expr, "应该包含NamedExpr(walrus运算符)节点")


# ============================================================================
# 其他表达式（2项）
# ============================================================================

class TestEXPR01_NotOperation(ControlFlowTestCase):
    """EXPR01: not运算"""
    SOURCE_CODE = "x = not a"

    def test_structure_correct(self):
        decompiled = self.decompile()
        tree = self.verify_syntax(decompiled)
        self.assertIsNotNone(tree)
        unaryop = self.find_node(tree, ast.UnaryOp)
        self.assertIsNotNone(unaryop, "应该包含UnaryOp(not)节点")
        self.assertIsInstance(unaryop.op, ast.Not, "应该是Not操作")


class TestEXPR02_BooleanShortCircuit(ControlFlowTestCase):
    """EXPR02: 布尔运算短路"""
    SOURCE_CODE = """x = a and b and c
y = d or e or f"""

    def test_structure_correct(self):
        decompiled = self.decompile()
        tree = self.verify_syntax(decompiled)
        self.assertIsNotNone(tree)
        boolop_count = len(self.find_all_nodes(tree, ast.BoolOp))
        self.assertGreaterEqual(boolop_count, 2, "应该有多个BoolOp节点（and和or）")


# 测试统计：总计14项
# BoolOp: 4项 (BO01-BO04)
# 链式比较: 3项 (CC01-CC03)
# 三元表达式: 4项 (T01-T04)
# Walrus运算符: 1项 (S07)
# 其他表达式: 2项 (EXPR01-EXPR02)
