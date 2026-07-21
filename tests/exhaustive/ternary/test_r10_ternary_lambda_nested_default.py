import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))
from tests.exhaustive.base import ExhaustiveTestCase


class TestR10TernaryLambdaNestedDefault(ExhaustiveTestCase):
    """Bug R10: nested ternary in default arg of lambda — 字节码不一致。

    原始:
        f = lambda x=(a if c else (d if e else f)): x
    缺陷: lambda 的 default arg 是嵌套 ternary（ternary 内嵌套 ternary）。
         嵌套 ternary 在外层 code object 计算（默认参数在函数定义时求值），
         内层 ternary merge 块是外层 ternary 的 then/else 分支之一。
         依「自底向上归约」原则：内层 ternary 先归约作为单个抽象节点，
         外层 ternary 后归约时引用内层 ternary 入口。MAKE_FUNCTION +
         LOAD_CONST defaults + BUILD_TUPLE 与嵌套 ternary merge 块归属
         可能冲突。依「父引用子入口」：外层 ternary 通过其 then/else 分支
         引用内层 ternary 入口。
    """
    SOURCE_CODE = """f = lambda x=(a if c else (d if e else f)): x
"""
    REGION_TYPE = "TERNARY"

    def test_decompile(self):
        self.verify_decompilation()
