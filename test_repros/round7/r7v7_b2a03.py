class B2A03:
    def b2a03_shallow(self, xs, flag):
        acc = 0
        for x in xs:
            if x < 0 and flag:
                continue
            acc += x
        return acc

    def b2a03_deep(self, xs, flag):
        acc = 0
        for x in xs:
            if flag:
                if x != 0:
                    if x < 0:
                        continue
                    acc += x
                else:
                    acc -= 1
        return acc
