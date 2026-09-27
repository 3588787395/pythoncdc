# F-POLARITY (api_base.get_history): a truthy guard whose body is a nested
# if/elif/else ladder, followed by an unconditional tail.  The decompiler
# inverts the guard sense (`if assets:` -> `if not assets: ... else: <body>`),
# so the first divergent instruction is
# POP_JUMP_FORWARD_IF_FALSE -> POP_JUMP_FORWARD_IF_TRUE with the SAME target.
def get_history(asset, bar_count, frequency='1d', skip_suspended=False, include=False):
    assets = assure_assets(asset)
    if assets:
        engine_obj = engine_instance()
        if frequency == '1d':
            sys_frequency = engine_obj.config.frequency
            if sys_frequency in ('1m', 'tick') or include:
                if ExecutionContext.phase() == BEFORE_TRADING_START:
                    query_date = data_proxy().previous_date()
                    include = False
                else:
                    query_date = engine_instance().calendar_dt
        else:
            query_date = engine_instance().calendar_dt
        query_date = convert_dt_to_int(query_date)
        if isinstance(asset, list):
            if skip_suspended:
                raise IQInvalidArgument('skip_suspended only supports a single contract')
            return {a.symbol: fetch(a, bar_count, query_date) for a in assets}
        else:
            return fetch(assets[0], bar_count, query_date)
    if isinstance(asset, list):
        return {}
    return EMPTY_BAR_NP_ARRAY
