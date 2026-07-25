import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))
from tests.exhaustive.base import ExhaustiveTestCase


class TestR25LambdaIifeInElifCond(ExhaustiveTestCase):
    SOURCE_CODE = """def f(y):
    if y > 0:
        return 'pos'
    elif (lambda x: x < 0)(y):
        return 'neg'
    else:
        return 'zero' """
    REGION_TYPE = "IF_REGION"

    def test_decompile(self):
        self.verify_decompilation()
