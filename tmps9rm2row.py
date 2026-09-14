def test_except_if_else_raise():
    try:
        execute_sql()
        if '10001' in str(ex.orig):
            tmp = 'CREATE'
            sql = tmp + ')'
            execute(sql)
            data_to_sql()
            return None
        else:
            raise ex
    except Exception as e:
        log_error()
        raise e