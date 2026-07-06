import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))
from tests.exhaustive.base import ExhaustiveTestCase

class TestTE065(ExhaustiveTestCase):
    SOURCE_CODE = "def f():\n    try:\n        x = 1\n    except TypeError:\n        return 'type_error'\n    except ValueError:\n        return 'value_error'"
    REGION_TYPE = "TRY_EXCEPT"
    def test_decompile(self):
        self.verify_decompilation()
