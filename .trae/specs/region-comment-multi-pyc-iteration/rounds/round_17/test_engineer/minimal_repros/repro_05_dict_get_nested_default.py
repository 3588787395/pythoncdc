# Pattern: dict.get with nested .get default (mirror read_config_file pe_times_high)
# Function: mirror zt_api.pyc read_config_file nested .get default
# Expected: float(info[0].get('pe_times_high', info[0].get('pe_times', 0)))
# Actual: same (pyc 100% match, NO-DEFECT control)
def get_pe(info):
    pe_low = float(info[0].get('pe_times_low', -999999))
    pe_high = float(info[0].get('pe_times_high', info[0].get('pe_times', 0)))
    return pe_low + pe_high
# NO-DEFECT
