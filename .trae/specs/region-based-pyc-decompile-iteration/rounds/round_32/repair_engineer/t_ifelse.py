def f(algo, datalist):
    for item in datalist:
        if item:
            algo += 1
        else:
            algo -= 1
    return algo

def g(algo, datalist):
    for item in datalist:
        if item:
            algo += 1
    return algo

def h(algo, datalist):
    for item in datalist:
        if item:
            algo += 1
            continue
        algo -= 1
    return algo

def k(algo, datalist):
    for item in datalist:
        if item:
            continue
        algo -= 1
    return algo
