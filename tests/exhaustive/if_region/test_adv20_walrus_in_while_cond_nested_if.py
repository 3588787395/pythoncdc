import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))
from tests.exhaustive.base import ExhaustiveTestCase


class TestAdv20WalrusInWhileCondNestedIf(ExhaustiveTestCase):
    # if body 内含 while + walrus 在条件 + 嵌套 if-else：
    # def f(items):
    #     if items:
    #         result = []
    #         it = iter(items)
    #         while (x := next(it, None)) is not None:
    #             if x > 0:
    #                 result.append('pos')
    #             elif x < 0:
    #                 result.append('neg')
    #             else:
    #                 result.append('zero')
    #         return result
    #     return []
    # 字节码 CALL next / COPY / STORE_FAST x / COMPARE_OP is not / POP_JUMP_IF_FALSE
    # / 反编译器在 if body 内 while+walrus+嵌套 if-elif-else 时易丢失 walrus 绑定。
    SOURCE_CODE = """def f(items):
    if items:
        result = []
        it = iter(items)
        while (x := next(it, None)) is not None:
            if x > 0:
                result.append('pos')
            elif x < 0:
                result.append('neg')
            else:
                result.append('zero')
        return result
    return []"""
    REGION_TYPE = "IF_REGION"

    def test_decompile(self):
        self.verify_decompilation()
