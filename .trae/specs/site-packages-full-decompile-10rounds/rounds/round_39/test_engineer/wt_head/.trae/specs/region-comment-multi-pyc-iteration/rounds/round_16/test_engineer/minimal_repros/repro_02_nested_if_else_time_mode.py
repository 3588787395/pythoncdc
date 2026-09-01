# Pattern: outer if/else (mode branch) + nested if/else (get_pre_half_year_date)
# Function: mirror common.pyc TIME_MODE outer + '-' inner
# Expected: if mode=='1': if '-' in s: ... else: ... else: arithmetic branch
# Actual: same (pyc 100% match, NO-DEFECT control)
import datetime
def get_date(mode, s, dtime):
    if mode == '1':
        if '-' in s:
            return str(datetime.datetime.strptime(s, '%Y-%m-%d').date())
        else:
            return str(datetime.datetime.strptime(s, '%Y%m%d').date())
    else:
        delta = datetime.timedelta(days=dtime.day)
        return str(dtime - delta)
# NO-DEFECT
