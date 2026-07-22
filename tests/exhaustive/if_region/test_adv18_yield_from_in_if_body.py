import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))
from tests.exhaustive.base import ExhaustiveTestCase


class TestAdv18YieldFromInIfBody(ExhaustiveTestCase):
    # if-elif-else body 内分别含 yield from 表达式：
    # def gen():
    #     if x > 0:
    #         yield from [1, 2, 3]
    #     elif x < 0:
    #         yield from [-1, -2, -3]
    #     else:
    #         yield from [0]
    # 字节码 GET_YIELD_FROM_ITER + LOAD_CONST None + SEND + YIELD_VALUE 链
    # / 反编译器在 if-elif-else 三个分支都含 yield from 时易丢失中间分支。
    SOURCE_CODE = """def gen():
    if x > 0:
        yield from [1, 2, 3]
    elif x < 0:
        yield from [-1, -2, -3]
    else:
        yield from [0]"""
    REGION_TYPE = "IF_REGION"

    def test_decompile(self):
        self.verify_decompilation()
