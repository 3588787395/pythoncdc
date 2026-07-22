import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))
from tests.exhaustive.base import ExhaustiveTestCase


class TestR1AssertSimple(ExhaustiveTestCase):
    """Bug 3: assert(ternary) — 三元条件被折叠为 BoolOp，丢失 IfExp。

    原始: assert (a if a > 0 else 0)
    错误反编译:
        assert (a > 0 and a)
    缺陷: assert 的参数是一个 IfExp 表达式，反编译器误把
         ternary 折叠成 `a > 0 and a` 的 BoolOp（短路语义），
         实际上当 a <= 0 时原表达式应抛 AssertionError，
         而折叠后 a <= 0 时 assert 不抛错（因 a 已被求值），
         行为发生实质改变。IfExp AST 节点缺失。
    """
    SOURCE_CODE = """assert (a if a > 0 else 0)"""
    REGION_TYPE = "TERNARY"

    def test_decompile(self):
        self.verify_decompilation()
