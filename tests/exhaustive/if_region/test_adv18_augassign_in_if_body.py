import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))
from tests.exhaustive.base import ExhaustiveTestCase


class TestAdv18AugassignInIfBody(ExhaustiveTestCase):
    # if-elif-else body 内含复合 augassign（+=, *=, //=）：
    # def f(x, total):
    #     if x > 0:
    #         total += x
    #         total *= 2
    #     elif x < 0:
    #         total -= abs(x)
    #     else:
    #         total //= 2
    #     return total
    # 字节码 LOAD_FAST total / LOAD_FAST x / BINARY_OP += / STORE_FAST total
    # / 反编译器在 if body 内多个复合 augassign 时易丢失第二个 augassign。
    SOURCE_CODE = """def f(x, total):
    if x > 0:
        total += x
        total *= 2
    elif x < 0:
        total -= abs(x)
    else:
        total //= 2
    return total"""
    REGION_TYPE = "IF_REGION"

    def test_decompile(self):
        self.verify_decompilation()
