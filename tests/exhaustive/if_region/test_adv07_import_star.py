import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))
from tests.exhaustive.base import ExhaustiveTestCase


class TestAdv07ImportStar(ExhaustiveTestCase):
    # if 体内 from m import * (星号导入)
    SOURCE_CODE = """if c:
    from m import *"""
    REGION_TYPE = "IF_REGION"

    def test_decompile(self):
        self.verify_decompilation()
