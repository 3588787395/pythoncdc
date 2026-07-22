import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))
from tests.exhaustive.base import ExhaustiveTestCase


class TestAdv18DictLiteralInElifBody(ExhaustiveTestCase):
    # if-elif-else body 内含 dict 字面量赋值（多键 + 嵌套）：
    # if mode == 1:
    #     cfg = {'name': 'a', 'value': 1, 'nested': {'k': 'v'}}
    # elif mode == 2:
    #     cfg = {'name': 'b', 'value': 2, 'nested': {'k': 'w'}}
    # else:
    #     cfg = {'name': 'c', 'value': 3, 'nested': {'k': 'x'}}
    # 字节码 BUILD_MAP + LOAD_CONST keys / 反编译器在 if body 内含
    # 嵌套 dict 字面量时易丢失内层 dict 或错合并键值对。
    SOURCE_CODE = """if mode == 1:
    cfg = {'name': 'a', 'value': 1, 'nested': {'k': 'v'}}
elif mode == 2:
    cfg = {'name': 'b', 'value': 2, 'nested': {'k': 'w'}}
else:
    cfg = {'name': 'c', 'value': 3, 'nested': {'k': 'x'}}"""
    REGION_TYPE = "IF_REGION"

    def test_decompile(self):
        self.verify_decompilation()
