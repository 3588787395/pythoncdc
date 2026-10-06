class B3A04:
    def b3a04_shallow(self, xs, flag):
        total = 0
        for x in xs:
            if x:
                total += x
            total += 1
        return total

    def b3a04_deep(self, xs, flag):
        total = 0
        for x in xs:
            if flag:
                if x:
                    if x > 5:
                        total += 5
                    total += x
            total += 1
        return total
