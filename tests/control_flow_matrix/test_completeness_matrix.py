"""
控制流语法全排列组合测试矩阵

根据 CFG架构对比与完善路线.md 中的完备性测试矩阵，
系统化测试所有控制流语法及其嵌套组合。
"""

import ast
from .base import ControlFlowTestCase


class TestB01SimpleAssign(ControlFlowTestCase):
    SOURCE_CODE = "x = 1"
    def test_structure_correct(self):
        decompiled = self.decompile()
        tree = self.verify_syntax(decompiled)
        self.assertIsNotNone(tree)

class TestB02AugAssign(ControlFlowTestCase):
    SOURCE_CODE = "x = 0\nx += 1"
    def test_structure_correct(self):
        decompiled = self.decompile()
        tree = self.verify_syntax(decompiled)
        self.assertIsNotNone(tree)

class TestB03MultiTargetAssign(ControlFlowTestCase):
    SOURCE_CODE = "a = b = 1"
    def test_structure_correct(self):
        decompiled = self.decompile()
        tree = self.verify_syntax(decompiled)
        self.assertIsNotNone(tree)

class TestB04TupleUnpack(ControlFlowTestCase):
    SOURCE_CODE = "a, b = 1, 2"
    def test_structure_correct(self):
        decompiled = self.decompile()
        tree = self.verify_syntax(decompiled)
        self.assertIsNotNone(tree)

class TestB05ExprStmt(ControlFlowTestCase):
    SOURCE_CODE = "print(x)"
    def test_structure_correct(self):
        decompiled = self.decompile()
        tree = self.verify_syntax(decompiled)
        self.assertIsNotNone(tree)

class TestB06Return(ControlFlowTestCase):
    SOURCE_CODE = "def f():\n    return x"
    def test_structure_correct(self):
        decompiled = self.decompile()
        tree = self.verify_syntax(decompiled)
        self.assertIsNotNone(tree)

class TestB07ReturnNone(ControlFlowTestCase):
    SOURCE_CODE = "def f():\n    return"
    def test_structure_correct(self):
        decompiled = self.decompile()
        tree = self.verify_syntax(decompiled)
        self.assertIsNotNone(tree)

class TestB08Pass(ControlFlowTestCase):
    SOURCE_CODE = "pass"
    def test_structure_correct(self):
        decompiled = self.decompile()
        tree = self.verify_syntax(decompiled)
        self.assertIsNotNone(tree)


class TestC01IfThen(ControlFlowTestCase):
    SOURCE_CODE = "if x:\n    y = 1"
    def test_structure_correct(self):
        decompiled = self.decompile()
        tree = self.verify_syntax(decompiled)
        self.assertIsNotNone(self.find_node(tree, ast.If))

class TestC02IfElse(ControlFlowTestCase):
    SOURCE_CODE = "if x:\n    y = 1\nelse:\n    y = 2"
    def test_structure_correct(self):
        decompiled = self.decompile()
        tree = self.verify_syntax(decompiled)
        if_node = self.find_node(tree, ast.If)
        self.assertIsNotNone(if_node)
        self.assertIsNotNone(if_node.orelse)

class TestC03IfElif(ControlFlowTestCase):
    SOURCE_CODE = "if x > 0:\n    y = 1\nelif x < 0:\n    y = -1"
    def test_structure_correct(self):
        decompiled = self.decompile()
        tree = self.verify_syntax(decompiled)
        self.assertIsNotNone(self.find_node(tree, ast.If))

class TestC04IfElifElse(ControlFlowTestCase):
    SOURCE_CODE = "if x > 0:\n    y = 1\nelif x < 0:\n    y = -1\nelse:\n    y = 0"
    def test_structure_correct(self):
        decompiled = self.decompile()
        tree = self.verify_syntax(decompiled)
        self.assertIsNotNone(self.find_node(tree, ast.If))

class TestC05MultiElif(ControlFlowTestCase):
    SOURCE_CODE = "if x == 1:\n    y = 'a'\nelif x == 2:\n    y = 'b'\nelif x == 3:\n    y = 'c'\nelse:\n    y = 'd'"
    def test_structure_correct(self):
        decompiled = self.decompile()
        tree = self.verify_syntax(decompiled)
        self.assertIsNotNone(self.find_node(tree, ast.If))

