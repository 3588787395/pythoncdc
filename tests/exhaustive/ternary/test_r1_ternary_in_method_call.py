import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))
from tests.exhaustive.base import ExhaustiveTestCase


class TestR1TernaryInMethodCall(ExhaustiveTestCase):
    """Bug 8: ternary 作为方法调用参数 — 字节码严重不一致，丢失方法调用。

    原始: obj.method(a if a > 0 else 0)
    错误反编译:
        (a if a > 0 else 0)
    缺陷: 原始是 LOAD_NAME obj; LOAD_METHOD method; <ternary>;
         PRECALL; CALL; POP_TOP 序列。反编译器只保留了 ternary 表达式，
         完全丢失 obj.method() 调用结构。IfExp 在 AST 中存在，
         但字节码指令序列与原始严重不一致（少了 LOAD_METHOD/PRECALL/CALL）。
    """
    SOURCE_CODE = """obj.method(a if a > 0 else 0)"""
    REGION_TYPE = "TERNARY"

    def test_decompile(self):
        self.verify_decompilation()
