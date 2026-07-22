import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))
from tests.exhaustive.base import ExhaustiveTestCase


class TestAdv18ForElseNestedInIfBody(ExhaustiveTestCase):
    # if body 内嵌套 for-else + if-elif-else 复杂结构：
    # def f(items):
    #     if flag:
    #         for x in items:
    #             if x > 0:
    #                 continue
    #             elif x < 0:
    #                 break
    #         else:
    #             return -1
    #         return x
    #     return 0
    # 字节码 FOR_ITER + POP_JUMP_IF_FALSE 链 + JUMP_BACKWARD + RETURN
    # / 反编译器在 if body 内 for-else + 嵌套 if-elif-else + 多 return 时
    # 易把 for-else 的 else 错挂到 if 上，或丢失 break。
    SOURCE_CODE = """def f(items):
    if flag:
        for x in items:
            if x > 0:
                continue
            elif x < 0:
                break
        else:
            return -1
        return x
    return 0"""
    REGION_TYPE = "IF_REGION"

    def test_decompile(self):
        self.verify_decompilation()
