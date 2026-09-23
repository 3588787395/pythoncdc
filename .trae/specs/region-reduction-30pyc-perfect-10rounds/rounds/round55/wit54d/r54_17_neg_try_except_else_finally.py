def w(g, x):
    try:
        if x > 0:
            v = g(1)
        elif x < 0:
            v = g(2)
        else:
            v = g(3)
    except ValueError as e:
        v = g(4)
    except Exception:
        v = g(5)
    else:
        v += 1
    finally:
        g(6)
    return v
