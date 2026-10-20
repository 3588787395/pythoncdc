"""R4 synth: yield 语境/优先级交叉变体（YF9 族）。"""


def s_nested_yield(xs):
    for i in xs:
        yield (yield i) + 1


def s_compare(xs):
    for i in xs:
        if (yield i) < 3:
            yield i


def s_shift(xs):
    for i in xs:
        v = (yield i) << 2
        yield v
