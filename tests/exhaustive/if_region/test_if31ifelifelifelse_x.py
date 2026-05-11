import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))
from tests.exhaustive.base import ExhaustiveTestCase


class TestIF31IfElifElifElse_x(ExhaustiveTestCase):
    SOURCE_CODE = """if x > 10:
    pass
elif x > 5:
    pass
elif x > 0:
    pass
else:
    pass"""
    REGION_TYPE = "IF_REGION"

    def test_decompile(self):
        self.verify_decompilation()
