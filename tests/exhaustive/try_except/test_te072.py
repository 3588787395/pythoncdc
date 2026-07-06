import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))
from tests.exhaustive.base import ExhaustiveTestCase

class TestTE072(ExhaustiveTestCase):
    SOURCE_CODE = 'def f():\n    try:\n        x = 1\n    except:\n        return None\n    else:\n        return x'
    REGION_TYPE = "TRY_EXCEPT"
    def test_decompile(self):
        self.verify_decompilation()
