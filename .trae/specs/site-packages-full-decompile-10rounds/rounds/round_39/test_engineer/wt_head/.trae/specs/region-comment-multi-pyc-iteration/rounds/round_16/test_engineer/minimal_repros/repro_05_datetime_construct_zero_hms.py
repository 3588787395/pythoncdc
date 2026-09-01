# Pattern: datetime.datetime(y, m, 1, 0, 0, 0) construction (get_pre_half_year_date loop body)
# Function: mirror common.pyc datetime construction with zeroed hms
# Expected: dayto = datetime.datetime(dayto.year, dayto.month, 1, 0, 0, 0)
# Actual: same (pyc 100% match, NO-DEFECT control)
import datetime
def first_of_month(dtime):
    return datetime.datetime(dtime.year, dtime.month, 1, 0, 0, 0)
# NO-DEFECT
