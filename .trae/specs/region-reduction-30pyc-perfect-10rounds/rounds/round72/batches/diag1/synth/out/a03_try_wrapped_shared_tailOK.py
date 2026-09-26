# Source Generated with Decompyle++ (Python version)
# File: a03_try_wrapped_shared_tail.pyc (Python 3.11)

def get_fields(table, fields, fetch, pit, log, system_log):
    try:
        if fields is None:
            if table == 'valuation':
                error_msg, financial_data_tmp = fetch(table, '20180511')
            elif table in pit:
                financial_data_tmp = pit[table]
                return financial_data_tmp
            else:
                error_msg, financial_data_tmp = fetch(table, '2015')
                if error_msg['error_no'] == 0 and financial_data_tmp:
                    financial_data = []
                    for data in financial_data_tmp:
                        financial_data.append(data)
                    return financial_data
                log.error('bad')
                return list()
        return fields
    except BaseException as e:
        system_log.exception('exception')
        return e
