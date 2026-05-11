import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))
from tests.exhaustive.base import ExhaustiveTestCase


class TestB23YieldFrom_Expr(ExhaustiveTestCase):
    SOURCE_CODE = """def f():
    yield from func()"""
    REGION_TYPE = "BASIC"

    def test_decompile(self):
        self.verify_decompilation()


class TestB23YieldFrom_Attr(ExhaustiveTestCase):
    SOURCE_CODE = """def f():
    yield from obj.iter"""
    REGION_TYPE = "BASIC"

    def test_decompile(self):
        self.verify_decompilation()


class TestB23YieldFrom_Subscript(ExhaustiveTestCase):
    SOURCE_CODE = """def f():
    yield from items[0]"""
    REGION_TYPE = "BASIC"

    def test_decompile(self):
        self.verify_decompilation()


class TestB23YieldFrom_Chain(ExhaustiveTestCase):
    SOURCE_CODE = """def f():
    yield from a
    yield from b
    yield from c"""
    REGION_TYPE = "BASIC"

    def test_decompile(self):
        self.verify_decompilation()


class TestB23YieldFrom_Mixed(ExhaustiveTestCase):
    SOURCE_CODE = """def f():
    yield 1
    yield from gen()
    yield 2"""
    REGION_TYPE = "BASIC"

    def test_decompile(self):
        self.verify_decompilation()


class TestB23YieldFrom_InLoop(ExhaustiveTestCase):
    SOURCE_CODE = """def f():
    for i in range(3):
        yield from i"""
    REGION_TYPE = "FOR_LOOP"

    def test_decompile(self):
        self.verify_decompilation()


class TestB23YieldFrom_ComplexExpr(ExhaustiveTestCase):
    SOURCE_CODE = """def f():
    yield from (x for x in range(10))"""
    REGION_TYPE = "BASIC"

    def test_decompile(self):
        self.verify_decompilation()
