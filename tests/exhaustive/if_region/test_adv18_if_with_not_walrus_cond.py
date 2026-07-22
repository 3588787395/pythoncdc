import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))
from tests.exhaustive.base import ExhaustiveTestCase


class TestAdv18IfWithNotWalrusCond(ExhaustiveTestCase):
    # if 条件含 `not (x := expr)` 模式：
    # if not (x := compute()):
    #     r = 'empty'
    # elif x > 100:
    #     r = 'big'
    # else:
    #     r = 'small'
    # 字节码 LOAD_GLOBAL compute / PRECALL / CALL / COPY / STORE_NAME x /
    # POP_JUMP_IF_TRUE (because of `not`) / 反编译器在 if 条件含 not+walrus
    # 时易把 not 丢失或错识别为正向 walrus。
    SOURCE_CODE = """if not (x := compute()):
    r = 'empty'
elif x > 100:
    r = 'big'
else:
    r = 'small'"""
    REGION_TYPE = "IF_REGION"

    def test_decompile(self):
        self.verify_decompilation()
