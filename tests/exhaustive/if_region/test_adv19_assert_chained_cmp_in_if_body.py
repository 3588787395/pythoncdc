import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))
from tests.exhaustive.base import ExhaustiveTestCase


class TestAdv19AssertChainedCmpInIfBody(ExhaustiveTestCase):
    # if-elif-else body 内含 assert + chained comparison message：
    # def f(x):
    #     if x > 0:
    #         assert 0 < x < 100, f'x out of range: {x}'
    #         return 'pos_valid'
    #     elif x < 0:
    #         assert -100 < x < 0, f'x too negative: {x}'
    #         return 'neg_valid'
    #     else:
    #         assert x == 0
    #         return 'zero'
    # 字节码 ASSERT_RAISE / COMPARE_OP / FORMAT_VALUE / LOAD_CONST
    # / 反编译器在 if-elif-else 三分支都含 assert + chained cmp + f-string msg 时易结构错乱。
    SOURCE_CODE = """def f(x):
    if x > 0:
        assert 0 < x < 100, f'x out of range: {x}'
        return 'pos_valid'
    elif x < 0:
        assert -100 < x < 0, f'x too negative: {x}'
        return 'neg_valid'
    else:
        assert x == 0
        return 'zero'"""
    REGION_TYPE = "IF_REGION"

    def test_decompile(self):
        self.verify_decompilation()
