import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))
from tests.exhaustive.base import ExhaustiveTestCase


class TestR8TernaryInLambdaComprehension(ExhaustiveTestCase):
    """Bug R8: lambda 内 comprehension 含 ternary — 字节码不一致。

    原始:
        f = lambda items: [x if c else y for x in items]
    缺陷: lambda 内的 listcomp 包含 ternary 表达式。lambda 与
         listcomp 都是独立 code object。R8 测嵌套 code object 边界：
         listcomp 的 BUILD_LIST 0 + LIST_APPEND 在 inner code object，
         ternary merge 块在 listcomp code object 内部，与 lambda
         外层 code object 的边界可能冲突。
    """
    SOURCE_CODE = """f = lambda items: [x if c else y for x in items]
"""
    REGION_TYPE = "TERNARY"

    def test_decompile(self):
        self.verify_decompilation()
