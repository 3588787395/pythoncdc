import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..', '..'))
from tests.exhaustive.base import ExhaustiveTestCase


class TestR5ForMatchGuard(ExhaustiveTestCase):
    SOURCE_CODE = """for i in r:
    match x:
        case _ if x > 0:
            y = 1
        case _:
            y = 2"""
    REGION_TYPE = "FOR_LOOP"

    def test_decompile(self):
        self.verify_decompilation()
