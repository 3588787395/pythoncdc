class B4A04:
    def b4a04_shallow(self, xs, flag):
        acc = 0
        try:
            for x in xs:
                if x > 0:
                    acc += x
        finally:
            acc += 1
        return acc

    def b4a04_deep(self, xs, flag):
        acc = 0
        try:
            if flag:
                for x in xs:
                    if x > 0:
                        if x > 10:
                            acc += 10
                        else:
                            acc += x
        finally:
            acc += 1
        return acc
