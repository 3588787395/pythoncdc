def build(df, index_data=False):
    if len(df) > 0:
        tempdict = {}
        tempdict['open'] = [df[0]]
        tempdict['is_open'] = [1 if df != 0 else 0]
        return tempdict
    return None
