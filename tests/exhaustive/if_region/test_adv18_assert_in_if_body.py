import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))
from tests.exhaustive.base import ExhaustiveTestCase


class TestAdv18AssertInIfBody(ExhaustiveTestCase):
    # if-elif-else body 内含 assert + 消息（含变量）：
    # if x > 0:
    #     assert x < 100, f"value too large: {x}"
    # elif x < 0:
    #     assert x > -100, "value too small"
    # else:
    #     assert True, "should not reach"
    # 字节码 LOAD_ASSERTION_ERROR / RAISE_VARARGS / 反编译器在 if body
    # 内 assert + f-string 消息时易把 assert 退化为 if not cond: raise。
    SOURCE_CODE = """if x > 0:
    assert x < 100, f"value too large: {x}"
elif x < 0:
    assert x > -100, "value too small"
else:
    assert True, "should not reach\""""
    REGION_TYPE = "IF_REGION"

    def test_decompile(self):
        self.verify_decompilation()
