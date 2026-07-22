import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))
from tests.exhaustive.base import ExhaustiveTestCase


class TestAdv18WhileBreakNestedInIfBody(ExhaustiveTestCase):
    # if body 内嵌套 while + if-elif-else + break/continue 复杂结构：
    # def f(items):
    #     if flag:
    #         i = 0
    #         while i < len(items):
    #             x = items[i]
    #             if x > 10:
    #                 break
    #             elif x < 0:
    #                 continue
    #             i += 1
    #         return i
    #     return -1
    # 字节码 while + POP_JUMP_IF_FALSE + 内嵌 if-elif-else + break/continue
    # / 反编译器在 if body 内 while + 嵌套 if-elif-else + flow control 时
    # 易把 break/continue 错挂到 if 而非 while。
    SOURCE_CODE = """def f(items):
    if flag:
        i = 0
        while i < len(items):
            x = items[i]
            if x > 10:
                break
            elif x < 0:
                continue
            i += 1
        return i
    return -1"""
    REGION_TYPE = "IF_REGION"

    def test_decompile(self):
        self.verify_decompilation()
