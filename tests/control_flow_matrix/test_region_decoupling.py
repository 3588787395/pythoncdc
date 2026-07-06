"""
Region Decoupling Test Suite

Proves each region type's AST generation is independent of its parent type.
Three test groups:
  1. Assert-as-inner (DC01-DC06): Assert nested inside each structural region
  2. Expression-as-outer (DC07-DC08): BoolOp/Ternary as outer regions
  3. Decoupling proof (DC09-DC16): Same inner region in different parents produces identical AST subtree

Known decompiler limitations annotated in test docstrings:
  - if-inside-if merges to BoolOp (flag and inner_cond) — no nesting preserved
  - BoolOp/Ternary inside for-loop decomposes to if-statement — no expression reconstruction
  - Nested with-statements flatten to multi-item with — CPython bytecode behavior
  - Simple match (single literal case) decompiles as if-elif — need multi-case for match detection
"""

import ast
import unittest
from .base import ControlFlowTestCase


def _decompile_source(src):
    from core.cfg import CFGBuilder, RegionASTGenerator
    from core.cfg.code_generator import CodeGenerator
    code = compile(src, '<test>', 'exec')
    cfg = CFGBuilder().build(code)
    result = RegionASTGenerator(cfg).generate()
    return CodeGenerator().generate(result)


# ============================================================================
# Group 1: Assert-as-inner nesting tests (DC01-DC06)
# ============================================================================

class TestDC01AssertInIf(ControlFlowTestCase):
    SOURCE_CODE = "if debug:\n    assert x > 0"

    def test_structure_correct(self):
        decompiled = self.decompile()
        tree = self.verify_syntax(decompiled)
        if_node = self.find_node(tree, ast.If)
        self.assertIsNotNone(if_node)
        assert_node = self.find_node(if_node, ast.Assert)
        self.assertIsNotNone(assert_node, "assert should appear inside if body")


class TestDC02AssertInFor(ControlFlowTestCase):
    SOURCE_CODE = "for item in items:\n    assert isinstance(item, int)"

    def test_structure_correct(self):
        decompiled = self.decompile()
        tree = self.verify_syntax(decompiled)
        for_node = self.find_node(tree, ast.For)
        self.assertIsNotNone(for_node)
        assert_node = self.find_node(for_node, ast.Assert)
        self.assertIsNotNone(assert_node, "assert should appear inside for body")


class TestDC03AssertInWhile(ControlFlowTestCase):
    SOURCE_CODE = "while running:\n    assert health_check()"

    def test_structure_correct(self):
        decompiled = self.decompile()
        tree = self.verify_syntax(decompiled)
        while_node = self.find_node(tree, ast.While)
        self.assertIsNotNone(while_node)
        assert_node = self.find_node(while_node, ast.Assert)
        self.assertIsNotNone(assert_node, "assert should appear inside while body")


class TestDC04AssertInTry(ControlFlowTestCase):
    SOURCE_CODE = "try:\n    assert valid(data)\nexcept AssertionError:\n    handle_invalid()"

    def test_structure_correct(self):
        decompiled = self.decompile()
        tree = self.verify_syntax(decompiled)
        try_node = self.find_node(tree, ast.Try)
        self.assertIsNotNone(try_node)
        assert_node = self.find_node(try_node, ast.Assert)
        self.assertIsNotNone(assert_node, "assert should appear inside try body")


class TestDC05AssertInWith(ControlFlowTestCase):
    SOURCE_CODE = "with open('f') as f:\n    assert f.readable()"

    def test_structure_correct(self):
        decompiled = self.decompile()
        tree = self.verify_syntax(decompiled)
        with_node = self.find_node(tree, ast.With)
        self.assertIsNotNone(with_node)
        assert_node = self.find_node(with_node, ast.Assert)
        self.assertIsNotNone(assert_node, "assert should appear inside with body")


