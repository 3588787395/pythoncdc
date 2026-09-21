class Box(object):

    def clean(self, items, g, h):
        for x in items:
            if x:
                try:
                    g(x)
                except BaseException:
                    h(x)
        return self
