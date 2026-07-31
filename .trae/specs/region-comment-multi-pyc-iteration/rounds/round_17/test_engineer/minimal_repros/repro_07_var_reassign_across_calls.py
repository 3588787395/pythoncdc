# Pattern: variable reassignment across calls (mirror read_config_file factor_type=0,1,2,3)
# Function: mirror zt_api.pyc read_config_file factor_type progression
# Expected: ft = 0; a = get(..., ft); ft = 1; b = get(..., ft); ft = 2; c = get(..., ft)
# Actual: same (pyc 100% match, NO-DEFECT control)
def fetch(factor_id):
    ft = 0
    a = info_get(factor_id, ft)
    ft = 1
    b = info_get(factor_id, ft)
    ft = 2
    c = info_get(factor_id, ft)
    return a, b, c
# NO-DEFECT
