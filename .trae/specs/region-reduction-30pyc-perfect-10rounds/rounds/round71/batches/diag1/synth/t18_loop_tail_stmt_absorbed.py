# F-CROSS (trade_info_utils.trade_operation): a statement that follows an `if`
# inside a for-loop body is pulled into the then-branch by the decompiler.
def trade_operation(orders, write_info):
    for o in orders:
        if o.get('valid'):
            write_info.append(o)
        write_info.append('mark')
    return write_info
