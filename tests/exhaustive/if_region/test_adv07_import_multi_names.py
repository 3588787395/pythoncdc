import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))
from tests.exhaustive.base import ExhaustiveTestCase


class TestAdv07ImportMultiNames(ExhaustiveTestCase):
    # if 体内 from m import 多个名字: from m import a, b, cc
    SOURCE_CODE = """if c:
    from m import a, b, cc"""
    REGION_TYPE = "IF_REGION"

    def test_decompile(self):
        self.verify_decompilation()
