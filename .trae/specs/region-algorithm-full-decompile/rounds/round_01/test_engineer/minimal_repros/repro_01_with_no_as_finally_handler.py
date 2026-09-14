import csv

def get_user_info(user_id, trade_id):
    user_info_file = '/tmp/%s/user_info.csv' % user_id
    if os.path.exists(user_info_file):
        fp = None
        fp = open(user_info_file, 'r')
        csv_r = csv.reader(fp)
        for item in csv_r:
            if item[0] == trade_id:
                item
                if fp is not None:
                    return fp.close()
                else:
                    return None
