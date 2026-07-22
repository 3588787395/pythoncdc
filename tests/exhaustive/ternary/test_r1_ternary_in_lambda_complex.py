import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))
from tests.exhaustive.base import ExhaustiveTestCase


class TestR1TernaryInLambdaComplex(ExhaustiveTestCase):
    """Bug 12: lambda body 是 (ternary) + 算术 — body 被替换为 None。

    原始: f = lambda x, y: (x if x > y else y) + 1
    错误反编译:
        f = lambda x, y: None
    缺陷: lambda body 是 `(ternary) + 1` 复合表达式。
         反编译器在递归处理 lambda 的内嵌 code object 时，
         未能重建 `IfExp + 1` 表达式，直接以 None 作为 body。
         IfExp AST 节点缺失，行为严重错误（lambda 返回 None 而非计算结果）。
    """
    SOURCE_CODE = """f = lambda x, y: (x if x > y else y) + 1"""
    REGION_TYPE = "TERNARY"

    def test_decompile(self):
        self.verify_decompilation()
