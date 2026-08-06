
def func(x, freq):
    if freq[-1] == 'd':
        return x.isocalendar()
    elif freq[-1] == 'm':
        return x.month
    else:
        return x.year