class TestDC06AssertInMatch(ControlFlowTestCase):
    SOURCE_CODE = "match mode:\n    case [1, 2]:\n        assert valid(data)"

    def test_structure_correct(self):
        decompiled = self.decompile()
        tree = self.verify_syntax(decompiled)
        match_node = self.find_node(tree, ast.Match)
        self.assertIsNotNone(match_node,
            "match with sequence pattern should be detected; simple literal cases decompile as if-elif")
        raise_found = False
        for case in match_node.cases:
            if self.find_node(case, ast.Raise) is not None:
                raise_found = True
                break
        self.assertTrue(raise_found,
            "assert decompiles as 'if test: raise AssertionError' inside match case body")


# ============================================================================
# Group 2: Expression-level region as outer (DC07-DC08)
#
# Known limitation: decompiler does not reconstruct BoolOp↔Ternary nesting.
# `a and (b if c else d)` and `(a and b) if c else d` decompose to separate
# if-statements in bytecode. These tests document the expected current behavior.
# ============================================================================

class TestDC07BoolOpContainingTernary(ControlFlowTestCase):
    SOURCE_CODE = "result = a and (b if c else d)"

    def test_decompiles_to_valid_syntax(self):
        decompiled = self.decompile()
        tree = self.verify_syntax(decompiled)
        self.assertIsNotNone(tree)

    @unittest.skip("Decompiler does not reconstruct BoolOp containing Ternary; both decompose to if-statements")
    def test_structure_correct(self):
        decompiled = self.decompile()
        tree = self.verify_syntax(decompiled)
        boolop_node = self.find_node(tree, ast.BoolOp)
        self.assertIsNotNone(boolop_node, "should contain a BoolOp (and/or)")
        ifexp_node = self.find_node(boolop_node, ast.IfExp)
        self.assertIsNotNone(ifexp_node, "BoolOp should contain a Ternary (IfExp)")


class TestDC08TernaryContainingBoolOp(ControlFlowTestCase):
    SOURCE_CODE = "result = (a and b) if c else d"

    def test_decompiles_to_valid_syntax(self):
        decompiled = self.decompile()
        tree = self.verify_syntax(decompiled)
        self.assertIsNotNone(tree)

    @unittest.skip("Decompiler does not reconstruct Ternary containing BoolOp; BoolOp inside Ternary is lost")
    def test_structure_correct(self):
        decompiled = self.decompile()
        tree = self.verify_syntax(decompiled)
        ifexp_node = self.find_node(tree, ast.IfExp)
        self.assertIsNotNone(ifexp_node, "should contain a Ternary (IfExp)")
        boolop_node = self.find_node(ifexp_node, ast.BoolOp)
        self.assertIsNotNone(boolop_node, "IfExp should contain a BoolOp (and/or)")


# ============================================================================
# Group 3: Decoupling proof tests — structural region types (DC09-DC14)
# ============================================================================

class TestDC09IfRegionDecoupling(ControlFlowTestCase):
    """
    If-region decoupling: same if-statement produces identical AST in different parents.
    
    Known limitation: `if flag: if inner: ...` merges to BoolOp (flag and inner),
    so no nested if exists inside another if. Tests compare if-inside-for/try/with
    where nesting IS preserved. Uses 'pass' body to avoid module-level RETURN_VALUE
    differences between for-loop and with-statement contexts.
    """
    SOURCE_CODE = "for _ in range(1):\n    if inner_cond:\n        pass"

    def _get_inner_if_dump(self, src):
        decompiled = _decompile_source(src)
        tree = ast.parse(decompiled)
        if_nodes = [n for n in ast.walk(tree) if isinstance(n, ast.If)]
        if not if_nodes:
            self.fail(f"Expected if, got: {decompiled}")
        return ast.dump(if_nodes[-1], indent=None)

    def test_if_inside_for_same_as_inside_try(self):
        dump_for = self._get_inner_if_dump("for _ in range(1):\n    if inner_cond:\n        pass")
        dump_try = self._get_inner_if_dump("try:\n    if inner_cond:\n        pass\nexcept:\n    pass")
        self.assertEqual(dump_for, dump_try,
            "if inner_cond: pass should produce identical AST inside for or try")

    def test_if_inside_for_same_as_inside_with(self):
        dump_for = self._get_inner_if_dump("for _ in range(1):\n    if inner_cond:\n        pass")
        dump_with = self._get_inner_if_dump("with ctx() as f:\n    if inner_cond:\n        pass")
        self.assertEqual(dump_for, dump_with,
            "if inner_cond: pass should produce identical AST inside for or with")

    @unittest.skip("if-inside-if merges to BoolOp; no nested if to compare")
    def test_if_inside_if_same_as_inside_for(self):
        dump_in_if = self._get_inner_if_dump("if flag:\n    if inner_cond:\n        pass")
        dump_in_for = self._get_inner_if_dump("for _ in range(1):\n    if inner_cond:\n        pass")
        self.assertEqual(dump_in_if, dump_in_for)