class TestC06NestedIf(ControlFlowTestCase):
    SOURCE_CODE = "if x:\n    if y:\n        z = 1"
    def test_structure_correct(self):
        decompiled = self.decompile()
        tree = self.verify_syntax(decompiled)
        ifs = self.find_all_nodes(tree, ast.If)
        boolops = self.find_all_nodes(tree, ast.BoolOp)
        self.assertTrue(len(ifs) >= 2 or len(boolops) >= 1,
                       "Either nested if or BoolOp is acceptable (bytecode ambiguous)")

class TestC07NestedIfElse(ControlFlowTestCase):
    SOURCE_CODE = "if x:\n    if y:\n        z = 1\n    else:\n        z = 2\nelse:\n    z = 3"
    def test_structure_correct(self):
        decompiled = self.decompile()
        tree = self.verify_syntax(decompiled)
        ifs = self.find_all_nodes(tree, ast.If)
        self.assertGreaterEqual(len(ifs), 2)


class TestL01ForLoop(ControlFlowTestCase):
    SOURCE_CODE = "for i in range(10):\n    print(i)"
    def test_structure_correct(self):
        decompiled = self.decompile()
        tree = self.verify_syntax(decompiled)
        self.assertIsNotNone(self.find_node(tree, ast.For))

class TestL02WhileLoop(ControlFlowTestCase):
    SOURCE_CODE = "while x > 0:\n    x -= 1"
    def test_structure_correct(self):
        decompiled = self.decompile()
        tree = self.verify_syntax(decompiled)
        self.assertIsNotNone(self.find_node(tree, ast.While))

class TestL03ForElse(ControlFlowTestCase):
    SOURCE_CODE = "for i in range(10):\n    x = i\nelse:\n    x = -1"
    def test_structure_correct(self):
        # Cat-A: for/else without break produces identical bytecode as for/... — unsolvable from bytecode alone
        decompiled = self.decompile()
        tree = self.verify_syntax(decompiled)
        for_node = self.find_node(tree, ast.For)
        self.assertIsNotNone(for_node)
        self.assertTrue(len(for_node.orelse) > 0)

class TestL04WhileElse(ControlFlowTestCase):
    SOURCE_CODE = "while x > 0:\n    x -= 1\nelse:\n    x = 0"
    def test_structure_correct(self):
        # Cat-A: while/else without break produces identical bytecode as while/... — unsolvable from bytecode alone
        decompiled = self.decompile()
        tree = self.verify_syntax(decompiled)
        while_node = self.find_node(tree, ast.While)
        self.assertIsNotNone(while_node)
        self.assertTrue(len(while_node.orelse) > 0)

class TestL05ForBreak(ControlFlowTestCase):
    SOURCE_CODE = "for i in range(10):\n    if i == 5:\n        break"
    def test_structure_correct(self):
        decompiled = self.decompile()
        tree = self.verify_syntax(decompiled)
        self.assertIsNotNone(self.find_node(tree, ast.For))
        self.assertIsNotNone(self.find_node(tree, ast.Break))

class TestL06ForContinue(ControlFlowTestCase):
    SOURCE_CODE = "for i in range(10):\n    if i == 5:\n        continue\n    print(i)"
    def test_structure_correct(self):
        decompiled = self.decompile()
        tree = self.verify_syntax(decompiled)
        self.assertIsNotNone(self.find_node(tree, ast.For))
        self.assertIsNotNone(self.find_node(tree, ast.Continue))

class TestL07WhileBreak(ControlFlowTestCase):
    SOURCE_CODE = "while x > 0:\n    if x == 1:\n        break\n    x -= 1"
    def test_structure_correct(self):
        decompiled = self.decompile()
        tree = self.verify_syntax(decompiled)
        self.assertIsNotNone(self.find_node(tree, ast.While))
        self.assertIsNotNone(self.find_node(tree, ast.Break))

class TestL08WhileContinue(ControlFlowTestCase):
    SOURCE_CODE = "while x > 0:\n    if x == 1:\n        continue\n    x -= 1"
    def test_structure_correct(self):
        decompiled = self.decompile()
        tree = self.verify_syntax(decompiled)
        self.assertIsNotNone(self.find_node(tree, ast.While))
        self.assertIsNotNone(self.find_node(tree, ast.Continue))

