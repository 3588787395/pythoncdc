import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))
from tests.exhaustive.base import ExhaustiveTestCase


class TestAdv19MixedComplexBranches(ExhaustiveTestCase):
    # if-elif-else 三分支各自含不同复杂语句：
    # if: for + break
    # elif: try/except + raise
    # else: with + nested if
    # def f(x, items):
    #     if x > 0:
    #         for item in items:
    #             if item == x:
    #                 break
    #         return 'found_pos'
    #     elif x < 0:
    #         try:
    #             raise ValueError('neg')
    #         except ValueError as e:
    #             return str(e)
    #     else:
    #         with open('log') as f:
    #             if f.read():
    #                 return 'has_log'
    #         return 'no_log'
    # 字节码 FOR_ITER + POP_JUMP_IF_FALSE / RAISE_VARARGS / BEFORE_WITH
    # / 反编译器在 if-elif-else 三分支各自含不同复杂语句时易结构错乱。
    SOURCE_CODE = """def f(x, items):
    if x > 0:
        for item in items:
            if item == x:
                break
        return 'found_pos'
    elif x < 0:
        try:
            raise ValueError('neg')
        except ValueError as e:
            return str(e)
    else:
        with open('log') as f:
            if f.read():
                return 'has_log'
        return 'no_log'"""
    REGION_TYPE = "IF_REGION"

    def test_decompile(self):
        self.verify_decompilation()