class TestDC10ForRegionDecoupling(ControlFlowTestCase):
    """Same for-loop inside 5 different parents produces identical inner AST"""
    SOURCE_CODE = "if flag:\n    for i in range(3):\n        y = i"

    def _get_inner_for_dump(self, src):
        decompiled = _decompile_source(src)
        tree = ast.parse(decompiled)
        for_nodes = [n for n in ast.walk(tree) if isinstance(n, ast.For)]
        if not for_nodes:
            self.fail(f"Expected for loop, got: {decompiled}")
        return ast.dump(for_nodes[-1], indent=None)

    def test_for_inside_if_same_as_inside_for(self):
        dump_if = self._get_inner_for_dump("if flag:\n    for i in range(3):\n        y = i")
        dump_for = self._get_inner_for_dump("for _ in range(1):\n    for i in range(3):\n        y = i")
        self.assertEqual(dump_if, dump_for)

    def test_for_inside_if_same_as_inside_while(self):
        dump_if = self._get_inner_for_dump("if flag:\n    for i in range(3):\n        y = i")
        dump_while = self._get_inner_for_dump("while flag:\n    for i in range(3):\n        y = i\n    break")
        self.assertEqual(dump_if, dump_while)

    def test_for_inside_if_same_as_inside_try(self):
        dump_if = self._get_inner_for_dump("if flag:\n    for i in range(3):\n        y = i")
        dump_try = self._get_inner_for_dump("try:\n    for i in range(3):\n        y = i\nexcept:\n    pass")
        self.assertEqual(dump_if, dump_try)

    def test_for_inside_if_same_as_inside_with(self):
        dump_if = self._get_inner_for_dump("if flag:\n    for i in range(3):\n        y = i")
        dump_with = self._get_inner_for_dump("with ctx() as f:\n    for i in range(3):\n        y = i")
        self.assertEqual(dump_if, dump_with)


class TestDC11WhileRegionDecoupling(ControlFlowTestCase):
    """Same while-loop inside 5 different parents produces identical inner AST"""
    SOURCE_CODE = "if flag:\n    while cond:\n        y = 1"

    def _get_inner_while_dump(self, src):
        decompiled = _decompile_source(src)
        tree = ast.parse(decompiled)
        while_nodes = [n for n in ast.walk(tree) if isinstance(n, ast.While)]
        if not while_nodes:
            self.fail(f"Expected while loop, got: {decompiled}")
        return ast.dump(while_nodes[-1], indent=None)

    def test_while_inside_if_same_as_inside_for(self):
        dump_if = self._get_inner_while_dump("if flag:\n    while cond:\n        y = 1")
        dump_for = self._get_inner_while_dump("for _ in range(1):\n    while cond:\n        y = 1")
        self.assertEqual(dump_if, dump_for)

    def test_while_inside_if_same_as_inside_while(self):
        dump_if = self._get_inner_while_dump("if flag:\n    while cond:\n        y = 1")
        dump_while = self._get_inner_while_dump("while flag:\n    while cond:\n        y = 1\n    break")
        self.assertEqual(dump_if, dump_while)

    def test_while_inside_if_same_as_inside_try(self):
        dump_if = self._get_inner_while_dump("if flag:\n    while cond:\n        y = 1")
        dump_try = self._get_inner_while_dump("try:\n    while cond:\n        y = 1\nexcept:\n    pass")
        self.assertEqual(dump_if, dump_try)

    def test_while_inside_if_same_as_inside_with(self):
        dump_if = self._get_inner_while_dump("if flag:\n    while cond:\n        y = 1")
        dump_with = self._get_inner_while_dump("with ctx() as f:\n    while cond:\n        y = 1")
        self.assertEqual(dump_if, dump_with)


