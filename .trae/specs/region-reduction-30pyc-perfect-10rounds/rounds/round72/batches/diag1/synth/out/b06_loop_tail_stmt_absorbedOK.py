# Source Generated with Decompyle++ (Python version)
# File: b06_loop_tail_stmt_absorbed.pyc (Python 3.11)

def trade_operation(orders, write_info):
    for o in orders:
        if o.get('valid'):
            write_info.append(o)
        write_info.append('mark')
    return write_info
