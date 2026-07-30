def f(x, y, z):
        try:
            if x is None:
                return z
            else:
                return y
        except BaseException:
            return y