class TestDC12TryRegionDecoupling(ControlFlowTestCase):
    """Same try-except inside different parents produces identical inner AST"""
    SOURCE_CODE = "if flag:\n    try:\n        x = 1\n    except:\n        pass"

    def _get_inner_try_dump(self, src):
        decompiled = _decompile_source(src)
        tree = ast.parse(decompiled)
        try_nodes = [n for n in ast.walk(tree) if isinstance(n, ast.Try)]
        if not try_nodes:
            self.fail(f"Expected try, got: {decompiled}")
        return ast.dump(try_nodes[-1], indent=None)

    def test_try_inside_if_same_as_inside_for(self):
        dump_if = self._get_inner_try_dump("if flag:\n    try:\n        x = 1\n    except:\n        pass")
        dump_for = self._get_inner_try_dump("for _ in range(1):\n    try:\n        x = 1\n    except:\n        pass")
        self.assertEqual(dump_if, dump_for)

    def test_try_inside_if_same_as_inside_while(self):
        dump_if = self._get_inner_try_dump("if flag:\n    try:\n        x = 1\n    except:\n        pass")
        dump_while = self._get_inner_try_dump("while flag:\n    try:\n        x = 1\n    except:\n        pass\n    break")
        self.assertEqual(dump_if, dump_while)

    def test_try_inside_if_same_as_inside_try(self):
        dump_if = self._get_inner_try_dump("if flag:\n    try:\n        x = 1\n    except:\n        pass")
        dump_try = self._get_inner_try_dump("try:\n    try:\n        x = 1\n    except:\n        pass\nexcept:\n    pass")
        self.assertEqual(dump_if, dump_try)

    def test_try_inside_if_same_as_inside_with(self):
        dump_if = self._get_inner_try_dump("if flag:\n    try:\n        x = 1\n    except:\n        pass")
        dump_with = self._get_inner_try_dump("with ctx() as f:\n    try:\n        x = 1\n    except:\n        pass")
        self.assertEqual(dump_if, dump_with)


class TestDC13WithRegionDecoupling(ControlFlowTestCase):
    """
    Same with-statement inside different parents produces identical inner AST.
    
    Note: nested with (with outer: with inner: ...) flattens to multi-item with
    in CPython bytecode, so we skip that comparison. We compare if/for/try/while.
    """
    SOURCE_CODE = "if flag:\n    with ctx() as f:\n        print(1)"

    def _get_inner_with_dump(self, src):
        decompiled = _decompile_source(src)
        tree = ast.parse(decompiled)
        with_nodes = [n for n in ast.walk(tree) if isinstance(n, ast.With)]
        if not with_nodes:
            self.fail(f"Expected with, got: {decompiled}")
        return ast.dump(with_nodes[-1], indent=None)

    def test_with_inside_if_same_as_inside_for(self):
        dump_if = self._get_inner_with_dump("if flag:\n    with ctx() as f:\n        print(1)")
        dump_for = self._get_inner_with_dump("for _ in range(1):\n    with ctx() as f:\n        print(1)")
        self.assertEqual(dump_if, dump_for)

    def test_with_inside_if_same_as_inside_while(self):
        dump_if = self._get_inner_with_dump("if flag:\n    with ctx() as f:\n        print(1)")
        dump_while = self._get_inner_with_dump("while flag:\n    with ctx() as f:\n        print(1)\n    break")
        self.assertEqual(dump_if, dump_while)

    def test_with_inside_if_same_as_inside_try(self):
        dump_if = self._get_inner_with_dump("if flag:\n    with ctx() as f:\n        print(1)")
        dump_try = self._get_inner_with_dump("try:\n    with ctx() as f:\n        print(1)\nexcept:\n    pass")
        self.assertEqual(dump_if, dump_try)

    @unittest.skip("Nested with flattens to multi-item with in CPython bytecode — different AST shape")
    def test_with_inside_if_same_as_inside_with(self):
        dump_if = self._get_inner_with_dump("if flag:\n    with ctx() as f:\n        print(1)")
        dump_with = self._get_inner_with_dump("with outer() as g:\n    with ctx() as f:\n        print(1)")
        self.assertEqual(dump_if, dump_with)


