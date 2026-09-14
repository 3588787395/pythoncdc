# Source Generated with Decompyle++ (Python version)
# File: repro_01_with_no_as_finally_handler.cpython-311.pyc (Python 3.11)

import csv
def get_user_info(user_id, trade_id):
    user_info_file = '/tmp/%s/user_info.csv' % user_id
    if os.path.exists(user_info_file):
        fp = None
        fp = open(user_info_file, 'r')
        csv_r = csv.reader(fp)
        for item in csv_r:
            if item[0] == trade_id:
                match item:
                    case _:
                        return fp.close()
