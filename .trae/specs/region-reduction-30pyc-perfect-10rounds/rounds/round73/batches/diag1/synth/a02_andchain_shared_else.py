# F-ORELSE (finance get_financial_and_growth_factors / pit_mode): `if A and B: X
# else: Y` -- decompiler re-attaches the else to the innermost test, emitting
# nested ifs so the outer false path skips the else body.
def f(date=None, start_year=None, end_year=None, now=None):
    if not date:
        if start_year is None and end_year is None:
            date = query_date(now, date=date)
            date = change(date)
            date = int(date)
        else:
            date = None
    a, b = convert(date)
    return a, b
