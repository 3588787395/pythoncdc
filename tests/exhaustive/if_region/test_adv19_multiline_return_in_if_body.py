import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))
from tests.exhaustive.base import ExhaustiveTestCase


class TestAdv19MultilineReturnInIfBody(ExhaustiveTestCase):
    # if body 内含多行 return + ternary + 多行字典构造 + 嵌套 if：
    # def f(x):
    #     if x > 0:
    #         result = {
    #             'value': x,
    #             'category': 'pos' if x < 10 else 'big',
    #             'doubled': x * 2,
    #         }
    #         if result['doubled'] > 100:
    #             return {**result, 'overflow': True}
    #         return result
    #     return None
    # 字节码 BUILD_MAP / FORMAT_VALUE / STORE_FAST / LOAD_FAST / COMPARE_OP
    # / 反编译器在 if body 内多行 dict 字面量 + 嵌套 ternary + 后续 if 时易结构错乱。
    SOURCE_CODE = """def f(x):
    if x > 0:
        result = {
            'value': x,
            'category': 'pos' if x < 10 else 'big',
            'doubled': x * 2,
        }
        if result['doubled'] > 100:
            return {**result, 'overflow': True}
        return result
    return None"""
    REGION_TYPE = "IF_REGION"

    def test_decompile(self):
        self.verify_decompilation()
