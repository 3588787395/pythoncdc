import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))
from tests.exhaustive.base import ExhaustiveTestCase


class TestAdv04DeepSubscrAssign(ExhaustiveTestCase):
    # 多层下标赋值（d[a][b][c] = 1）
    SOURCE_CODE = """if c:
    d[a][b][c] = 1"""
    REGION_TYPE = "IF_REGION"

    def test_decompile(self):
        self.verify_decompilation()
