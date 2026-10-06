# Source Generated with Decompyle++ (Python version)
# File: r1_92_regress_if_for_seq_setup.pyc (Python 3.11)

def f92(accounts, api_option, api_future, api_method):
    if 'option' in accounts:
        for export_name in api_option.__all__:
            api_method(getattr(api_option, export_name))
    if 'future' in accounts:
        for export_name in api_future.__all__:
            api_method(getattr(api_future, export_name))
