# Source Generated with Decompyle++ (Python version)
# File: minrepro_24.pyc (Python 3.11)

def trade_operation_pattern(trade_id, operation):
    try:
        items = read_data(trade_id)
        write_info = []
        for item in items:
            if operation == 'stop':
                item[2] = '1'
            if operation == 'delete':
                item[2] = '2'
                write_info.append(item)
                continue
            write_info.append(item)
            continue
        if len(write_info) > 0:
            write_data(write_info)
            return True
        else:
            return False
    except BaseException:
        log('error')
        return False
