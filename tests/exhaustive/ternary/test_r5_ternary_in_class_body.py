import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))
from tests.exhaustive.base import ExhaustiveTestCase


class TestR5TernaryInClassBody(ExhaustiveTestCase):
    """Bug R5-08: ternary 在 class body 多属性 + 方法 — 字节码不一致。

    原始:
        class C:
            x = a if c else b
            y = m if c else n
            def f(self):
                return self.x
    缺陷: R3 已通过单属性 class 场景（test_r3_ternary_class_attr）。
         R5 用多属性 + 方法的复合 class body 测试，加重 class code object
         内部嵌套结构复杂度。期望：class 内每个 ternary 属性正确归约；
         当前疑似第二个 ternary 之前泄漏条件表达式（与 R1 class_body_multi_ternary 同根因）。
    """
    SOURCE_CODE = """class C:
    x = a if c else b
    y = m if c else n
    def f(self):
        return self.x
"""
    REGION_TYPE = "TERNARY"

    def test_decompile(self):
        self.verify_decompilation()
