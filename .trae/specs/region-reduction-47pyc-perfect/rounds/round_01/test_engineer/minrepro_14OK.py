# Source Generated with Decompyle++ (Python version)
# File: minrepro_14.pyc (Python 3.11)

def create_daily_stats_pattern(daily_result):
    result = {}
    for account in ('A', 'B', 'C', 'D'):
        if account in daily_result:
            result[account] = daily_result[account]
    result = None
    return result
