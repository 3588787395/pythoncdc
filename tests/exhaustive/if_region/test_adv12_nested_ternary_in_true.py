import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))
from tests.exhaustive.base import ExhaustiveTestCase


class TestAdv12NestedTernaryInTrue(ExhaustiveTestCase):
    # if 条件中外层三元的 true 分支本身是三元，且整体作属性访问：
    # if ((a if c else b) if d else e).x > 0
    # 字节码含嵌套三元（true 分支为内层三元）+ LOAD_ATTR。
    SOURCE_CODE = """if ((a if c else b) if d else e).x > 0:
    pass"""
    REGION_TYPE = "IF_REGION"

    def test_decompile(self):
        self.verify_decompilation()
