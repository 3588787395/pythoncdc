import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))
from tests.exhaustive.base import ExhaustiveTestCase


class TestAdv19ForContinueInEachBranch(ExhaustiveTestCase):
    # if-elif-else 三分支各自含 for + continue/break：
    # def f(items, mode):
    #     if mode == 'a':
    #         for x in items:
    #             if x < 0:
    #                 continue
    #             process_a(x)
    #         return 'a_done'
    #     elif mode == 'b':
    #         for x in items:
    #             if x > 100:
    #                 break
    #             process_b(x)
    #         return 'b_done'
    #     else:
    #         for x in items:
    #             process_c(x)
    #         return 'c_done'
    # 字节码 FOR_ITER / POP_JUMP_IF_FALSE / JUMP_BACKWARD / JUMP_ABSOLUTE
    # / 反编译器在 if-elif-else 三分支各自含 for + continue/break 时易结构错乱。
    SOURCE_CODE = """def f(items, mode):
    if mode == 'a':
        for x in items:
            if x < 0:
                continue
            process_a(x)
        return 'a_done'
    elif mode == 'b':
        for x in items:
            if x > 100:
                break
            process_b(x)
        return 'b_done'
    else:
        for x in items:
            process_c(x)
        return 'c_done'"""
    REGION_TYPE = "IF_REGION"

    def test_decompile(self):
        self.verify_decompilation()
