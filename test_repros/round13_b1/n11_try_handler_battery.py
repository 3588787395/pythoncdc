def tf(g, h):
    try:
        try:
            g()
        except ValueError:
            k = 1
    except Exception as e:
        v = (e, k)
    try:
        for i in range(3):
            if i == 1:
                break
            x = i
    except KeyError:
        pass
    try:
        h()
    except* ValueError:
        pass
    except* TypeError:
        pass
    finally:
        z = 1