class TestL09ForBreakElse(ControlFlowTestCase):
    SOURCE_CODE = "for i in range(10):\n    if i == 5:\n        break\nelse:\n    x = -1"
    def test_structure_correct(self):
        decompiled = self.decompile()
        tree = self.verify_syntax(decompiled)
        for_node = self.find_node(tree, ast.For)
        self.assertIsNotNone(for_node)
        self.assertIsNotNone(self.find_node(tree, ast.Break))

class TestL10WhileBreakElse(ControlFlowTestCase):
    SOURCE_CODE = "while x > 0:\n    if x == 1:\n        break\n    x -= 1\nelse:\n    x = 0"
    def test_structure_correct(self):
        decompiled = self.decompile()
        tree = self.verify_syntax(decompiled)
        while_node = self.find_node(tree, ast.While)
        self.assertIsNotNone(while_node)
        self.assertIsNotNone(self.find_node(tree, ast.Break))

class TestL11ForBreakContinue(ControlFlowTestCase):
    SOURCE_CODE = "for i in range(10):\n    if i == 3:\n        continue\n    if i == 7:\n        break\n    print(i)"
    def test_structure_correct(self):
        decompiled = self.decompile()
        tree = self.verify_syntax(decompiled)
        self.assertIsNotNone(self.find_node(tree, ast.Break))
        self.assertIsNotNone(self.find_node(tree, ast.Continue))

class TestL12WhileBreakContinue(ControlFlowTestCase):
    SOURCE_CODE = "while x > 0:\n    if x == 5:\n        continue\n    if x == 1:\n        break\n    x -= 1"
    def test_structure_correct(self):
        decompiled = self.decompile()
        tree = self.verify_syntax(decompiled)
        self.assertIsNotNone(self.find_node(tree, ast.Break))
        self.assertIsNotNone(self.find_node(tree, ast.Continue))

class TestL13NestedFor(ControlFlowTestCase):
    SOURCE_CODE = "for i in range(3):\n    for j in range(3):\n        print(i, j)"
    def test_structure_correct(self):
        decompiled = self.decompile()
        tree = self.verify_syntax(decompiled)
        fors = self.find_all_nodes(tree, ast.For)
        self.assertGreaterEqual(len(fors), 2)

class TestL14NestedWhile(ControlFlowTestCase):
    SOURCE_CODE = "while x > 0:\n    while y > 0:\n        y -= 1\n    x -= 1"
    def test_structure_correct(self):
        decompiled = self.decompile()
        tree = self.verify_syntax(decompiled)
        whiles = self.find_all_nodes(tree, ast.While)
        self.assertGreaterEqual(len(whiles), 2)

class TestL15NestedForBreak(ControlFlowTestCase):
    SOURCE_CODE = "for i in range(3):\n    for j in range(3):\n        if j == 1:\n            break\n    print(i)"
    def test_structure_correct(self):
        decompiled = self.decompile()
        tree = self.verify_syntax(decompiled)
        self.assertIsNotNone(self.find_node(tree, ast.Break))

class TestL16NestedForContinue(ControlFlowTestCase):
    SOURCE_CODE = "for i in range(3):\n    for j in range(3):\n        if j == 1:\n            continue\n        print(i, j)"
    def test_structure_correct(self):
        decompiled = self.decompile()
        tree = self.verify_syntax(decompiled)
        self.assertIsNotNone(self.find_node(tree, ast.Continue))

class TestL17ForInWhile(ControlFlowTestCase):
    SOURCE_CODE = "while x > 0:\n    for i in range(3):\n        print(i)\n    x -= 1"
    def test_structure_correct(self):
        decompiled = self.decompile()
        tree = self.verify_syntax(decompiled)
        self.assertIsNotNone(self.find_node(tree, ast.While))
        self.assertIsNotNone(self.find_node(tree, ast.For))

class TestL18WhileInFor(ControlFlowTestCase):
    SOURCE_CODE = "for i in range(3):\n    while x > 0:\n        x -= 1\n    x = 10"
    def test_structure_correct(self):
        decompiled = self.decompile()
        tree = self.verify_syntax(decompiled)
        self.assertIsNotNone(self.find_node(tree, ast.For))
        self.assertIsNotNone(self.find_node(tree, ast.While))


class TestE01TryExcept(ControlFlowTestCase):
    SOURCE_CODE = "try:\n    x = 1\nexcept TypeError:\n    x = 0"
    def test_structure_correct(self):
        decompiled = self.decompile()
        tree = self.verify_syntax(decompiled)
        self.assertIsNotNone(self.find_node(tree, ast.Try))

