import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..', '..'))
from tests.exhaustive.base import ExhaustiveTestCase


class TestR1WhileTryExceptElseFinallyBreak(ExhaustiveTestCase):
    SOURCE_CODE = """while a:
    try:
        x = 1
    except E:
        break
    else:
        y = 2
    finally:
        z = 3"""
    REGION_TYPE = "WHILE_LOOP"

    def test_decompile(self):
        self.verify_decompilation()
