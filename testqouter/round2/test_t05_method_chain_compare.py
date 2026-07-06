def test():
    import datetime
    d1 = datetime.date(2024, 1, 1)
    d2 = datetime.date(2024, 1, 1)
    return d1.isocalendar()[0] == d2.isocalendar()[0] and d1.isocalendar()[1] == d2.isocalendar()[1]