class TestE02TryMultiExcept(ControlFlowTestCase):
    SOURCE_CODE = "try:\n    x = 1\nexcept TypeError:\n    x = 0\nexcept ValueError:\n    x = -1"
    def test_structure_correct(self):
        decompiled = self.decompile()
        tree = self.verify_syntax(decompiled)
        try_node = self.find_node(tree, ast.Try)
        self.assertIsNotNone(try_node)
        self.assertGreaterEqual(len(try_node.handlers), 2)

class TestE03TryExceptElse(ControlFlowTestCase):
    SOURCE_CODE = "try:\n    x = 1\nexcept TypeError:\n    x = 0\nelse:\n    y = 2"
    def test_structure_correct(self):
        decompiled = self.decompile()
        tree = self.verify_syntax(decompiled)
        try_node = self.find_node(tree, ast.Try)
        self.assertIsNotNone(try_node)
        self.assertTrue(len(try_node.orelse) > 0)

class TestE04TryFinally(ControlFlowTestCase):
    SOURCE_CODE = "try:\n    x = 1\nfinally:\n    x = 0"
    def test_structure_correct(self):
        decompiled = self.decompile()
        tree = self.verify_syntax(decompiled)
        try_node = self.find_node(tree, ast.Try)
        self.assertIsNotNone(try_node)
        self.assertTrue(len(try_node.finalbody) > 0)

class TestE05TryExceptFinally(ControlFlowTestCase):
    SOURCE_CODE = "try:\n    x = 1\nexcept TypeError:\n    x = 0\nfinally:\n    y = 2"
    def test_structure_correct(self):
        decompiled = self.decompile()
        tree = self.verify_syntax(decompiled)
        try_node = self.find_node(tree, ast.Try)
        self.assertIsNotNone(try_node)
        self.assertTrue(len(try_node.handlers) > 0)
        self.assertTrue(len(try_node.finalbody) > 0)

class TestE06TryExceptElseFinally(ControlFlowTestCase):
    SOURCE_CODE = "try:\n    x = 1\nexcept TypeError:\n    x = 0\nelse:\n    y = 2\nfinally:\n    z = 3"
    def test_structure_correct(self):
        decompiled = self.decompile()
        tree = self.verify_syntax(decompiled)
        try_node = self.find_node(tree, ast.Try)
        self.assertIsNotNone(try_node)

class TestE07ExceptAs(ControlFlowTestCase):
    SOURCE_CODE = "try:\n    x = 1\nexcept TypeError as e:\n    print(e)"
    def test_structure_correct(self):
        decompiled = self.decompile()
        tree = self.verify_syntax(decompiled)
        try_node = self.find_node(tree, ast.Try)
        self.assertIsNotNone(try_node)

class TestE08BareExcept(ControlFlowTestCase):
    SOURCE_CODE = "try:\n    x = 1\nexcept:\n    x = 0"
    def test_structure_correct(self):
        decompiled = self.decompile()
        tree = self.verify_syntax(decompiled)
        try_node = self.find_node(tree, ast.Try)
        self.assertIsNotNone(try_node)

class TestE09NestedTry(ControlFlowTestCase):
    SOURCE_CODE = "try:\n    try:\n        x = 1\n    except TypeError:\n        x = 0\nexcept ValueError:\n    x = -1"
    def test_structure_correct(self):
        decompiled = self.decompile()
        tree = self.verify_syntax(decompiled)
        tries = self.find_all_nodes(tree, ast.Try)
        self.assertGreaterEqual(len(tries), 2)

class TestE10TryInLoop(ControlFlowTestCase):
    SOURCE_CODE = "for i in range(3):\n    try:\n        x = i\n    except TypeError:\n        x = 0"
    def test_structure_correct(self):
        decompiled = self.decompile()
        tree = self.verify_syntax(decompiled)
        self.assertIsNotNone(self.find_node(tree, ast.For))
        self.assertIsNotNone(self.find_node(tree, ast.Try))

