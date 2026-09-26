# F-ORELSE/F-THENOVER (finance.get_fields): whole body wrapped in try/except; the
# shared tail that follows the inner if/elif/else is absorbed into the else arm, so
# the first then-arm's exit jump re-targets the far merge instead of the tail
# (A@92 -> 236 vs B@94 -> 742), forcing an extra EXTENDED_ARG (177/178 instructions).
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
