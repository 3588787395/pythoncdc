def except_branch_with_reraise(data):
    try:
        result = process(data)
        return result
    except BaseException:
        error_info = get_traceback()
        log.error(f'Error: {error_info}')
        return None
