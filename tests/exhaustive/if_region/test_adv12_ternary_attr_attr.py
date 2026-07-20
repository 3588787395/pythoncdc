import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))
from tests.exhaustive.base import ExhaustiveTestCase


class TestAdv12TernaryAttrAttr(ExhaustiveTestCase):
    # if 条件中三元表达式作多级属性访问的 receiver：
    # if (a if c else b).x.y > 0
    # 字节码含两个 LOAD_ATTR（多级属性）紧跟三元 merge。
    SOURCE_CODE = """if (a if c else b).x.y > 0:
    pass"""
    REGION_TYPE = "IF_REGION"

    def test_decompile(self):
        self.verify_decompilation()
