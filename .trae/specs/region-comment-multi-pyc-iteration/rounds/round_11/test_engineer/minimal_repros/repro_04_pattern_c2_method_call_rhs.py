"""[R11 repro_04] Pattern C2: 2-tuple unpack with method-call RHS."""


def f(obj):
    if obj.flag:
        a, b = obj.get_a(), obj.get_b()
        return a, b
