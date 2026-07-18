import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))
from tests.exhaustive.base import ExhaustiveTestCase


class TestAdv06AugassignSubscr(ExhaustiveTestCase):
    # if 体内 augmented assign with subscr target a[b] += 1
    SOURCE_CODE = """if c:
    a[b] += 1"""
    REGION_TYPE = "IF_REGION"

    def test_decompile(self):
        self.verify_decompilation()