class TestE11LoopInTry(ControlFlowTestCase):
    SOURCE_CODE = "try:\n    for i in range(3):\n        x = i\nexcept TypeError:\n    x = 0"
    def test_structure_correct(self):
        decompiled = self.decompile()
        tree = self.verify_syntax(decompiled)
        self.assertIsNotNone(self.find_node(tree, ast.Try))
        self.assertIsNotNone(self.find_node(tree, ast.For))

class TestE12TryInIf(ControlFlowTestCase):
    SOURCE_CODE = "if x:\n    try:\n        y = 1\n    except TypeError:\n        y = 0"
    def test_structure_correct(self):
        decompiled = self.decompile()
        tree = self.verify_syntax(decompiled)
        self.assertIsNotNone(self.find_node(tree, ast.If))
        self.assertIsNotNone(self.find_node(tree, ast.Try))

class TestE13IfInTry(ControlFlowTestCase):
    SOURCE_CODE = "try:\n    if x:\n        y = 1\nexcept TypeError:\n    y = 0"
    def test_structure_correct(self):
        decompiled = self.decompile()
        tree = self.verify_syntax(decompiled)
        self.assertIsNotNone(self.find_node(tree, ast.Try))
        self.assertIsNotNone(self.find_node(tree, ast.If))


class TestW01SimpleWith(ControlFlowTestCase):
    SOURCE_CODE = "with open('f') as f:\n    data = f.read()"
    def test_structure_correct(self):
        decompiled = self.decompile()
        tree = self.verify_syntax(decompiled)
        self.assertIsNotNone(self.find_node(tree, ast.With))

class TestW02WithNoAs(ControlFlowTestCase):
    SOURCE_CODE = "with ctx:\n    pass"
    def test_structure_correct(self):
        decompiled = self.decompile()
        tree = self.verify_syntax(decompiled)
        self.assertIsNotNone(self.find_node(tree, ast.With))

class TestW03MultiContextWith(ControlFlowTestCase):
    SOURCE_CODE = "with open('a') as a, open('b') as b:\n    data = a.read() + b.read()"
    def test_structure_correct(self):
        decompiled = self.decompile()
        tree = self.verify_syntax(decompiled)
        self.assertIsNotNone(self.find_node(tree, ast.With))

class TestW04NestedWith(ControlFlowTestCase):
    SOURCE_CODE = "with open('a') as a:\n    with open('b') as b:\n        data = a.read() + b.read()"
    def test_structure_correct(self):
        decompiled = self.decompile()
        tree = self.verify_syntax(decompiled)
        withs = self.find_all_nodes(tree, ast.With)
        self.assertGreaterEqual(len(withs), 1)
        if len(withs) == 1:
            self.assertGreaterEqual(len(withs[0].items), 2)

class TestW05WithInTry(ControlFlowTestCase):
    SOURCE_CODE = "try:\n    with open('f') as f:\n        data = f.read()\nexcept OSError:\n    data = ''"
    def test_structure_correct(self):
        decompiled = self.decompile()
        tree = self.verify_syntax(decompiled)
        self.assertIsNotNone(self.find_node(tree, ast.Try))
        self.assertIsNotNone(self.find_node(tree, ast.With))

class TestW06TryInWith(ControlFlowTestCase):
    SOURCE_CODE = "with open('f') as f:\n    try:\n        data = f.read()\n    except OSError:\n        data = ''"
    def test_structure_correct(self):
        decompiled = self.decompile()
        tree = self.verify_syntax(decompiled)
        self.assertIsNotNone(self.find_node(tree, ast.With))
        self.assertIsNotNone(self.find_node(tree, ast.Try))


class TestN01ForIfBreak(ControlFlowTestCase):
    SOURCE_CODE = "for i in range(10):\n    if i == 5:\n        break"
    def test_structure_correct(self):
        decompiled = self.decompile()
        tree = self.verify_syntax(decompiled)
        self.assertIsNotNone(self.find_node(tree, ast.For))
        self.assertIsNotNone(self.find_node(tree, ast.Break))

class TestN02ForIfContinue(ControlFlowTestCase):
    SOURCE_CODE = "for i in range(10):\n    if i == 5:\n        continue"
    def test_structure_correct(self):
        decompiled = self.decompile()
        tree = self.verify_syntax(decompiled)
        self.assertIsNotNone(self.find_node(tree, ast.For))
        self.assertIsNotNone(self.find_node(tree, ast.Continue))

