"""Dict-AST carrier with the same statement arms nested one level deeper."""


def pj_entry():
    """Zero-arg entry: every statement arm inside a function body."""
    local = {"x": 1}

    def build():
        inner = {"y": 2}
        inner["z"] = local["x"]
        return inner

    class Nested:
        ATTR = {"n": [1, 2, 3]}

        def get(self):
            return self.ATTR

    del local["x"]
    return build(), Nested()


def pj_entry_comp(ns=(1, 2, 3)):
    """Zero-arg entry: dict/set/generator comprehensions."""
    d = {n: n * 2 for n in ns}
    s = {n + 1 for n in ns}
    g = (n - 1 for n in ns)
    return d, s, list(g)


def main():
    return pj_entry(), pj_entry_comp()


if __name__ == "__main__":
    main()
