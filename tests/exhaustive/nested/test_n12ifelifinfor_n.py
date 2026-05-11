import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))
from tests.exhaustive.base import ExhaustiveTestCase


class TestN12IfElifInFor_n(ExhaustiveTestCase):
    SOURCE_CODE = """for n in range(10):
    if n > 7:
        pass
    elif n > 3:
        pass
    else:
        pass"""
    REGION_TYPE = "NESTED"

    def test_decompile(self):
        self.verify_decompilation()
