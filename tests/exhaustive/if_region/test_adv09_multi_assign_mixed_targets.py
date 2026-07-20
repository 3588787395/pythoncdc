import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))
from tests.exhaustive.base import ExhaustiveTestCase


class TestAdv09MultiAssignMixedTargets(ExhaustiveTestCase):
    # if 体内多元赋值含属性+下标+名 a = b.c = d[e] = f
    SOURCE_CODE = """if c:
    a = b.c = d[e] = f"""
    REGION_TYPE = "IF_REGION"

    def test_decompile(self):
        self.verify_decompilation()
