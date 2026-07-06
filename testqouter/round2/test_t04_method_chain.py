def test():
    import datetime
    d = datetime.date(2024, 1, 15)
    return d.isocalendar()[0]
