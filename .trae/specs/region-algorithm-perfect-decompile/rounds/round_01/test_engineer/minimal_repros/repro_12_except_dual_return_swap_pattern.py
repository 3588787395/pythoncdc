def except_dual_return(match_obj, info, func_name):
    match_val = match_obj.group(0)
    try:
        result = eval(match_obj.group(1))
        return match_val
    except:
        if match_obj.group(1) not in info:
            return None
        val = info[match_obj.group(1)]
        if val not in info:
            return None
        return match_val
