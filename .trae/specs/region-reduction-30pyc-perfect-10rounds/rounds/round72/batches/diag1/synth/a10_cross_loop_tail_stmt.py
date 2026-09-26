# F-CROSS/F-THENOVER (trade_info_utils.trade_operation): a statement that belongs to
# the for-loop body (`write_info.append(items)`) is absorbed into the trailing if-chain,
# so the chain's exit jump lands after it (A@676 -> 1000 vs B -> 1042).
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
