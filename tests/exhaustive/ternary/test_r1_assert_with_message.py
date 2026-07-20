import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))
from tests.exhaustive.base import ExhaustiveTestCase


class TestR1AssertWithMessage(ExhaustiveTestCase):
    """Bug 4: assert(ternary, msg) — 带消息的 assert 中三元被折叠为 BoolOp。

    原始: assert (a if a > 0 else 0), "error"
    错误反编译:
        assert (a > 0 and a), 'error'
    缺陷: assert 语句的第一个参数是 IfExp，反编译器误折叠为 BoolOp。
         与 Bug 3 同源，但此用例增加了 message 参数，验证折叠
         错误在带消息场景仍存在。IfExp AST 节点缺失。
    """
    SOURCE_CODE = '''assert (a if a > 0 else 0), "error"'''
    REGION_TYPE = "TERNARY"

    def test_decompile(self):
        self.verify_decompilation()
