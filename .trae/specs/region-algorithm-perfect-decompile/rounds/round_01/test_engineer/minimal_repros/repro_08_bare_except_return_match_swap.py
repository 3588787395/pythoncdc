def bare_except_return_match(match_obj):
    match_val = match_obj.group(0)
    try:
        result = eval(match_obj.group(1))
        return match_val
    except:
        return match_val
