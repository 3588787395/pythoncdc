# t07: trade_operation carrier stack mirror: try > if os.path.exists > with
# FileLock > for > if membership (tail append shared with membership-false).
import os


class FileLock(object):
    def __init__(self, path):
        self.path = path

    def __enter__(self):
        return self

    def __exit__(self, *a):
        return False


def read_csv(path):
    return []


def t07(trade_list_file, trade_id_list, operation, write_info,
        delete_write_info):
    try:
        if os.path.exists(trade_list_file):
            with FileLock(trade_list_file):
                csv_reader = read_csv(trade_list_file)
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
            return None
        else:
            return False
    except BaseException:
        return False


def log(*a):
    return None
