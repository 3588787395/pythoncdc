import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))
from tests.exhaustive.base import ExhaustiveTestCase


class TestIF41Ifelifnestedif_n(ExhaustiveTestCase):
    SOURCE_CODE = """if n > 0:
    n = 1
elif n < 0:
    if n < -10:
        n = -10"""
    REGION_TYPE = "IF_REGION"

    def test_decompile(self):
        self.verify_decompilation()
