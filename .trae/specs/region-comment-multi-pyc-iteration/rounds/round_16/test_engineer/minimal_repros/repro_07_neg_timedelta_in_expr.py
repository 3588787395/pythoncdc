# Pattern: (dtime + datetime.timedelta(days=-1)).strftime(...) negative delta (get_pre_one_year_date else)
# Function: mirror common.pyc negative-timedelta-in-expression return
# Expected: return (dtime + datetime.timedelta(days=-1)).strftime('%Y-%m-%d')
# Actual: same (pyc 100% match, NO-DEFECT control)
import datetime
def prev_day_str(dtime):
    return (dtime + datetime.timedelta(days=-1)).strftime('%Y-%m-%d')
# NO-DEFECT
