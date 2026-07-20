import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))
from tests.exhaustive.base import ExhaustiveTestCase


class TestR4TernaryAttrAssign(ExhaustiveTestCase):
    """Bug R4-11: ternary 作为 setattr 调用参数（属性名动态选择）— 字节码不一致。

    原始: setattr(obj, 'a' if cond else 'b', 1)
    缺陷: ternary 作为 setattr 第二参数（属性名字符串）时，PRECALL + CALL
         在 merge_block 中消费 ternary 结果与 value。setattr 是普通函数调用，
         但 ternary 作为参数位置在中间，反编译器可能丢失 setattr 结构。
    """
    SOURCE_CODE = """setattr(obj, 'a' if cond else 'b', 1)"""
    REGION_TYPE = "TERNARY"

    def test_decompile(self):
        self.verify_decompilation()
