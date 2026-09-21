class C:
    def m(self, a, d, e):
        if a:
            d = 1
        elif d:
            d = d * 3
            if d > e:
                e = d
        return (d, e)
