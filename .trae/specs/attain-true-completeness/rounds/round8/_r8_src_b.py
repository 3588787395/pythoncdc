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
