import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))
from tests.exhaustive.base import ExhaustiveTestCase


class TestR7TernaryInClassAttr(ExhaustiveTestCase):
    """Bug R7: 类属性 = ternary 在 BinOp 中 — 字节码不一致。

    原始:
        class C:
            x = (a if c else b) + 1
    缺陷: ternary 作为类属性赋值 RHS 的一部分（嵌入 BinOp）。R3 已测
         简单 class attr ternary (test_r3_ternary_class_attr)，R5 测
         多属性 + 方法变体 (test_r5_ternary_in_class_body)。R7 测
         ternary 嵌入 BinOp 的变体：类 code object 内 ternary merge
         块后还有 BINARY_OP 消费，可能让 ternary 的 value_target 推断
         失败，进而退化。
    """
    SOURCE_CODE = """class C:
    x = (a if c else b) + 1
"""
    REGION_TYPE = "TERNARY"

    def test_decompile(self):
        self.verify_decompilation()
