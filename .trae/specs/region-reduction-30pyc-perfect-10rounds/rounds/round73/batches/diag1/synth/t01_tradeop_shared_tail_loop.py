# F-ABSORB (trade_info_utils.trade_operation target_diff #94): inside a loop,
# `if C:` with a long then-arm (nested comparisons) followed by a SHARED tail
# statement.  Original: false-edge of `items[0] in trade_id_list` jumps to the
# shared tail (write_info.append) then loops back; product absorbs the tail into
# the then-arm so the false edge skips it (jump target 1000 -> 1042).
def trade_operation(csv_reader, trade_id_list, operation, write_info):
    for items in csv_reader:
        if items[0] in trade_id_list:
            if operation == 'start':
                items[2] = '0'
                operation = 'restart'
            if operation == 'stop':
                items[2] = '1'
            if operation == 'delete':
                items[2] = '2'
            if operation == 'pause':
                items[2] = '3'
            if operation == 'reload':
                items[2] = '4'
            log(items[0], operation)
        write_info.append(items)
    return len(write_info)


def log(*a):
    return None
