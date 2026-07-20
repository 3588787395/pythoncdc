import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))
from tests.exhaustive.base import ExhaustiveTestCase


class TestAdv19YieldInElifBody(ExhaustiveTestCase):
    # elif body 内含 yield + 嵌套 if-else（生成器，R18 只测 if body 内 yield）：
    # def gen(x):
    #     if x > 0:
    #         yield 'pos'
    #     elif x < 0:
    #         if x < -10:
    #             yield 'very_neg'
    #         else:
    #             yield 'neg'
    #     else:
    #         yield 'zero'
    # 字节码 YIELD_VALUE / RESUME / POP_JUMP_IF_FALSE
    # / 反编译器在 elif body 内 yield + 嵌套 if-else 时易结构错乱。
    SOURCE_CODE = """def gen(x):
    if x > 0:
        yield 'pos'
    elif x < 0:
        if x < -10:
            yield 'very_neg'
        else:
            yield 'neg'
    else:
        yield 'zero'"""
    REGION_TYPE = "IF_REGION"

    def test_decompile(self):
        self.verify_decompilation()
