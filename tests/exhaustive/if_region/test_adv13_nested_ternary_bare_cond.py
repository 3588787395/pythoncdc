import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))
from tests.exhaustive.base import ExhaustiveTestCase


class TestAdv13NestedTernaryBareCond(ExhaustiveTestCase):
    # if 条件中嵌套三元（无外层括号）：
    # if a if b else c if d else e:
    #     pass
    # Python 解析为 if (a if b else (c if d else e)): pass
    # 字节码含两段嵌套三元 merge_block，外层 cond=b 选择 a / 内层三元，
    # 内层 cond=d 选择 c / e。R12 修复了嵌套三元选最外层，但此处作为 if 条件可能仍失败。
    SOURCE_CODE = """if a if b else c if d else e:
    pass"""
    REGION_TYPE = "IF_REGION"

    def test_decompile(self):
        self.verify_decompilation()
