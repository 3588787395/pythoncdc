import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))
from tests.exhaustive.base import ExhaustiveTestCase


class TestIF05IfMultiElif_x(ExhaustiveTestCase):
    SOURCE_CODE = """if x == 1:
    pass
elif x == 2:
    pass
elif x == 3:
    pass
else:
    pass"""
    REGION_TYPE = "IF_REGION"

    def test_decompile(self):
        self.verify_decompilation()
