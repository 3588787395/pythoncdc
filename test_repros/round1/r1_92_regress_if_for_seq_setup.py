def f92(accounts, api_option, api_future, api_method):
    if 'option' in accounts:
        for export_name in api_option.__all__:
            api_method(getattr(api_option, export_name))
    if 'future' in accounts:
        for export_name in api_future.__all__:
            api_method(getattr(api_future, export_name))
