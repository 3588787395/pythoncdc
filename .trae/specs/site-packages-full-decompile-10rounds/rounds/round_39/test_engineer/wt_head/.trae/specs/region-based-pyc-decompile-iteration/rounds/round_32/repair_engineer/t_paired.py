def paired(algo, datalist):
    try:
        a = 1
        b = a + 1
        for item in datalist:
            if item in a:
                c = 2
        else:
            a = 0
    except ValueError:
        b = 0
    finally:
        a = 3
    return b