class TestN03ForForBreak(ControlFlowTestCase):
    SOURCE_CODE = "for i in range(3):\n    for j in range(3):\n        if j == 1:\n            break\n    print(i)"
    def test_structure_correct(self):
        decompiled = self.decompile()
        tree = self.verify_syntax(decompiled)
        self.assertIsNotNone(self.find_node(tree, ast.Break))

class TestN04ForForContinue(ControlFlowTestCase):
    SOURCE_CODE = "for i in range(3):\n    for j in range(3):\n        if j == 1:\n            continue\n        print(i, j)"
    def test_structure_correct(self):
        decompiled = self.decompile()
        tree = self.verify_syntax(decompiled)
        self.assertIsNotNone(self.find_node(tree, ast.Continue))

class TestN05ForWhileBreak(ControlFlowTestCase):
    SOURCE_CODE = "for i in range(3):\n    while x > 0:\n        if x == 1:\n            break\n        x -= 1"
    def test_structure_correct(self):
        decompiled = self.decompile()
        tree = self.verify_syntax(decompiled)
        self.assertIsNotNone(self.find_node(tree, ast.Break))

class TestN06WhileIfBreak(ControlFlowTestCase):
    SOURCE_CODE = "while x > 0:\n    if x == 1:\n        break\n    x -= 1"
    def test_structure_correct(self):
        decompiled = self.decompile()
        tree = self.verify_syntax(decompiled)
        self.assertIsNotNone(self.find_node(tree, ast.Break))

class TestN07WhileIfContinue(ControlFlowTestCase):
    SOURCE_CODE = "while x > 0:\n    if x == 5:\n        continue\n    x -= 1"
    def test_structure_correct(self):
        decompiled = self.decompile()
        tree = self.verify_syntax(decompiled)
        self.assertIsNotNone(self.find_node(tree, ast.Continue))

class TestN08WhileForBreak(ControlFlowTestCase):
    SOURCE_CODE = "while x > 0:\n    for i in range(3):\n        if i == 1:\n            break\n    x -= 1"
    def test_structure_correct(self):
        decompiled = self.decompile()
        tree = self.verify_syntax(decompiled)
        self.assertIsNotNone(self.find_node(tree, ast.Break))

class TestN09WhileForContinue(ControlFlowTestCase):
    SOURCE_CODE = "while x > 0:\n    for i in range(3):\n        if i == 1:\n            continue\n        print(i)\n    x -= 1"
    def test_structure_correct(self):
        decompiled = self.decompile()
        tree = self.verify_syntax(decompiled)
        self.assertIsNotNone(self.find_node(tree, ast.Continue))

class TestN10TryForBreak(ControlFlowTestCase):
    SOURCE_CODE = "try:\n    for i in range(10):\n        if i == 5:\n            break\nexcept TypeError:\n    pass"
    def test_structure_correct(self):
        decompiled = self.decompile()
        tree = self.verify_syntax(decompiled)
        self.assertIsNotNone(self.find_node(tree, ast.Break))

class TestN11TryWhileContinue(ControlFlowTestCase):
    SOURCE_CODE = "try:\n    while x > 0:\n        if x == 5:\n            continue\n        x -= 1\nexcept TypeError:\n    pass"
    def test_structure_correct(self):
        decompiled = self.decompile()
        tree = self.verify_syntax(decompiled)
        self.assertIsNotNone(self.find_node(tree, ast.Continue))

class TestN12ForTryExcept(ControlFlowTestCase):
    SOURCE_CODE = "for i in range(3):\n    try:\n        x = i\n    except TypeError:\n        x = 0"
    def test_structure_correct(self):
        decompiled = self.decompile()
        tree = self.verify_syntax(decompiled)
        self.assertIsNotNone(self.find_node(tree, ast.For))
        self.assertIsNotNone(self.find_node(tree, ast.Try))

class TestN13WhileTryExcept(ControlFlowTestCase):
    SOURCE_CODE = "while x > 0:\n    try:\n        x -= 1\n    except TypeError:\n        x = 0"
    def test_structure_correct(self):
        decompiled = self.decompile()
        tree = self.verify_syntax(decompiled)
        self.assertIsNotNone(self.find_node(tree, ast.While))
        self.assertIsNotNone(self.find_node(tree, ast.Try))

