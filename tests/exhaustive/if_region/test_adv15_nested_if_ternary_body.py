import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))
from tests.exhaustive.base import ExhaustiveTestCase


class TestAdv15NestedIfTernaryBody(ExhaustiveTestCase):
    # 嵌套 if 的内层 if body 为三元赋值：
    # if a:
    #     if b:
    #         x = c if p else d
    # 字节码外层 POP_JUMP_IF_FALSE（cond=a）/ 内层
    # POP_JUMP_IF_FALSE（cond=b）/ 含三元 merge_block（cond=p
    # 选择 c / d）/ STORE_NAME x。反编译器在归约三元 merge 时
    # 将赋值语句从内层 if body 中提升到外层 if body，导致内层
    # if b 只剩 pass，且 LOAD_NAME 的 argval 发生错位（b 被误
    # 读为 p），控制流结构被破坏。
    SOURCE_CODE = """if a:
    if b:
        x = c if p else d"""
    REGION_TYPE = "IF_REGION"

    def test_decompile(self):
        self.verify_decompilation()
