import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))
from tests.exhaustive.base import ExhaustiveTestCase


class TestAdv20NestedWithTryInElifBody(ExhaustiveTestCase):
    # elif body 内含嵌套 with + try-except + 嵌套 if-else：
    # def f(flag, path):
    #     if flag == 'simple':
    #         return 'simple'
    #     elif flag == 'complex':
    #         with open(path) as f1:
    #             try:
    #                 data = f1.read()
    #                 if data:
    #                     with open(path + '.bak') as f2:
    #                         f2.write(data)
    #                     return 'written'
    #                 else:
    #                     return 'empty'
    #             except IOError as e:
    #                 return str(e)
    #     else:
    #         return 'none'
    # 字节码 BEFORE_WITH / SETUP_FINALLY / WITH_HANDLER_EXIT / PUSH_EXC_INFO
    # / 反编译器在 elif body 内 nested with + try + 嵌套 if-else 时易丢失 with 嵌套结构。
    SOURCE_CODE = """def f(flag, path):
    if flag == 'simple':
        return 'simple'
    elif flag == 'complex':
        with open(path) as f1:
            try:
                data = f1.read()
                if data:
                    with open(path + '.bak') as f2:
                        f2.write(data)
                    return 'written'
                else:
                    return 'empty'
            except IOError as e:
                return str(e)
    else:
        return 'none'"""
    REGION_TYPE = "IF_REGION"

    def test_decompile(self):
        self.verify_decompilation()