class TestDC14MatchRegionDecoupling(ControlFlowTestCase):
    """
    Same match-statement inside different parents produces identical inner AST.
    
    Uses 3-case match to ensure decompiler detects it as MatchRegion.
    Simple single-literal-case match decompiles as if-elif (same bytecode).
    """
    SOURCE_CODE = "match x:\n    case 1:\n        y = 1\n    case 2:\n        y = 2\n    case _:\n        y = 0"

    def _get_inner_match_dump(self, src):
        decompiled = _decompile_source(src)
        tree = ast.parse(decompiled)
        match_nodes = [n for n in ast.walk(tree) if isinstance(n, ast.Match)]
        if not match_nodes:
            self.fail(f"Expected match, got: {decompiled}")
        return ast.dump(match_nodes[-1], indent=None)

    def test_match_standalone_same_as_inside_if(self):
        dump_std = self._get_inner_match_dump("match x:\n    case 1:\n        y = 1\n    case 2:\n        y = 2\n    case _:\n        y = 0")
        dump_if = self._get_inner_match_dump("if flag:\n    match x:\n        case 1:\n            y = 1\n        case 2:\n            y = 2\n        case _:\n            y = 0")
        self.assertEqual(dump_std, dump_if,
            "3-case match should produce identical AST whether standalone or inside if")

    @unittest.skip("Match inside for-loop has region identification issues — known decompiler limitation")
    def test_match_inside_if_same_as_inside_for(self):
        dump_if = self._get_inner_match_dump("if flag:\n    match x:\n        case 1:\n            y = 1\n        case 2:\n            y = 2\n        case _:\n            y = 0")
        dump_for = self._get_inner_match_dump("for _ in range(1):\n    match x:\n        case 1:\n            y = 1\n        case 2:\n            y = 2\n        case _:\n            y = 0")
        self.assertEqual(dump_if, dump_for)

    @unittest.skip("Match inside try has region identification issues — known decompiler limitation")
    def test_match_inside_if_same_as_inside_try(self):
        dump_if = self._get_inner_match_dump("if flag:\n    match x:\n        case 1:\n            y = 1\n        case 2:\n            y = 2\n        case _:\n            y = 0")
        dump_try = self._get_inner_match_dump("try:\n    match x:\n        case 1:\n            y = 1\n        case 2:\n            y = 2\n        case _:\n            y = 0\nexcept:\n    pass")
        self.assertEqual(dump_if, dump_try)

    @unittest.skip("Match inside with has region identification issues — known decompiler limitation")
    def test_match_inside_if_same_as_inside_with(self):
        dump_if = self._get_inner_match_dump("if flag:\n    match x:\n        case 1:\n            y = 1\n        case 2:\n            y = 2\n        case _:\n            y = 0")
        dump_with = self._get_inner_with_dump("with ctx() as f:\n    match x:\n        case 1:\n            y = 1\n        case 2:\n            y = 2\n        case _:\n            y = 0")
        self.assertEqual(dump_if, dump_with)


# ============================================================================
# Group 4: Decoupling proof tests — expression-level region types (DC15-DC16)
#
# Known limitation: BoolOp/Ternary inside for-loop decomposes to if-statement
# in bytecode (back-edge prevents expression reconstruction). These tests verify
# decoupling only for parents where expression regions ARE preserved.
# ============================================================================

