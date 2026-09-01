# Pattern: for i in range(6) + timedelta subtraction (get_pre_half_year_date else branch)
# Function: mirror common.pyc for-loop with timedelta arithmetic
# Expected: for i in range(6): dayto = dayto - timedelta(days=1)
# Actual: same (pyc 100% match, NO-DEFECT control)
import datetime
def roll_back_months(dtime, n=6):
    dayto = dtime
    for i in range(n):
        dayto = dayto - datetime.timedelta(days=1)
    return dayto
# NO-DEFECT
