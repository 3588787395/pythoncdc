# Pattern: str(datetime.datetime.strptime(...).date()) conversion (get_pre_half_year_date if branch)
# Function: mirror common.pyc str(strptime().date()) return
# Expected: return str(datetime.datetime.strptime(s, fmt).date())
# Actual: same (pyc 100% match, NO-DEFECT control)
import datetime
def to_date_str(s, fmt):
    return str(datetime.datetime.strptime(s, fmt).date())
# NO-DEFECT
