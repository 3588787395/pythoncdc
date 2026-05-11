def test():
    import datetime
    d = datetime.date(2024, 1, 15)
    a = d.isocalendar()
    return a[0], a[1], a[2]
