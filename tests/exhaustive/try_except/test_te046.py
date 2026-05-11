import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))
from tests.exhaustive.base import ExhaustiveTestCase

class TestTE046(ExhaustiveTestCase):
    SOURCE_CODE = "try:\n    with open('a') as fa:\n        with open('b') as fb:\n            x = fa.read() + fb.read()\nexcept:\n    x = ''"
    REGION_TYPE = "TRY_EXCEPT"
    def test_decompile(self):
        self.verify_decompilation()
