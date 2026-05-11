import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))
from tests.exhaustive.base import ExhaustiveTestCase


class TestIF77Ifelifelsemultistmt_n(ExhaustiveTestCase):
    SOURCE_CODE = """if n > 0:
    n = 1
    m = 2
elif n < 0:
    n = -1
    m = -2
else:
    n = 0
    m = 0"""
    REGION_TYPE = "IF_REGION"

    def test_decompile(self):
        self.verify_decompilation()
