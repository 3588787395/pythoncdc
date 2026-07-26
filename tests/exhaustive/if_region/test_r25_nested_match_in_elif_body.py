import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))
from tests.exhaustive.base import ExhaustiveTestCase


class TestR25NestedMatchInElifBody(ExhaustiveTestCase):
    SOURCE_CODE = """def f(x):
    if x > 0:
        return 'pos'
    elif x < 0:
        match x:
            case -1:
                return 'minus_one'
            case -2:
                return 'minus_two'
            case _:
                return 'other_neg'
    else:
        return 'zero' """
    REGION_TYPE = "IF_REGION"

    def test_decompile(self):
        self.verify_decompilation()
