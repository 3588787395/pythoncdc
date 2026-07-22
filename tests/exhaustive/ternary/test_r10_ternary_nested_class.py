import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))
from tests.exhaustive.base import ExhaustiveTestCase


class TestR10TernaryNestedClass(ExhaustiveTestCase):
    """Bug R10: nested class + ternary — 字节码不一致。

    原始:
        class Outer:
            x = a if c else b
            class Inner:
                y = d if e else f
    缺陷: 嵌套类中两个 ternary 在不同 code object（Outer 与 Inner）。
         依「自底向上归约」原则，Inner 类的 ternary 先归约，Outer 类的
         ternary 后归约，但 Inner 类作为 Outer 类体中的一个抽象节点
         （LOAD_BUILD_CLASS + MAKE_FUNCTION + CALL 构建类），其 ternary
         在外层可见时可能与外层 ternary 归属冲突。R9 已测 metaclass
         class body ternary；R10 测 nested class 变体。
    """
    SOURCE_CODE = """class Outer:
    x = a if c else b
    class Inner:
        y = d if e else f
"""
    REGION_TYPE = "TERNARY"

    def test_decompile(self):
        self.verify_decompilation()
