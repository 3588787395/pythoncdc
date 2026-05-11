import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))
from tests.exhaustive.base import ExhaustiveTestCase


class TestIf05MultiElif(ExhaustiveTestCase):
    SOURCE_CODE = """if x > 10:
    y = 10
elif x > 5:
    y = 5
elif x > 0:
    y = 0
elif x == 0:
    y = -1
else:
    y = -999"""
    REGION_TYPE = "IF_REGION"

    def test_decompile(self):
        self.verify_decompilation()