class TestN14ForIfForBreak(ControlFlowTestCase):
    SOURCE_CODE = "for i in range(3):\n    if i > 0:\n        for j in range(3):\n            if j == 1:\n                break"
    def test_structure_correct(self):
        decompiled = self.decompile()
        tree = self.verify_syntax(decompiled)
        self.assertIsNotNone(self.find_node(tree, ast.Break))

class TestN15WhileIfWhileBreak(ControlFlowTestCase):
    SOURCE_CODE = "while x > 0:\n    if x < 5:\n        while y > 0:\n            if y == 1:\n                break\n            y -= 1\n    x -= 1"
    def test_structure_correct(self):
        decompiled = self.decompile()
        tree = self.verify_syntax(decompiled)
        self.assertIsNotNone(self.find_node(tree, ast.Break))

class TestN16ForForIfBreak(ControlFlowTestCase):
    SOURCE_CODE = "for i in range(3):\n    for j in range(3):\n        if j == 1:\n            break\n    print(i)"
    def test_structure_correct(self):
        decompiled = self.decompile()
        tree = self.verify_syntax(decompiled)
        self.assertIsNotNone(self.find_node(tree, ast.Break))

class TestN17ForIfTryExcept(ControlFlowTestCase):
    SOURCE_CODE = "for i in range(3):\n    if i > 0:\n        try:\n            x = i\n        except TypeError:\n            x = 0"
    def test_structure_correct(self):
        decompiled = self.decompile()
        tree = self.verify_syntax(decompiled)
        self.assertIsNotNone(self.find_node(tree, ast.Try))

class TestN18TryForIfBreak(ControlFlowTestCase):
    SOURCE_CODE = "try:\n    for i in range(10):\n        if i == 5:\n            break\nexcept TypeError:\n    pass"
    def test_structure_correct(self):
        decompiled = self.decompile()
        tree = self.verify_syntax(decompiled)
        self.assertIsNotNone(self.find_node(tree, ast.Break))


class TestCF1ForIfBreakContinue(ControlFlowTestCase):
    SOURCE_CODE = "for i in range(10):\n    if i == 3:\n        continue\n    if i == 7:\n        break\n    print(i)"
    def test_structure_correct(self):
        decompiled = self.decompile()
        tree = self.verify_syntax(decompiled)
        self.assertIsNotNone(self.find_node(tree, ast.Break))
        self.assertIsNotNone(self.find_node(tree, ast.Continue))

class TestCF2WhileIfBreakContinue(ControlFlowTestCase):
    SOURCE_CODE = "while x > 0:\n    if x == 5:\n        continue\n    if x == 1:\n        break\n    x -= 1"
    def test_structure_correct(self):
        decompiled = self.decompile()
        tree = self.verify_syntax(decompiled)
        self.assertIsNotNone(self.find_node(tree, ast.Break))
        self.assertIsNotNone(self.find_node(tree, ast.Continue))

class TestCL1IfInFor(ControlFlowTestCase):
    SOURCE_CODE = "if flag:\n    for i in range(10):\n        print(i)"
    def test_structure_correct(self):
        decompiled = self.decompile()
        tree = self.verify_syntax(decompiled)
        self.assertIsNotNone(self.find_node(tree, ast.If))
        self.assertIsNotNone(self.find_node(tree, ast.For))

class TestCL2IfInWhile(ControlFlowTestCase):
    SOURCE_CODE = "if flag:\n    while x > 0:\n        x -= 1"
    def test_structure_correct(self):
        decompiled = self.decompile()
        tree = self.verify_syntax(decompiled)
        self.assertIsNotNone(self.find_node(tree, ast.If))
        self.assertIsNotNone(self.find_node(tree, ast.While))


class TestTernary01(ControlFlowTestCase):
    SOURCE_CODE = "y = 10 if x > 3 else 0"
    def test_structure_correct(self):
        decompiled = self.decompile()
        tree = self.verify_syntax(decompiled)
        self.assertIsNotNone(self.find_node(tree, ast.IfExp))

class TestTernary02(ControlFlowTestCase):
    SOURCE_CODE = "z = 'yes' if flag else 'no'"
    def test_structure_correct(self):
        decompiled = self.decompile()
        tree = self.verify_syntax(decompiled)
        self.assertIsNotNone(self.find_node(tree, ast.IfExp))

class TestBoolOp01(ControlFlowTestCase):
    SOURCE_CODE = "if x and y:\n    z = 1"
    def test_structure_correct(self):
        decompiled = self.decompile()
        tree = self.verify_syntax(decompiled)
        self.assertIsNotNone(self.find_node(tree, ast.BoolOp))

