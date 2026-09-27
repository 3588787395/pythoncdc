# t04: trade_operation mirror WITH the internal `continue` (orig pyc 872
# JUMP_BACKWARD inside the then-arm after the delete branch's log).
def trade_operation(csv_reader, trade_id_list, operation, write_info,
                    delete_write_info):
    for items in csv_reader:
        if items[0] in trade_id_list:
            if operation == 'start':
                items[2] = '0'
                operation = 'restart'
            if operation == 'stop':
                items[2] = '1'
            if operation == 'delete':
                items[2] = '2'
                delete_write_info.append(items)
                log(items[0], operation)
                continue
            if operation == 'pause':
                items[2] = '3'
            if operation == 'reload':
                items[2] = '4'
            log(items[0], operation)
        write_info.append(items)
    return len(write_info)


def log(*a):
    return None