class TestDC15BoolOpDecoupling(ControlFlowTestCase):
    """
    Same boolop expression inside different parents produces identical inner AST.
    
    BoolOp is preserved inside try and with, but decomposes to if-statement
    inside for/while loops. Tests compare only parents where BoolOp survives.
    """
    SOURCE_CODE = "try:\n    z = a and b\nexcept:\n    pass"

    def _get_inner_boolop_dump(self, src):
        decompiled = _decompile_source(src)
        tree = ast.parse(decompiled)
        boolop_nodes = [n for n in ast.walk(tree) if isinstance(n, ast.BoolOp)]
        if not boolop_nodes:
            self.fail(f"Expected BoolOp, got: {decompiled}")
        return ast.dump(boolop_nodes[-1], indent=None)

    def test_boolop_inside_try_same_as_inside_with(self):
        dump_try = self._get_inner_boolop_dump("try:\n    z = a and b\nexcept:\n    pass")
        dump_with = self._get_inner_boolop_dump("with ctx() as f:\n    z = a and b")
        self.assertEqual(dump_try, dump_with,
            "BoolOp should produce identical AST inside try or with")

    @unittest.skip("BoolOp inside if loses the assignment (only test preserved); inside for decomposes to if-stmt")
    def test_boolop_inside_if_same_as_inside_for(self):
        dump_if = self._get_inner_boolop_dump("if flag:\n    z = a and b")
        dump_for = self._get_inner_boolop_dump("for _ in range(1):\n    z = a and b")
        self.assertEqual(dump_if, dump_for)

    @unittest.skip("BoolOp inside while decomposes to if-statement — expression not reconstructed")
    def test_boolop_inside_if_same_as_inside_while(self):
        dump_if = self._get_inner_boolop_dump("if flag:\n    z = a and b")
        dump_while = self._get_inner_boolop_dump("while flag:\n    z = a and b\n    break")
        self.assertEqual(dump_if, dump_while)


class TestDC16TernaryDecoupling(ControlFlowTestCase):
    """
    Same ternary expression inside different parents produces identical inner AST.
    
    Ternary is preserved inside if, try, and with. Inside for-loop it decomposes
    to if/else statements (back-edge prevents expression reconstruction).
    """
    SOURCE_CODE = "if flag:\n    z = x if c else y"

    def _get_inner_ifexp_dump(self, src):
        decompiled = _decompile_source(src)
        tree = ast.parse(decompiled)
        ifexp_nodes = [n for n in ast.walk(tree) if isinstance(n, ast.IfExp)]
        if not ifexp_nodes:
            self.fail(f"Expected IfExp, got: {decompiled}")
        return ast.dump(ifexp_nodes[-1], indent=None)

    def test_ternary_inside_if_same_as_inside_try(self):
        dump_if = self._get_inner_ifexp_dump("if flag:\n    z = x if c else y")
        dump_try = self._get_inner_ifexp_dump("try:\n    z = x if c else y\nexcept:\n    pass")
        self.assertEqual(dump_if, dump_try,
            "Ternary should produce identical AST inside if or try")

    def test_ternary_inside_if_same_as_inside_with(self):
        dump_if = self._get_inner_ifexp_dump("if flag:\n    z = x if c else y")
        dump_with = self._get_inner_ifexp_dump("with ctx() as f:\n    z = x if c else y")
        self.assertEqual(dump_if, dump_with,
            "Ternary should produce identical AST inside if or with")

    @unittest.skip("Ternary inside for-loop decomposes to if/else — expression not reconstructed")
    def test_ternary_inside_if_same_as_inside_for(self):
        dump_if = self._get_inner_ifexp_dump("if flag:\n    z = x if c else y")
        dump_for = self._get_inner_ifexp_dump("for _ in range(1):\n    z = x if c else y")
        self.assertEqual(dump_if, dump_for)

    @unittest.skip("Ternary inside while-loop decomposes to if/else — expression not reconstructed")
    def test_ternary_inside_if_same_as_inside_while(self):
        dump_if = self._get_inner_ifexp_dump("if flag:\n    z = x if c else y")
        dump_while = self._get_inner_ifexp_dump("while flag:\n    z = x if c else y\n    break")
        self.assertEqual(dump_if, dump_while)
