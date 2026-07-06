import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))
from tests.exhaustive.base import ExhaustiveTestCase


class TestN34ForWhileIf_x_y(ExhaustiveTestCase):
    SOURCE_CODE = """for x in range(5):
    while y > 0:
        if y > 2:
            y -= 1
        else:
            break"""
    REGION_TYPE = "NESTED"

    def test_decompile(self):
        self.verify_decompilation()
