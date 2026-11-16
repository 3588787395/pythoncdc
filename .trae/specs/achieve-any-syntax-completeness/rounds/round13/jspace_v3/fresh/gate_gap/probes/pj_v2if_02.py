"""Class/method code objects whose bodies hold if/elif chains.

Second sample for ASTGeneratorV2._generate_if_ast, adding class-body and
decorator shapes so the bridge (if any) sees a class-level if chain too.
"""


def deco(fn):
    return fn


class PJBase:
    def method(self, v):
        if v:
            return 1
        elif not v:
            return 2
        return 3


class PJChild(PJBase):
    """Class body with an if chain, a lambda attribute and a nested class."""

    if True:
        FLAG = 1
    else:
        FLAG = 0

    HOOK = lambda self, x: x if x else -1

    class Nested:
        def go(self, y):
            if y and y > 0:
                return y * 2
            elif y or y == 0:
                return y + 2
            return -y


@deco
def pj_entry(n):
    """Zero-arg-callable entry: method call plus class-level if chain."""
    child = PJChild()
    return PJBase().method(n), PJChild.Nested().go(n), child.FLAG


def pj_entry_default():
    """Zero-arg defaulted entry (J input_model.calls driver)."""
    return pj_entry(2)

def main():
    return pj_entry(2), PJChild.HOOK(None, 1)


if __name__ == "__main__":
    main()
