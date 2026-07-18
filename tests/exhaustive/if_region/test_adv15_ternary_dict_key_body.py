import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))
from tests.exhaustive.base import ExhaustiveTestCase


class TestAdv15TernaryDictKeyBody(ExhaustiveTestCase):
    # if 体内字典字面量 key 为三元表达式：
    # if c:
    #     d = {a if x else b: 'v'}
    # 字节码含三元 merge_block（cond=x 选择 a / b）作 BUILD_MAP 的
    # key 栈位，LOAD_CONST 'v' 作 value。反编译器错误地将三元
    # merge 拆出为独立表达式语句，BUILD_MAP 整体丢失，STORE_NAME d
    # 也丢失，仅保留 (a if x else b) 作为独立语句。
    SOURCE_CODE = """if c:
    d = {a if x else b: 'v'}"""
    REGION_TYPE = "IF_REGION"

    def test_decompile(self):
        self.verify_decompilation()
