def create_daily_stats_pattern(daily_result):
    result = {}
    for account in ('A', 'B', 'C', 'D'):
        if account in daily_result:
            result[account] = daily_result[account]
    result = None
    return result
