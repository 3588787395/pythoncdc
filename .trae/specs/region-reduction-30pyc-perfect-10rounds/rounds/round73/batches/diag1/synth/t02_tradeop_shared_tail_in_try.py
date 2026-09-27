# t02: t01 shape carried inside try/except (mirrors the original pyc where the
# loop sits inside a protected range) - tests whether the try carrier changes
# the shared-tail absorption.
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
    except Exception:
        return -1


def log(*a):
    return None
