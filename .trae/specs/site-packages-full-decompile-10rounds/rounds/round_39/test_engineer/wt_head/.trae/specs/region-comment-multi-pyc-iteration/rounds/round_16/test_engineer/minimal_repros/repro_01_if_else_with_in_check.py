# Pattern: if/else with `in` operator in condition (get_pre_half_year_date inner)
# Function: mirror common.pyc get_pre_half_year_date inner branch
# Expected: if '-' in s: return f(s, '%Y-%m-%d') else: return f(s, '%Y%m%d')
# Actual: same (pyc 100% match, NO-DEFECT control)
import datetime
def parse_date(s):
    if '-' in s:
        return str(datetime.datetime.strptime(s, '%Y-%m-%d').date())
    else:
        return str(datetime.datetime.strptime(s, '%Y%m%d').date())
# NO-DEFECT
