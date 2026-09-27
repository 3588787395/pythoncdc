# Source Generated with Decompyle++ (Python version)
# File: t02_tradeop_shared_tail_in_try.pyc (Python 3.11)

def trade_operation(csv_reader, trade_id_list, operation, write_info):
    try:
        for items in csv_reader:
            if items[0] in trade_id_list:
                if operation == 'start':
                    items[2] = '0'
                    operation = 'restart'
                if operation == 'stop':
                    items[2] = '1'
                if operation == 'delete':
                    items[2] = '2'
                log(items[0], operation)
            write_info.append(items)
        return len(write_info)
        return None
    except Exception:
        return -1
def log(*a):
    return None
