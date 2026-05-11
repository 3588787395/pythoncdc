import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))
from tests.exhaustive.base import ExhaustiveTestCase


class TestIF76Ifnestedelseif_a(ExhaustiveTestCase):
    SOURCE_CODE = """if a > 0:
    a = 1
else:
    if a < -10:
        a = -10
    else:
        a = 0"""
    REGION_TYPE = "IF_REGION"

    def test_decompile(self):
        self.verify_decompilation()
