"""Multi-context and nested ``with`` shapes (sync).

Targets StructuredAnalyzer._identify_with_structures, whose anchor lines sit in
the branch that requires >=2 BEFORE_WITH instructions in one block with no
STORE_FAST/POP_TOP between them (i.e. a multi-item ``with``).
"""


class Ctx:
    def __init__(self, tag):
        self.tag = tag

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        return False

    def read(self):
        return self.tag


def pj_entry(a, b):
    """Zero-arg-callable entry: two-item with."""
    with Ctx(a) as first, Ctx(b) as second:
        out = (first.read(), second.read())
    return out


def pj_entry_three(a, b, c):
    """Zero-arg-callable entry: three-item with (longer BEFORE_WITH run)."""
    with Ctx(a) as x, Ctx(b) as y, Ctx(c) as z:
        out = x.read() + y.read() + z.read()
    return out


def pj_entry_nested(a, b):
    """Zero-arg-callable entry: nested with statements."""
    with Ctx(a) as outer:
        with Ctx(b) as inner:
            return outer.read(), inner.read()


def pj_entry_module_level(a, b):
    """Zero-arg-callable entry: with inside try/except/else."""
    try:
        with Ctx(a) as x, Ctx(b) as y:
            out = x.read(), y.read()
    except ValueError:
        out = ()
    else:
        out = out + ("else",)
    return out


def pj_entry_default():
    """Zero-arg defaulted entry (J input_model.calls driver)."""
    return (pj_entry(1, 2), pj_entry_three(1, 2, 3),
            pj_entry_nested(1, 2), pj_entry_module_level(1, 2))

def main():
    return pj_entry(1, 2), pj_entry_three(1, 2, 3), pj_entry_nested(1, 2)


if __name__ == "__main__":
    main()
