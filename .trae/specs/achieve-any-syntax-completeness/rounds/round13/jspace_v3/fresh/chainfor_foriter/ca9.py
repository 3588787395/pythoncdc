class K9:
    def m(self, it):
        first = last = next(it)
        for x in it:
            yield (first, last, x)
