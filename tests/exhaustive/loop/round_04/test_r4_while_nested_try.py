import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..', '..'))
from tests.exhaustive.base import ExhaustiveTestCase


class TestR4WhileNestedTry(ExhaustiveTestCase):
    SOURCE_CODE = """while a:
    try:
        try:
            do()
        except E1:
            x = 1
    except E2:
        y = 2"""
    REGION_TYPE = "WHILE_LOOP"

    def test_decompile(self):
        self.verify_decompilation()
