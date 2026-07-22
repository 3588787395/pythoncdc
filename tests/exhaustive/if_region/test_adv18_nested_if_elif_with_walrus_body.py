import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))
from tests.exhaustive.base import ExhaustiveTestCase


class TestAdv18NestedIfElifWithWalrusBody(ExhaustiveTestCase):
    # 嵌套 if-elif 中含 walrus 在 body 中（赋值并使用）：
    # def f(data):
    #     if data:
    #         if (n := len(data)) > 10:
    #             return 'long'
    #         elif n > 5:
    #             return 'mid'
    #         else:
    #             return 'short'
    #     return None
    # 字节码 COPY + STORE_FAST n + COMPARE_OP / 反编译器在嵌套 if-elif 中
    # 内层 elif 条件含 walrus 时易把 walrus 错挂到外层 if body。
    SOURCE_CODE = """def f(data):
    if data:
        if (n := len(data)) > 10:
            return 'long'
        elif n > 5:
            return 'mid'
        else:
            return 'short'
    return None"""
    REGION_TYPE = "IF_REGION"

    def test_decompile(self):
        self.verify_decompilation()
