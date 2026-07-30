import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..', '..'))
from tests.exhaustive.base import ExhaustiveTestCase


class TestR5ForNestedTryInExcept(ExhaustiveTestCase):
    SOURCE_CODE = """for i in r:
    try:
        do()
    except E:
        try:
            x = 1
        except E2:
            y = 2"""
    REGION_TYPE = "FOR_LOOP"

    def test_decompile(self):
        self.verify_decompilation()
