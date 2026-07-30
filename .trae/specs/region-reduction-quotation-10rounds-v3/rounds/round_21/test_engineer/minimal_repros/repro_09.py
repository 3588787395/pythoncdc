"""repro_09: BUILD_CONST_KEY_MAP 消费模式 — 三元 value 涉及方法调用/属性访问。

测试 aspect: dict value 的三元表达式 then/else 分支包含方法调用或属性访问
(obj.method() if cond else obj.attr)。这些子表达式在三元分支内产生额外 LOAD_ATTR +
PRECALL + CALL 指令，merge_block 仍流入 BUILD_CONST_KEY_MAP。反编译器需将含方法调用
的三元作为整体 dict value 归约，不把方法调用拆为独立语句。

    d = {'a': obj.get() if cond else obj.default, 'b': b}
"""


class Obj:
    def get(self):
        return 1

    default = 0


def f(obj, cond, b):
    d = {
        'a': obj.get() if cond else obj.default,
        'b': b,
        'c': obj.get() if cond else 0,
    }
    return d
