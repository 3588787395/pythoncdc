import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))
from tests.exhaustive.base import ExhaustiveTestCase


class TestFor06ForElse(ExhaustiveTestCase):
    SOURCE_CODE = """for i in range(5):
    if i == 3:
        break
else:
    print("completed")"""
    REGION_TYPE = "FOR_LOOP"

    def test_decompile(self):
        self.verify_decompilation()
