import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))
from tests.exhaustive.base import ExhaustiveTestCase


class TestTry20ComplexPattern(ExhaustiveTestCase):
    SOURCE_CODE = """def robust_process(items):
    results = []
    errors = []
    for i, item in enumerate(items):
        try:
            if not valid(item):
                raise ValueError(f"Invalid at {i}")
            result = transform(item)
            if result is None:
                continue
            results.append(result)
        except ValueError as e:
            errors.append((i, str(e)))
        except TransformError:
            errors.append((i, "transform failed"))
    return results, errors"""
    REGION_TYPE = "TRY_EXCEPT"

    def test_decompile(self):
        self.verify_decompilation()
