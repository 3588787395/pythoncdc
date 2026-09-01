# DEFECT-REPRO Pattern T: 镜像 backtest handle_backtest_build — with→if/else→else:with→try/except
import shutil


def handle_build(strategy_path, backtest_path, content, user_strategy_path):
    with open(user_strategy_path, 'w') as file_user:
        file_user.write(content)
    error = verify(user_strategy_path)
    if error is not None:
        return ({'code': '2', 'message': error}, None, None)
    else:
        try:
            shutil.copy(strategy_path, backtest_path)
        except FileExistsError as e:
            return ({'code': '2', 'message': 'exists'}, None, None)
    return ({'code': '1', 'message': ''}, None, None)


def verify(p):
    return None
# DEFECT-REPRO
