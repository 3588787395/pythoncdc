def f():
    try:
        try:
            x = 1
        except ValueError:
            x = 2
        finally:
            x = 3
    except NameError:
        x = 4
    else:
        x = 5
    finally:
        x = 6


class CTryNest:
    try:
        try:
            DEEP = 1
        except ValueError:
            DEEP = 2
        finally:
            MID = 3
    except NameError:
        DEEP = 4
    else:
        OUT = 5
    finally:
        LEAF = 6
