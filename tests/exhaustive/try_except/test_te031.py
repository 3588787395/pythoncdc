import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))
from tests.exhaustive.base import ExhaustiveTestCase

class TestTE031(ExhaustiveTestCase):
    SOURCE_CODE = 'for i in range(3):\n    try:\n        x = 1\n    except:\n        break'
    REGION_TYPE = "TRY_EXCEPT"
    def test_decompile(self):
        self.verify_decompilation()
