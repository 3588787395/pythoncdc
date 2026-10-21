def nat(k):
    for i in k:
        try:
            x = 1
        except ValueError:
            pass
        finally:
            x = 3


def nat2(k):
    for i in k:
        try:
            x = 1
        except ValueError:
            pass
