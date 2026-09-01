# Pattern: return x.strftime('%Y-%m-%d') formatting (get_pre_half_year_date tail)
# Function: mirror common.pyc strftime return
# Expected: return dayto.strftime('%Y-%m-%d')
# Actual: same (pyc 100% match, NO-DEFECT control)
import datetime
def format_date(dtime):
    return dtime.strftime('%Y-%m-%d')
# NO-DEFECT
