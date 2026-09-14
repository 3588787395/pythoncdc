# Source Generated with Decompyle++ (Python version)
# File: minrepro_20.pyc (Python 3.11)

def get_trade_unit_info_pattern(dirs):
    results = []
    for user in dirs:
        try:
            items = read_file(user)
            for line in items:
                if line[2] == '0' or line[2] == '3':
                    results.append(line[0])
        except BaseException:
            log('error')
            return None
        if len(results) > 0:
            info = read_info(user)
            if info is not None:
                info.close()
        log('log message outside try')
    return results
