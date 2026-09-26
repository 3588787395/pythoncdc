# Source Generated with Decompyle++ (Python version)
# File: a10_cross_loop_tail_stmt.pyc (Python 3.11)

def trade_operation(csv_reader, trade_id_list, operation, write_info, delete_write_info, logger):
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
                continue
            if operation == 'pause':
                items[2] = '3'
            if operation == 'reload':
                items[2] = '4'
            logger.write(operation)
        write_info.append(items)
    return write_info
