def r10_except_handler(self, k):
    try:
        return self.d[k]
    except KeyError:
        self.d[k] = (r := make())
        return r
def make():
    return 5
