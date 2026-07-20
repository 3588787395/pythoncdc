import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))
from tests.exhaustive.base import ExhaustiveTestCase


class TestAdv08ForElseInIf(ExhaustiveTestCase):
    # if 体内嵌套 for-else
    SOURCE_CODE = """if c:
    for x in y:
        if x > 0:
            break
    else:
        r = 1"""
    REGION_TYPE = "IF_REGION"

    def test_decompile(self):
        self.verify_decompilation()
