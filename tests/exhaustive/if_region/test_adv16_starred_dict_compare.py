import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))
from tests.exhaustive.base import ExhaustiveTestCase


class TestAdv16StarredDictCompare(ExhaustiveTestCase):
    # 双星号解包的字典字面量 + 比较：
    # if {**a, **b} == c:
    #     pass
    # 字节码 BUILD_MAP 0 / LOAD_NAME a / DICT_UPDATE 1 / LOAD_NAME b /
    # DICT_UPDATE 1 / LOAD_NAME c / COMPARE_OP == / POP_JUMP_IF_FALSE。
    # BUILD_MAP + DICT_UPDATE 在 if 条件中作 COMPARE_OP 操作数时的反编译。
    SOURCE_CODE = """if {**a, **b} == c:
    pass"""
    REGION_TYPE = "IF_REGION"

    def test_decompile(self):
        self.verify_decompilation()
