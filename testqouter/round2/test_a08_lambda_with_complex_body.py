def test():
    f = lambda a, b: a.isocalendar()[0] == b.isocalendar()[0] and a.isocalendar()[1] == b.isocalendar()[1]
    import datetime
    d1 = datetime.date(2024, 1, 1)
    d2 = datetime.date(2024, 1, 1)
    return f(d1, d2)
