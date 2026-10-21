def f():
    try:
        x = 1
    except ValueError:
        return 2
    finally:
        x = 3


def g(k):
    while k:
        try:
            x = 1
        except ValueError:
            break
        finally:
            x = 3


def h(k):
    for i in k:
        try:
            x = 1
        except ValueError:
            continue
        finally:
            x = 3
