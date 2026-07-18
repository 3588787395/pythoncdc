import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))
from tests.exhaustive.base import ExhaustiveTestCase


class TestAdv09StarredDictMulti(ExhaustiveTestCase):
    # if 体内字典字面量含多个 ** 解包 r = {**a, k1: v1, **b, k2: v2, **c}
    SOURCE_CODE = """if c:
    r = {**a, k1: v1, **b, k2: v2, **c}"""
    REGION_TYPE = "IF_REGION"

    def test_decompile(self):
        self.verify_decompilation()
