import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))
from tests.exhaustive.base import ExhaustiveTestCase


class TestAdv15TernaryDictValueBody(ExhaustiveTestCase):
    # if 体内字典字面量 value 为三元表达式：
    # if c:
    #     d = {'k': a if x else b}
    # 字节码 LOAD_CONST 'k' / 含三元 merge_block（cond=x 选择 a / b）
    # / BUILD_MAP 1 / STORE_NAME d。反编译器未能正确将三元 merge
    # 归约到 BUILD_MAP 的 value 栈位，导致字典字面量丢失，仅残留
    # 三元表达式作为独立语句（POP_TOP），赋值目标 d 也丢失。
    SOURCE_CODE = """if c:
    d = {'k': a if x else b}"""
    REGION_TYPE = "IF_REGION"

    def test_decompile(self):
        self.verify_decompilation()
