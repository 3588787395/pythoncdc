import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))
from tests.exhaustive.base import ExhaustiveTestCase


class TestAdv19WalrusInInIfCond(ExhaustiveTestCase):
    # if 条件含 walrus + in 集合字面量 + elif 链：
    # def f(get_x):
    #     if (x := get_x()) in [1, 2, 3]:
    #         return 'small'
    #     elif (x := get_x()) in [4, 5, 6]:
    #         return 'mid'
    #     elif (y := get_x()) > 100:
    #         return 'big'
    #     else:
    #         return 'none'
    # 字节码 LOAD_CONST list / CONTAINS_OP / STORE_FAST (walrus)
    # / 反编译器在 if-elif 条件含 walrus + in list 时易丢失 walrus 赋值。
    SOURCE_CODE = """def f(get_x):
    if (x := get_x()) in [1, 2, 3]:
        return 'small'
    elif (x := get_x()) in [4, 5, 6]:
        return 'mid'
    elif (y := get_x()) > 100:
        return 'big'
    else:
        return 'none'"""
    REGION_TYPE = "IF_REGION"

    def test_decompile(self):
        self.verify_decompilation()
