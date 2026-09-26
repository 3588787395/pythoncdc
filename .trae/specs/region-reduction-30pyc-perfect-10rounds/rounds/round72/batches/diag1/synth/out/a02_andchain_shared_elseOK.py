# Source Generated with Decompyle++ (Python version)
# File: a02_andchain_shared_else.pyc (Python 3.11)

def f(date=None, start_year=None, end_year=None, now=None):
    if not date:
        if start_year is None:
            if end_year is None:
                date = query_date(now, date=date)
                date = change(date)
                date = int(date)
            else:
                date = None
    a, b = convert(date)
    return (a, b)
