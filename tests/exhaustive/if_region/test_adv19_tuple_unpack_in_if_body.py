import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))
from tests.exhaustive.base import ExhaustiveTestCase


class TestAdv19TupleUnpackInIfBody(ExhaustiveTestCase):
    # if-elif-else body 内含 tuple unpacking + starred + 嵌套 if：
    # def f(items, mode):
    #     if mode == 'a':
    #         a, b, *c = items
    #         if a > b:
    #             return c
    #         return a + b
    #     elif mode == 'b':
    #         (a, b), c = items
    #         return a + b + c
    #     else:
    #         *a, b = items
    #         return a, b
    # 字节码 UNPACK_SEQUENCE / UNPACK_EX / STORE_FAST
    # / 反编译器在 if-elif-else body 内 tuple unpacking + starred + 嵌套结构时易结构错乱。
    SOURCE_CODE = """def f(items, mode):
    if mode == 'a':
        a, b, *c = items
        if a > b:
            return c
        return a + b
    elif mode == 'b':
        (a, b), c = items
        return a + b + c
    else:
        *a, b = items
        return a, b"""
    REGION_TYPE = "IF_REGION"

    def test_decompile(self):
        self.verify_decompilation()
