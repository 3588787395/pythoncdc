import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))
from tests.exhaustive.base import ExhaustiveTestCase


class TestAdv18ChainedCallInIfCond(ExhaustiveTestCase):
    # if 条件含深度链式属性/方法调用 a.b.c.d() + 比较：
    # if obj.a.b.c.get('key', 0) > 10:
    #     r = 1
    # elif obj.a.b.c.get('key', 0) < -10:
    #     r = -1
    # else:
    #     r = 0
    # 字节码 LOAD_NAME obj / LOAD_ATTR a / LOAD_ATTR b / LOAD_ATTR c /
    # LOAD_METHOD get / PRECALL/CALL / COMPARE_OP / POP_JUMP_IF_FALSE
    # / 反编译器在 if 条件中含深度链式属性 + 方法调用时易丢失中间属性。
    SOURCE_CODE = """if obj.a.b.c.get('key', 0) > 10:
    r = 1
elif obj.a.b.c.get('key', 0) < -10:
    r = -1
else:
    r = 0"""
    REGION_TYPE = "IF_REGION"

    def test_decompile(self):
        self.verify_decompilation()
