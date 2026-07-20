import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))
from tests.exhaustive.base import ExhaustiveTestCase


class TestAdv18DelInIfBody(ExhaustiveTestCase):
    # if-elif-else body 内分别含 del 语句：
    # if mode == 1:
    #     del cache[key1]
    #     del cache[key2]
    # elif mode == 2:
    #     del cache[key3]
    # else:
    #     del cache[key4]
    # 字节码 DELETE_SUBSCR / 反编译器在 if body 内多个 del 语句时
    # 易丢失第二个 del 或错合并 del。
    SOURCE_CODE = """if mode == 1:
    del cache[key1]
    del cache[key2]
elif mode == 2:
    del cache[key3]
else:
    del cache[key4]"""
    REGION_TYPE = "IF_REGION"

    def test_decompile(self):
        self.verify_decompilation()
