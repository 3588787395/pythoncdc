import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))
from tests.exhaustive.base import ExhaustiveTestCase


class TestAdv19WalrusComplexBoolopInIfCond(ExhaustiveTestCase):
    # if 条件含 walrus + complex boolop (4+ operands, mix and/or) + elif：
    # def f(get_a, get_b, get_c):
    #     if (a := get_a()) > 0 and (b := get_b()) > 0 and (c := get_c()) > 0:
    #         return 'all_pos'
    #     elif (a := get_a()) < 0 or (b := get_b()) < 0 or (c := get_c()) < 0:
    #         return 'some_neg'
    #     elif (a := get_a()) == 0:
    #         return 'a_zero'
    #     else:
    #         return 'other'
    # 字节码 LOAD_FAST / STORE_FAST (walrus) / COMPARE_OP / POP_JUMP_IF_FALSE
    # / 反编译器在 if-elif 条件含多 walrus + boolop 链时易归约错乱。
    SOURCE_CODE = """def f(get_a, get_b, get_c):
    if (a := get_a()) > 0 and (b := get_b()) > 0 and (c := get_c()) > 0:
        return 'all_pos'
    elif (a := get_a()) < 0 or (b := get_b()) < 0 or (c := get_c()) < 0:
        return 'some_neg'
    elif (a := get_a()) == 0:
        return 'a_zero'
    else:
        return 'other'"""
    REGION_TYPE = "IF_REGION"

    def test_decompile(self):
        self.verify_decompilation()
