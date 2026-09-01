# Pattern: isinstance check + conditional reassignment (get_dividend)
# Function: BasicDataSource.get_dividend
# Expected: if isinstance(x, date): x = convert(x); return self._obj.method(x)
# Actual: same (pyc 100% match, NO-DEFECT control)
def get_dividend(symbol, query_date=None):
    if isinstance(query_date, int):
        query_date = query_date + 1
    return query_date
# NO-DEFECT