class TestBoolOp02(ControlFlowTestCase):
    SOURCE_CODE = "if x or y:\n    z = 1"
    def test_structure_correct(self):
        decompiled = self.decompile()
        tree = self.verify_syntax(decompiled)
        self.assertIsNotNone(self.find_node(tree, ast.BoolOp))

class TestBoolOp03(ControlFlowTestCase):
    SOURCE_CODE = "if x and y and z:\n    w = 1"
    def test_structure_correct(self):
        decompiled = self.decompile()
        tree = self.verify_syntax(decompiled)
        self.assertIsNotNone(self.find_node(tree, ast.BoolOp))

class TestBoolOp04(ControlFlowTestCase):
    SOURCE_CODE = "if x or y or z:\n    w = 1"
    def test_structure_correct(self):
        decompiled = self.decompile()
        tree = self.verify_syntax(decompiled)
        self.assertIsNotNone(self.find_node(tree, ast.BoolOp))

class TestBoolOp05(ControlFlowTestCase):
    SOURCE_CODE = "if (x and y) or z:\n    w = 1"
    def test_structure_correct(self):
        decompiled = self.decompile()
        tree = self.verify_syntax(decompiled)
        self.assertIsNotNone(self.find_node(tree, ast.BoolOp))

class TestChainedCompare01(ControlFlowTestCase):
    SOURCE_CODE = "if 0 < x < 100:\n    y = 1"
    def test_structure_correct(self):
        decompiled = self.decompile()
        tree = self.verify_syntax(decompiled)
        compare = self.find_node(tree, ast.Compare)
        self.assertIsNotNone(compare)
        self.assertGreaterEqual(len(compare.ops), 2)

class TestChainedCompare02(ControlFlowTestCase):
    SOURCE_CODE = "if a <= b <= c:\n    y = 1"
    def test_structure_correct(self):
        decompiled = self.decompile()
        tree = self.verify_syntax(decompiled)
        compare = self.find_node(tree, ast.Compare)
        self.assertIsNotNone(compare)
        self.assertGreaterEqual(len(compare.ops), 2)

class TestChainedCompare03(ControlFlowTestCase):
    SOURCE_CODE = "if 0 < x < y < 100:\n    z = 1"
    def test_structure_correct(self):
        decompiled = self.decompile()
        tree = self.verify_syntax(decompiled)
        compare = self.find_node(tree, ast.Compare)
        self.assertIsNotNone(compare)
        self.assertGreaterEqual(len(compare.ops), 3)


class TestAssert01(ControlFlowTestCase):
    SOURCE_CODE = "assert x > 0"
    def test_structure_correct(self):
        decompiled = self.decompile()
        tree = self.verify_syntax(decompiled)
        self.assertIsNotNone(self.find_node(tree, ast.Assert))

class TestAssert02(ControlFlowTestCase):
    SOURCE_CODE = "assert x > 0, 'x must be positive'"
    def test_structure_correct(self):
        decompiled = self.decompile()
        tree = self.verify_syntax(decompiled)
        self.assertIsNotNone(self.find_node(tree, ast.Assert))


class TestMatch01(ControlFlowTestCase):
    SOURCE_CODE = "match x:\n    case 1:\n        y = 'one'\n    case 2:\n        y = 'two'\n    case _:\n        y = 'other'"
    def test_structure_correct(self):
        decompiled = self.decompile()
        tree = self.verify_syntax(decompiled)
        self.assertIsNotNone(self.find_node(tree, ast.Match))

class TestMatch02(ControlFlowTestCase):
    SOURCE_CODE = "match x:\n    case [a, b]:\n        y = a + b\n    case _:\n        y = 0"
    def test_structure_correct(self):
        decompiled = self.decompile()
        tree = self.verify_syntax(decompiled)
        self.assertIsNotNone(self.find_node(tree, ast.Match))

class TestMatch03(ControlFlowTestCase):
    SOURCE_CODE = "match x:\n    case {'key': v}:\n        y = v\n    case _:\n        y = None"
    def test_structure_correct(self):
        decompiled = self.decompile()
        tree = self.verify_syntax(decompiled)
        self.assertIsNotNone(self.find_node(tree, ast.Match))
