import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..', '..'))
from tests.exhaustive.base import ExhaustiveTestCase


class TestR5ForMatchOrGuard(ExhaustiveTestCase):
    SOURCE_CODE = """for i in r:
    match x:
        case 1 | 2 if i > 0:
            y = 1
        case _:
            y = 0"""
    REGION_TYPE = "FOR_LOOP"

    def test_decompile(self):
        self.verify_decompilation()
