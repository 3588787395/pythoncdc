# Source Generated with Decompyle++ (Python version)
# File: repro_09_for_try_with_except_return_finally_misorder.cpython-311.pyc (Python 3.11)

import csv
def get_trade_unit_info(base_path):
    tempTradeUnits = []
    for user in os.listdir(base_path):
        tempBacktestIds = []
        trade_file = os.path.join(base_path, user, 'trades.csv')
        try:
            if os.path.exists(trade_file):
                with Lock(trade_file, 'shared'):
                    reader = get_reader(trade_file)
                for line in reader:
                    if line[2] == '0' or line[2] == '3':
                        tempBacktestIds.append(line[0])
        except BaseException:
            print('error reading %s' % trade_file)
            return None
        if len(tempBacktestIds) > 0:
            info_file = os.path.join(base_path, user, 'info.csv')
            if os.path.exists(info_file):
                fp = None
                fp = open(info_file, 'r', encoding='utf-8')
                csv_r = csv.reader(fp)
                for item in csv_r:
                    if item[0] in tempBacktestIds:
                        if len(item) >= 5:
                            tempTradeUnits.append(str(item[4]))
                        if len(item) >= 7 and item[6]:
                            tempTradeUnits.append(str(item[6]))
                if fp is not None:
                    fp.close()
        print('read %s' % info_file)
    return tempTradeUnits
