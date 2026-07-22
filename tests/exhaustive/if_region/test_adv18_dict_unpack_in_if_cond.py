import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))
from tests.exhaustive.base import ExhaustiveTestCase


class TestAdv18DictUnpackInIfCond(ExhaustiveTestCase):
    # if 条件含 ** 解包 dict 字面量作函数参数 + 比较：
    # if f(**{'a': 1, 'b': 2}) > 0:
    #     r = 1
    # elif f(**{'c': 3}) < 0:
    #     r = -1
    # else:
    #     r = 0
    # 字节码 BUILD_MAP + DICT_MERGE / KW_NAMES / CALL_KW / 反编译器在 if 条件中
    # 含 ** 解包 dict 字面量作函数 kwargs 时易丢失 ** 标记或错合并键值对。
    SOURCE_CODE = """if f(**{'a': 1, 'b': 2}) > 0:
    r = 1
elif f(**{'c': 3}) < 0:
    r = -1
else:
    r = 0"""
    REGION_TYPE = "IF_REGION"

    def test_decompile(self):
        self.verify_decompilation()
