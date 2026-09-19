# Source Generated with Decompyle++ (Python version)
# File: r2_09_bool_cond_invert_dec_dec.pyc (Python 3.11)

__doc__ = """Repro: create_user_code_iqe if/elif chain and boolop mangling.

Original shape (inside the function, after a big f-string assignment):
    if business_mode is None or business_mode == BUSINESS_MODE_2 or reloads:
        if reloads:
            tmp = int(time.time())
            strategy_file_name = 'user_strategy_{}'.format(str(tmp))
        else:
            strategy_file_name = 'user_strategy'
        strategy_file = os.path.join(trade_result_path, strategy_file_name + '.py')
        with open(strategy_file, 'w') as f_user:
            f_user.write(user_code)
    elif business_mode == BUSINESS_MODE_1 and not reloads:
        src_so_path = os.path.join(STRATEGY_DIR_PATH, login_id, strategy_id, USER_CODE_DAT)
        os.system('sudo /bin/cp -rf {} {}'.format(src_so_path, dst_so_path))

The decompiler emitted (verified against trade_info_utilsOK.py):
    if business_mode is not None and business_mode == BUSINESS_MODE_2 or reloads and reloads:
        tmp = int(time.time())
        strategy_file_name = 'user_strategy_{}'.format(str(tmp))
        strategy_file_name = 'user_strategy'
        ...
    if not reloads:
        src_so_path = ...
i.e. (a) the or-chain was inverted into an and-chain, (b) the nested
`if reloads:` guard was absorbed as a duplicated `and reloads` operand,
(c) the inner if/else collapsed to two unconditional assignments, and
(d) the elif guard lost its first operand. first_diff idx550:
JUMP_FORWARD(2908) vs LOAD_CONST('user_strategy').
"""
import os
import time
BUSINESS_MODE_1 = 'B1'
BUSINESS_MODE_2 = 'B2'
STRATEGY_DIR_PATH = 's'
USER_CODE_DAT = 'd.dat'
def create_user_code(business_mode, reloads, trade_result_path, login_id, strategy_id):
    user_code = 'print(1)'
    if business_mode or business_mode == BUSINESS_MODE_2 or reloads and reloads:
        tmp = int(time.time())
        strategy_file_name = 'user_strategy_{}'.format(str(tmp))
        strategy_file_name = 'user_strategy'
        strategy_file = os.path.join(trade_result_path, strategy_file_name + '.py')
        with open(strategy_file, 'w') as f_user:
            f_user.write(user_code)
        if reloads:
            return None
    elif not (business_mode == BUSINESS_MODE_1 and reloads):
        pass
    if reloads:
        src_so_path = os.path.join(STRATEGY_DIR_PATH, login_id, strategy_id, USER_CODE_DAT)
        os.system('sudo /bin/cp -rf {} {}'.format(src_so_path, trade_result_path))
        return None
    else:
        return user_code
