import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))
from tests.exhaustive.base import ExhaustiveTestCase


class TestAdv19WhileElseBreakInElifBody(ExhaustiveTestCase):
    # elif body 内含 while-else + break + continue：
    # def f(items, mode):
    #     if mode == 'a':
    #         return 'a_mode'
    #     elif mode == 'b':
    #         i = 0
    #         while i < len(items):
    #             if items[i] == 'stop':
    #                 break
    #             i += 1
    #         else:
    #             return 'no_stop'
    #         return items[i]
    #     else:
    #         return 'unknown'
    # 字节码 WHILE + POP_JUMP_IF_FALSE + JUMP_BACKWARD + GET_ITER
    # / 反编译器在 elif body 内 while-else + break 时易把 else 错挂到 if 上。
    SOURCE_CODE = """def f(items, mode):
    if mode == 'a':
        return 'a_mode'
    elif mode == 'b':
        i = 0
        while i < len(items):
            if items[i] == 'stop':
                break
            i += 1
        else:
            return 'no_stop'
        return items[i]
    else:
        return 'unknown'"""
    REGION_TYPE = "IF_REGION"

    def test_decompile(self):
        self.verify_decompilation()
