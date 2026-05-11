import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))
from tests.exhaustive.base import ExhaustiveTestCase


class TestBO16OrReturn_x_y(ExhaustiveTestCase):
    SOURCE_CODE = """def f():
    return x or y"""
    REGION_TYPE = "BOOL_OP"

    def test_decompile(self):
        self.verify_decompilation()
