import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))
from tests.exhaustive.base import ExhaustiveTestCase


class TestIF30IfElifElif_a(ExhaustiveTestCase):
    SOURCE_CODE = """if a > 10:
    pass
elif a > 5:
    pass
elif a > 0:
    pass"""
    REGION_TYPE = "IF_REGION"

    def test_decompile(self):
        self.verify_decompilation()
