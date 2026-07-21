import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))
from tests.exhaustive.base import ExhaustiveTestCase


class TestR15TernaryIssubclassSecondArg(ExhaustiveTestCase):
    """Bug R15 (new): issubclass(X, (a if c else b)) — issubclass 第二参数 ternary。

    原始:
        issubclass(X, (a if c else b))
    缺陷: ternary 作为 issubclass 第二位置参数（带括号），X 作为第一位置参数。
         cond_block preload 含 PUSH_NULL + LOAD issubclass + LOAD X，ternary
         merge 块栈顶由 PRECALL + CALL 2 消费。R15 isinstance 测过类似模式，
         本测试测 issubclass 同结构但不同内置函数变体。
    """
    SOURCE_CODE = """issubclass(X, (a if c else b))
"""
    REGION_TYPE = "TERNARY"

    def test_decompile(self):
        self.verify_decompilation()
