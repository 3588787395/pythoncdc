import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))
from tests.exhaustive.base import ExhaustiveTestCase


class TestAdv20YieldInWhileInIfBody(ExhaustiveTestCase):
    # if body 内含 while + yield + 嵌套 if-elif（生成器函数）：
    # def f(flag, items):
    #     if flag:
    #         i = 0
    #         while i < len(items):
    #             x = items[i]
    #             if x > 0:
    #                 yield x * 2
    #             elif x < 0:
    #                 yield -x
    #             else:
    #                 yield x
    #             i += 1
    #         return
    #     return
    # 字节码 YIELD_VALUE / GET_ITER / POP_JUMP_IF_FALSE
    # / 反编译器在 if body 内 while + yield + 嵌套 if-elif 时易丢失 yield 或 while 结构。
    SOURCE_CODE = """def f(flag, items):
    if flag:
        i = 0
        while i < len(items):
            x = items[i]
            if x > 0:
                yield x * 2
            elif x < 0:
                yield -x
            else:
                yield x
            i += 1
        return
    return"""
    REGION_TYPE = "IF_REGION"

    def test_decompile(self):
        self.verify_decompilation()
