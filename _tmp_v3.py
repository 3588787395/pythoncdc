def f(x, y, z):
        try:
            if x is None:
                return z
            return y
        except BaseException:
            return y
