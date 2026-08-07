# Source Generated with Decompyle++ (Python version)
# File: empty_api_backtest.pyc (Python 3.11)

from IQEngine.const import ExecutionPhase
from IQEngine.core.execution_context import ExecutionContext
from IQEngine.utils import strategy_log
from IQCommon.util.wrapper_utils import check_arg
__all__ = ['get_etf_list', 'get_etf_info', 'get_etf_stock_list', 'get_etf_stock_info', 'etf_basket_order', 'etf_purchase_redemption', 'margincash_open', 'margincash_close', 'marginsec_open', 'marginsec_close', 'margincash_direct_refund', 'marginsec_direct_refund', 'get_margin_entrans_amount', 'get_margin_contract', 'get_margin_contractreal', 'get_assure_security_list', 'get_margincash_stocks', 'get_marginsec_stocks', 'get_margincash_open_amount', 'get_margincash_close_amount', 'get_marginsec_open_amount', 'get_marginsec_close_amount', 'ipo_stocks_order', 'debt_to_stock_order', 'order_market', 'get_snapshot', 'after_trading_order', 'after_trading_cancel_order', 'order_tick', 'cancel_order_ex', 'get_all_orders', 'send_email', 'send_qywx', 'get_cb_list', 'get_tick_direction', 'get_sort_msg', 'run_interval', 'permission_test', 'get_deliver', 'get_fundjour', 'get_trade_name', 'get_hks_list', 'hks_order', 'hks_odd_lot_order', 'get_hks_price_gap', 'get_hks_unit_amount', 'get_enslo_security_info', 'get_future_main_code', 'get_covered_lock_amount', 'get_covered_unlock_amount', 'option_covered_lock', 'option_covered_unlock', 'get_margin_asset', 'get_ipo_stocks', 'get_gear_price', 'get_crdt_fund', 'fund_transfer', 'market_fund_transfer', 'get_manage_mark', 'set_email_info']
@check_arg
@ExecutionContext.enforce_phase(ExecutionPhase.ON_HANDLE_AUCTION, ExecutionPhase.ON_HANDLE_DATA, ExecutionPhase.ON_ORDER_RSP, ExecutionPhase.ON_TRADE_RSP, ExecutionPhase.ON_HANDLE_TICK, ExecutionPhase.SCHEDULED, ExecutionPhase.GLOBAL, ExecutionPhase.BEFORE_TRADING_START, ExecutionPhase.AFTER_TRADING_END)
def get_etf_list():
    strategy_log.warning('回测不支持get_etf_list函数')
@check_arg
@ExecutionContext.enforce_phase(ExecutionPhase.ON_HANDLE_AUCTION, ExecutionPhase.ON_HANDLE_DATA, ExecutionPhase.ON_ORDER_RSP, ExecutionPhase.ON_TRADE_RSP, ExecutionPhase.ON_HANDLE_TICK, ExecutionPhase.SCHEDULED, ExecutionPhase.GLOBAL, ExecutionPhase.BEFORE_TRADING_START, ExecutionPhase.AFTER_TRADING_END)
def get_etf_info(etf_code):
    strategy_log.warning('回测不支持get_etf_info函数')
@check_arg
@ExecutionContext.enforce_phase(ExecutionPhase.ON_HANDLE_AUCTION, ExecutionPhase.ON_HANDLE_DATA, ExecutionPhase.ON_ORDER_RSP, ExecutionPhase.ON_TRADE_RSP, ExecutionPhase.ON_HANDLE_TICK, ExecutionPhase.SCHEDULED, ExecutionPhase.GLOBAL, ExecutionPhase.BEFORE_TRADING_START, ExecutionPhase.AFTER_TRADING_END)
def get_etf_stock_list(etf_code):
    strategy_log.warning('回测不支持get_etf_stock_list函数')
@check_arg
@ExecutionContext.enforce_phase(ExecutionPhase.ON_HANDLE_AUCTION, ExecutionPhase.ON_HANDLE_DATA, ExecutionPhase.SCHEDULED, ExecutionPhase.GLOBAL, ExecutionPhase.ON_ORDER_RSP, ExecutionPhase.ON_TRADE_RSP, ExecutionPhase.BEFORE_TRADING_START, ExecutionPhase.AFTER_TRADING_END, ExecutionPhase.ON_HANDLE_TICK)
def get_etf_stock_info(etf_code, security):
    strategy_log.warning('回测不支持get_etf_stock_info函数')
@check_arg
@ExecutionContext.enforce_phase(ExecutionPhase.ON_HANDLE_AUCTION, ExecutionPhase.ON_HANDLE_DATA, ExecutionPhase.SCHEDULED, ExecutionPhase.GLOBAL, ExecutionPhase.ON_ORDER_RSP, ExecutionPhase.ON_TRADE_RSP, ExecutionPhase.ON_HANDLE_TICK, ExecutionPhase.BEFORE_TRADING_START, ExecutionPhase.AFTER_TRADING_END)
def etf_basket_order(etf_code, amount, price_style=None, position=True, info=None, style=None, priceGear=0, limit_price=None, stop_price=None):
    strategy_log.warning('回测不支持etf_basket_order函数')
@check_arg
@ExecutionContext.enforce_phase(ExecutionPhase.ON_HANDLE_AUCTION, ExecutionPhase.ON_HANDLE_DATA, ExecutionPhase.SCHEDULED, ExecutionPhase.GLOBAL, ExecutionPhase.ON_ORDER_RSP, ExecutionPhase.ON_TRADE_RSP, ExecutionPhase.ON_HANDLE_TICK, ExecutionPhase.BEFORE_TRADING_START, ExecutionPhase.AFTER_TRADING_END)
def etf_purchase_redemption(etf_code, amount=0, limit_price=None, style=None, priceGear=0, stop_price=None):
    strategy_log.warning('回测不支持etf_purchase_redemption函数')
@check_arg
@ExecutionContext.enforce_phase(ExecutionPhase.ON_HANDLE_AUCTION, ExecutionPhase.ON_HANDLE_DATA, ExecutionPhase.SCHEDULED, ExecutionPhase.GLOBAL, ExecutionPhase.ON_ORDER_RSP, ExecutionPhase.ON_TRADE_RSP, ExecutionPhase.ON_HANDLE_TICK, ExecutionPhase.BEFORE_TRADING_START, ExecutionPhase.AFTER_TRADING_END)
def margincash_open(security, amount, limit_price=None, market_type=None, cash_group=None):
    strategy_log.warning('回测不支持margincash_open函数')
@check_arg
@ExecutionContext.enforce_phase(ExecutionPhase.ON_HANDLE_AUCTION, ExecutionPhase.ON_HANDLE_DATA, ExecutionPhase.SCHEDULED, ExecutionPhase.GLOBAL, ExecutionPhase.ON_ORDER_RSP, ExecutionPhase.ON_TRADE_RSP, ExecutionPhase.ON_HANDLE_TICK, ExecutionPhase.BEFORE_TRADING_START, ExecutionPhase.AFTER_TRADING_END)
def margincash_close(security, amount, limit_price=None, market_type=None, cash_group=None):
    strategy_log.warning('回测不支持margincash_close函数')
@check_arg
@ExecutionContext.enforce_phase(ExecutionPhase.ON_HANDLE_AUCTION, ExecutionPhase.ON_HANDLE_DATA, ExecutionPhase.SCHEDULED, ExecutionPhase.GLOBAL, ExecutionPhase.ON_ORDER_RSP, ExecutionPhase.ON_TRADE_RSP, ExecutionPhase.ON_HANDLE_TICK, ExecutionPhase.BEFORE_TRADING_START, ExecutionPhase.AFTER_TRADING_END)
def marginsec_open(security, amount, limit_price=None, cash_group=None, market_type=None):
    strategy_log.warning('回测不支持marginsec_open函数')
@check_arg
@ExecutionContext.enforce_phase(ExecutionPhase.ON_HANDLE_AUCTION, ExecutionPhase.ON_HANDLE_DATA, ExecutionPhase.SCHEDULED, ExecutionPhase.GLOBAL, ExecutionPhase.ON_ORDER_RSP, ExecutionPhase.ON_TRADE_RSP, ExecutionPhase.ON_HANDLE_TICK, ExecutionPhase.BEFORE_TRADING_START, ExecutionPhase.AFTER_TRADING_END)
def marginsec_close(security, amount, limit_price=None, market_type=None, cash_group=None):
    strategy_log.warning('回测不支持marginsec_close函数')
@check_arg
@ExecutionContext.enforce_phase(ExecutionPhase.ON_HANDLE_AUCTION, ExecutionPhase.ON_HANDLE_DATA, ExecutionPhase.SCHEDULED, ExecutionPhase.GLOBAL, ExecutionPhase.ON_ORDER_RSP, ExecutionPhase.ON_TRADE_RSP, ExecutionPhase.ON_HANDLE_TICK, ExecutionPhase.BEFORE_TRADING_START, ExecutionPhase.AFTER_TRADING_END)
def margincash_direct_refund(security, amount=None, cash_group=None):
    strategy_log.warning('回测不支持margincash_direct_refund函数')
@check_arg
@ExecutionContext.enforce_phase(ExecutionPhase.ON_HANDLE_AUCTION, ExecutionPhase.ON_HANDLE_DATA, ExecutionPhase.SCHEDULED, ExecutionPhase.GLOBAL, ExecutionPhase.ON_ORDER_RSP, ExecutionPhase.ON_TRADE_RSP, ExecutionPhase.ON_HANDLE_TICK, ExecutionPhase.BEFORE_TRADING_START, ExecutionPhase.AFTER_TRADING_END)
def marginsec_direct_refund(security, amount=None, cash_group=None):
    strategy_log.warning('回测不支持marginsec_direct_refund函数')
@check_arg
@ExecutionContext.enforce_phase(ExecutionPhase.ON_HANDLE_AUCTION, ExecutionPhase.ON_HANDLE_DATA, ExecutionPhase.SCHEDULED, ExecutionPhase.GLOBAL, ExecutionPhase.ON_ORDER_RSP, ExecutionPhase.ON_TRADE_RSP, ExecutionPhase.ON_HANDLE_TICK, ExecutionPhase.BEFORE_TRADING_START, ExecutionPhase.AFTER_TRADING_END)
def get_margin_entrans_amount(security, cash_group=None):
    strategy_log.warning('回测不支持get_margin_entrans_amount函数')
@check_arg
@ExecutionContext.enforce_phase(ExecutionPhase.ON_HANDLE_AUCTION, ExecutionPhase.ON_HANDLE_DATA, ExecutionPhase.SCHEDULED, ExecutionPhase.GLOBAL, ExecutionPhase.ON_ORDER_RSP, ExecutionPhase.ON_TRADE_RSP, ExecutionPhase.ON_HANDLE_TICK, ExecutionPhase.BEFORE_TRADING_START, ExecutionPhase.AFTER_TRADING_END)
def get_margin_contract(compact_source=None):
    strategy_log.warning('回测不支持get_margin_contract函数')
@check_arg
@ExecutionContext.enforce_phase(ExecutionPhase.ON_HANDLE_AUCTION, ExecutionPhase.ON_HANDLE_DATA, ExecutionPhase.SCHEDULED, ExecutionPhase.GLOBAL, ExecutionPhase.ON_ORDER_RSP, ExecutionPhase.ON_TRADE_RSP, ExecutionPhase.ON_HANDLE_TICK, ExecutionPhase.BEFORE_TRADING_START, ExecutionPhase.AFTER_TRADING_END)
def get_margin_contractreal():
    strategy_log.warning('回测不支持get_margin_contractreal函数')
@check_arg
@ExecutionContext.enforce_phase(ExecutionPhase.BEFORE_TRADING_START, ExecutionPhase.ON_HANDLE_DATA, ExecutionPhase.ON_HANDLE_TICK, ExecutionPhase.SCHEDULED, ExecutionPhase.GLOBAL, ExecutionPhase.ON_ORDER_RSP, ExecutionPhase.ON_TRADE_RSP, ExecutionPhase.AFTER_TRADING_END)
def get_margin_asset():
    strategy_log.warning('回测不支持get_margin_asset函数')
    return {}
@check_arg
@ExecutionContext.enforce_phase(ExecutionPhase.ON_HANDLE_AUCTION, ExecutionPhase.ON_HANDLE_DATA, ExecutionPhase.SCHEDULED, ExecutionPhase.GLOBAL, ExecutionPhase.ON_ORDER_RSP, ExecutionPhase.ON_TRADE_RSP, ExecutionPhase.ON_HANDLE_TICK, ExecutionPhase.BEFORE_TRADING_START, ExecutionPhase.AFTER_TRADING_END)
def get_assure_security_list():
    strategy_log.warning('回测不支持get_assure_security_list函数')
@check_arg
@ExecutionContext.enforce_phase(ExecutionPhase.ON_HANDLE_AUCTION, ExecutionPhase.ON_HANDLE_DATA, ExecutionPhase.SCHEDULED, ExecutionPhase.GLOBAL, ExecutionPhase.ON_ORDER_RSP, ExecutionPhase.ON_TRADE_RSP, ExecutionPhase.ON_HANDLE_TICK, ExecutionPhase.BEFORE_TRADING_START, ExecutionPhase.AFTER_TRADING_END)
def get_margincash_stocks():
    strategy_log.warning('回测不支持get_margincash_stocks函数')
@check_arg
@ExecutionContext.enforce_phase(ExecutionPhase.ON_HANDLE_AUCTION, ExecutionPhase.ON_HANDLE_DATA, ExecutionPhase.SCHEDULED, ExecutionPhase.GLOBAL, ExecutionPhase.ON_ORDER_RSP, ExecutionPhase.ON_TRADE_RSP, ExecutionPhase.ON_HANDLE_TICK, ExecutionPhase.BEFORE_TRADING_START, ExecutionPhase.AFTER_TRADING_END)
def get_marginsec_stocks():
    strategy_log.warning('回测不支持get_marginsec_stocks函数')
@check_arg
@ExecutionContext.enforce_phase(ExecutionPhase.ON_HANDLE_AUCTION, ExecutionPhase.ON_HANDLE_DATA, ExecutionPhase.SCHEDULED, ExecutionPhase.GLOBAL, ExecutionPhase.ON_ORDER_RSP, ExecutionPhase.ON_TRADE_RSP, ExecutionPhase.ON_HANDLE_TICK, ExecutionPhase.BEFORE_TRADING_START, ExecutionPhase.AFTER_TRADING_END)
def get_margincash_open_amount(security, price=None, cash_group=None):
    strategy_log.warning('回测不支持get_margincash_open_amount函数')
@check_arg
@ExecutionContext.enforce_phase(ExecutionPhase.ON_HANDLE_AUCTION, ExecutionPhase.ON_HANDLE_DATA, ExecutionPhase.SCHEDULED, ExecutionPhase.GLOBAL, ExecutionPhase.ON_ORDER_RSP, ExecutionPhase.ON_TRADE_RSP, ExecutionPhase.ON_HANDLE_TICK, ExecutionPhase.BEFORE_TRADING_START, ExecutionPhase.AFTER_TRADING_END)
def get_margincash_close_amount(security, price=None, cash_group=None):
    strategy_log.warning('回测不支持get_margincash_close_amount函数')
@check_arg
@ExecutionContext.enforce_phase(ExecutionPhase.ON_HANDLE_AUCTION, ExecutionPhase.ON_HANDLE_DATA, ExecutionPhase.SCHEDULED, ExecutionPhase.GLOBAL, ExecutionPhase.ON_ORDER_RSP, ExecutionPhase.ON_TRADE_RSP, ExecutionPhase.ON_HANDLE_TICK, ExecutionPhase.BEFORE_TRADING_START, ExecutionPhase.AFTER_TRADING_END)
def get_marginsec_open_amount(security, price=None, cash_group=None):
    strategy_log.warning('回测不支持get_marginsec_open_amount函数')
@check_arg
@ExecutionContext.enforce_phase(ExecutionPhase.ON_HANDLE_AUCTION, ExecutionPhase.ON_HANDLE_DATA, ExecutionPhase.SCHEDULED, ExecutionPhase.GLOBAL, ExecutionPhase.ON_ORDER_RSP, ExecutionPhase.ON_TRADE_RSP, ExecutionPhase.ON_HANDLE_TICK, ExecutionPhase.BEFORE_TRADING_START, ExecutionPhase.AFTER_TRADING_END)
def get_marginsec_close_amount(security, price=None, cash_group=None):
    strategy_log.warning('回测不支持get_marginsec_close_amount函数')
@check_arg
@ExecutionContext.enforce_phase(ExecutionPhase.ON_HANDLE_AUCTION, ExecutionPhase.ON_HANDLE_DATA, ExecutionPhase.SCHEDULED, ExecutionPhase.GLOBAL, ExecutionPhase.ON_ORDER_RSP, ExecutionPhase.ON_TRADE_RSP, ExecutionPhase.ON_HANDLE_TICK, ExecutionPhase.BEFORE_TRADING_START, ExecutionPhase.AFTER_TRADING_END)
def ipo_stocks_order(submarket_type=None, black_stocks=None):
    strategy_log.warning('回测不支持ipo_stocks_order函数')
@check_arg
@ExecutionContext.enforce_phase(ExecutionPhase.ON_HANDLE_AUCTION, ExecutionPhase.ON_HANDLE_DATA, ExecutionPhase.SCHEDULED, ExecutionPhase.GLOBAL, ExecutionPhase.ON_ORDER_RSP, ExecutionPhase.ON_TRADE_RSP, ExecutionPhase.BEFORE_TRADING_START, ExecutionPhase.AFTER_TRADING_END, ExecutionPhase.ON_HANDLE_TICK)
def debt_to_stock_order(security, amount):
    strategy_log.warning('回测不支持debt_to_stock_order函数')
@check_arg
@ExecutionContext.enforce_phase(ExecutionPhase.BEFORE_TRADING_START, ExecutionPhase.ON_HANDLE_AUCTION, ExecutionPhase.ON_HANDLE_DATA, ExecutionPhase.ON_HANDLE_TICK, ExecutionPhase.AFTER_TRADING_END, ExecutionPhase.SCHEDULED, ExecutionPhase.ON_TRADE_RSP, ExecutionPhase.ON_ORDER_RSP, ExecutionPhase.GLOBAL)
def order_market(security, amount, market_type=None, limit_price=None):
    strategy_log.warning('回测不支持order_market函数')
@check_arg
@ExecutionContext.enforce_phase(ExecutionPhase.BEFORE_TRADING_START, ExecutionPhase.ON_HANDLE_AUCTION, ExecutionPhase.ON_HANDLE_DATA, ExecutionPhase.ON_HANDLE_TICK, ExecutionPhase.AFTER_TRADING_END, ExecutionPhase.SCHEDULED, ExecutionPhase.ON_TRADE_RSP, ExecutionPhase.ON_ORDER_RSP, ExecutionPhase.GLOBAL)
def get_snapshot(security):
    strategy_log.warning('回测不支持get_snapshot函数')
@check_arg
@ExecutionContext.enforce_phase(ExecutionPhase.ON_HANDLE_AUCTION, ExecutionPhase.ON_HANDLE_DATA, ExecutionPhase.SCHEDULED, ExecutionPhase.GLOBAL, ExecutionPhase.ON_ORDER_RSP, ExecutionPhase.ON_TRADE_RSP, ExecutionPhase.ON_HANDLE_TICK, ExecutionPhase.AFTER_TRADING_END)
def after_trading_order(security, amount, entrust_price):
    strategy_log.warning('回测不支持after_trading_order函数')
@check_arg
@ExecutionContext.enforce_phase(ExecutionPhase.ON_HANDLE_AUCTION, ExecutionPhase.ON_HANDLE_DATA, ExecutionPhase.SCHEDULED, ExecutionPhase.GLOBAL, ExecutionPhase.ON_ORDER_RSP, ExecutionPhase.ON_TRADE_RSP, ExecutionPhase.ON_HANDLE_TICK, ExecutionPhase.AFTER_TRADING_END)
def after_trading_cancel_order(order_param=None):
    strategy_log.warning('回测不支持after_trading_cancel_order函数')
@check_arg
@ExecutionContext.enforce_phase(ExecutionPhase.ON_HANDLE_TICK)
def order_tick(sid, amount, priceGear=None, limit_price=None):
    strategy_log.warning('回测不支持order_tick函数')
@check_arg
@ExecutionContext.enforce_phase(ExecutionPhase.ON_HANDLE_AUCTION, ExecutionPhase.ON_HANDLE_DATA, ExecutionPhase.SCHEDULED, ExecutionPhase.GLOBAL, ExecutionPhase.ON_ORDER_RSP, ExecutionPhase.ON_TRADE_RSP, ExecutionPhase.BEFORE_TRADING_START, ExecutionPhase.AFTER_TRADING_END, ExecutionPhase.ON_HANDLE_TICK)
def cancel_order_ex(order_param):
    strategy_log.warning('回测不支持cancel_order_ex函数')
@check_arg
@ExecutionContext.enforce_phase(ExecutionPhase.ON_HANDLE_AUCTION, ExecutionPhase.ON_HANDLE_DATA, ExecutionPhase.SCHEDULED, ExecutionPhase.GLOBAL, ExecutionPhase.ON_ORDER_RSP, ExecutionPhase.ON_TRADE_RSP, ExecutionPhase.BEFORE_TRADING_START, ExecutionPhase.AFTER_TRADING_END, ExecutionPhase.ON_HANDLE_TICK)
def get_all_orders(security=None):
    strategy_log.warning('回测不支持get_all_orders函数')
@check_arg
@ExecutionContext.enforce_phase(ExecutionPhase.ON_HANDLE_AUCTION, ExecutionPhase.ON_HANDLE_DATA, ExecutionPhase.SCHEDULED, ExecutionPhase.GLOBAL, ExecutionPhase.ON_ORDER_RSP, ExecutionPhase.ON_TRADE_RSP, ExecutionPhase.BEFORE_TRADING_START, ExecutionPhase.AFTER_TRADING_END, ExecutionPhase.ON_HANDLE_TICK)
def send_email(send_email_info=None, get_email_info=None, smtp_code=None, info=None):
    strategy_log.warning('回测不支持send_email函数')
@check_arg
@ExecutionContext.enforce_phase(ExecutionPhase.ON_HANDLE_AUCTION, ExecutionPhase.ON_HANDLE_DATA, ExecutionPhase.SCHEDULED, ExecutionPhase.GLOBAL, ExecutionPhase.ON_ORDER_RSP, ExecutionPhase.ON_TRADE_RSP, ExecutionPhase.BEFORE_TRADING_START, ExecutionPhase.AFTER_TRADING_END, ExecutionPhase.ON_HANDLE_TICK)
def send_qywx(corp_id=None, secret=None, agent_id=None, info=None, toparty=None, touser=None, totag=None):
    strategy_log.warning('回测不支持send_qywx函数')
@check_arg
@ExecutionContext.enforce_phase(ExecutionPhase.ON_HANDLE_AUCTION, ExecutionPhase.GLOBAL, ExecutionPhase.SCHEDULED, ExecutionPhase.ON_ORDER_RSP, ExecutionPhase.ON_TRADE_RSP, ExecutionPhase.BEFORE_TRADING_START, ExecutionPhase.ON_HANDLE_TICK, ExecutionPhase.ON_HANDLE_DATA, ExecutionPhase.AFTER_TRADING_END)
def get_cb_list():
    strategy_log.warning('回测不支持get_cb_list函数')
    return []
@check_arg
@ExecutionContext.enforce_phase(ExecutionPhase.GLOBAL, ExecutionPhase.ON_HANDLE_DATA, ExecutionPhase.ON_HANDLE_TICK, ExecutionPhase.BEFORE_TRADING_START, ExecutionPhase.AFTER_TRADING_END, ExecutionPhase.SCHEDULED, ExecutionPhase.GLOBAL, ExecutionPhase.ON_ORDER_RSP, ExecutionPhase.ON_TRADE_RSP)
def get_tick_direction(symbols, query_date=0, start_pos=0, search_direction=1, data_count=50, business_type=0, is_dict=False):
    strategy_log.warning('回测不支持get_tick_direction函数')
@check_arg
@ExecutionContext.enforce_phase(ExecutionPhase.ON_HANDLE_AUCTION, ExecutionPhase.BEFORE_TRADING_START, ExecutionPhase.ON_HANDLE_DATA, ExecutionPhase.SCHEDULED, ExecutionPhase.ON_HANDLE_TICK, ExecutionPhase.AFTER_TRADING_END, ExecutionPhase.GLOBAL, ExecutionPhase.ON_ORDER_RSP, ExecutionPhase.ON_TRADE_RSP)
def get_sort_msg(sort_type_grp=None, sort_field_name=None, sort_type=1, data_count=100):
    strategy_log.warning('回测不支持get_sort_msg函数')
@check_arg
@ExecutionContext.enforce_phase(ExecutionPhase.INITIALIZE)
def run_interval(context, func, seconds=None, **kwargs):
    strategy_log.warning('回测不支持run_interval函数')
@check_arg
@ExecutionContext.enforce_phase(ExecutionPhase.INITIALIZE, ExecutionPhase.BEFORE_TRADING_START, ExecutionPhase.AFTER_TRADING_END)
def permission_test(account=None, end_date=None):
    strategy_log.warning('回测不支持permission_test函数')
@check_arg
@ExecutionContext.enforce_phase(ExecutionPhase.BEFORE_TRADING_START, ExecutionPhase.AFTER_TRADING_END)
def get_deliver(start_date='', end_date=''):
    strategy_log.warning('回测不支持get_deliver函数')
@check_arg
@ExecutionContext.enforce_phase(ExecutionPhase.BEFORE_TRADING_START, ExecutionPhase.AFTER_TRADING_END)
def get_fundjour(start_date='', end_date=''):
    strategy_log.warning('回测不支持get_fundjour函数')
@check_arg
@ExecutionContext.enforce_phase(ExecutionPhase.ON_HANDLE_DATA, ExecutionPhase.ON_ORDER_RSP, ExecutionPhase.ON_TRADE_RSP, ExecutionPhase.ON_HANDLE_TICK, ExecutionPhase.SCHEDULED, ExecutionPhase.GLOBAL, ExecutionPhase.BEFORE_TRADING_START, ExecutionPhase.AFTER_TRADING_END)
def get_trade_name():
    strategy_log.warning('回测不支持get_trade_name函数')
@check_arg
@ExecutionContext.enforce_phase(ExecutionPhase.GLOBAL, ExecutionPhase.ON_HANDLE_DATA, ExecutionPhase.ON_HANDLE_TICK, ExecutionPhase.AFTER_TRADING_END, ExecutionPhase.BEFORE_TRADING_START, ExecutionPhase.ON_HANDLE_AUCTION, ExecutionPhase.SCHEDULED, ExecutionPhase.ON_ORDER_RSP, ExecutionPhase.ON_TRADE_RSP)
def get_underlying_code(symbols):
    strategy_log.warning('回测不支持get_underlying_code函数')
@check_arg
@ExecutionContext.enforce_phase(ExecutionPhase.ON_HANDLE_DATA, ExecutionPhase.ON_ORDER_RSP, ExecutionPhase.ON_TRADE_RSP, ExecutionPhase.ON_HANDLE_TICK, ExecutionPhase.SCHEDULED, ExecutionPhase.GLOBAL, ExecutionPhase.BEFORE_TRADING_START, ExecutionPhase.AFTER_TRADING_END)
def get_hks_list(market=None):
    strategy_log.warning('回测不支持get_hks_list函数')
@check_arg
@ExecutionContext.enforce_phase(ExecutionPhase.ON_HANDLE_DATA, ExecutionPhase.ON_ORDER_RSP, ExecutionPhase.ON_TRADE_RSP, ExecutionPhase.ON_HANDLE_TICK, ExecutionPhase.SCHEDULED, ExecutionPhase.GLOBAL, ExecutionPhase.BEFORE_TRADING_START, ExecutionPhase.AFTER_TRADING_END)
def hks_order(security, amount, limit_price=None, style=None):
    strategy_log.warning('回测不支持hks_order函数')
@check_arg
@ExecutionContext.enforce_phase(ExecutionPhase.ON_HANDLE_DATA, ExecutionPhase.ON_ORDER_RSP, ExecutionPhase.ON_TRADE_RSP, ExecutionPhase.ON_HANDLE_TICK, ExecutionPhase.SCHEDULED, ExecutionPhase.GLOBAL, ExecutionPhase.BEFORE_TRADING_START, ExecutionPhase.AFTER_TRADING_END)
def hks_odd_lot_order(security, amount, limit_price=None):
    strategy_log.warning('回测不支持hks_odd_lot_order函数')
@check_arg
@ExecutionContext.enforce_phase(ExecutionPhase.ON_HANDLE_DATA, ExecutionPhase.ON_ORDER_RSP, ExecutionPhase.ON_TRADE_RSP, ExecutionPhase.ON_HANDLE_TICK, ExecutionPhase.SCHEDULED, ExecutionPhase.GLOBAL, ExecutionPhase.BEFORE_TRADING_START, ExecutionPhase.AFTER_TRADING_END)
def get_hks_price_gap():
    strategy_log.warning('回测不支持get_hks_price_gap函数')
@check_arg
@ExecutionContext.enforce_phase(ExecutionPhase.ON_HANDLE_DATA, ExecutionPhase.ON_ORDER_RSP, ExecutionPhase.ON_TRADE_RSP, ExecutionPhase.ON_HANDLE_TICK, ExecutionPhase.SCHEDULED, ExecutionPhase.GLOBAL, ExecutionPhase.BEFORE_TRADING_START, ExecutionPhase.AFTER_TRADING_END)
def get_hks_unit_amount(security, trade_type):
    strategy_log.warning('回测不支持get_hks_unit_amount函数')
@check_arg
@ExecutionContext.enforce_phase(ExecutionPhase.ON_HANDLE_DATA, ExecutionPhase.ON_ORDER_RSP, ExecutionPhase.ON_TRADE_RSP, ExecutionPhase.ON_HANDLE_TICK, ExecutionPhase.SCHEDULED, ExecutionPhase.GLOBAL, ExecutionPhase.BEFORE_TRADING_START, ExecutionPhase.AFTER_TRADING_END)
def get_enslo_security_info(cash_group=None, qry_type=None):
    strategy_log.warning('回测不支持get_enslo_security_info函数')
@check_arg
@ExecutionContext.enforce_phase(ExecutionPhase.GLOBAL, ExecutionPhase.ON_HANDLE_DATA, ExecutionPhase.ON_HANDLE_TICK, ExecutionPhase.AFTER_TRADING_END, ExecutionPhase.BEFORE_TRADING_START, ExecutionPhase.ON_HANDLE_AUCTION, ExecutionPhase.SCHEDULED)
def get_future_main_code(code):
    strategy_log.warning('回测不支持get_future_main_code函数')
@check_arg
@ExecutionContext.enforce_phase(ExecutionPhase.ON_HANDLE_DATA, ExecutionPhase.ON_ORDER_RSP, ExecutionPhase.ON_TRADE_RSP, ExecutionPhase.ON_HANDLE_TICK, ExecutionPhase.SCHEDULED, ExecutionPhase.GLOBAL, ExecutionPhase.BEFORE_TRADING_START, ExecutionPhase.AFTER_TRADING_END)
def get_covered_lock_amount(code):
    strategy_log.warning('回测不支持get_covered_lock_amount函数')
@check_arg
@ExecutionContext.enforce_phase(ExecutionPhase.ON_HANDLE_DATA, ExecutionPhase.ON_ORDER_RSP, ExecutionPhase.ON_TRADE_RSP, ExecutionPhase.ON_HANDLE_TICK, ExecutionPhase.SCHEDULED, ExecutionPhase.GLOBAL, ExecutionPhase.BEFORE_TRADING_START, ExecutionPhase.AFTER_TRADING_END)
def get_covered_unlock_amount(code):
    strategy_log.warning('回测不支持get_covered_unlock_amount函数')
@check_arg
@ExecutionContext.enforce_phase(ExecutionPhase.ON_HANDLE_DATA, ExecutionPhase.ON_ORDER_RSP, ExecutionPhase.ON_TRADE_RSP, ExecutionPhase.ON_HANDLE_TICK, ExecutionPhase.SCHEDULED, ExecutionPhase.GLOBAL, ExecutionPhase.BEFORE_TRADING_START, ExecutionPhase.AFTER_TRADING_END)
def option_covered_lock(code, amount):
    strategy_log.warning('回测不支持option_covered_lock函数')
@check_arg
@ExecutionContext.enforce_phase(ExecutionPhase.ON_HANDLE_DATA, ExecutionPhase.ON_ORDER_RSP, ExecutionPhase.ON_TRADE_RSP, ExecutionPhase.ON_HANDLE_TICK, ExecutionPhase.SCHEDULED, ExecutionPhase.GLOBAL, ExecutionPhase.BEFORE_TRADING_START, ExecutionPhase.AFTER_TRADING_END)
def option_covered_unlock(code, amount):
    strategy_log.warning('回测不支持option_covered_unlock函数')
@check_arg
@ExecutionContext.enforce_phase(ExecutionPhase.ON_HANDLE_DATA, ExecutionPhase.ON_ORDER_RSP, ExecutionPhase.ON_TRADE_RSP, ExecutionPhase.ON_HANDLE_TICK, ExecutionPhase.SCHEDULED, ExecutionPhase.BEFORE_TRADING_START, ExecutionPhase.GLOBAL)
def get_ipo_stocks():
    strategy_log.warning('回测不支持get_ipo_stocks函数')
@check_arg
@ExecutionContext.enforce_phase(ExecutionPhase.BEFORE_TRADING_START, ExecutionPhase.ON_HANDLE_AUCTION, ExecutionPhase.ON_HANDLE_DATA, ExecutionPhase.ON_HANDLE_TICK, ExecutionPhase.AFTER_TRADING_END, ExecutionPhase.SCHEDULED, ExecutionPhase.GLOBAL, ExecutionPhase.ON_TRADE_RSP, ExecutionPhase.ON_ORDER_RSP)
def get_gear_price(sids=None):
    strategy_log.warning('回测不支持get_gear_price函数')
@check_arg
@ExecutionContext.enforce_phase(ExecutionPhase.ON_HANDLE_DATA, ExecutionPhase.ON_ORDER_RSP, ExecutionPhase.ON_TRADE_RSP, ExecutionPhase.ON_HANDLE_TICK, ExecutionPhase.SCHEDULED, ExecutionPhase.GLOBAL, ExecutionPhase.BEFORE_TRADING_START, ExecutionPhase.AFTER_TRADING_END)
def get_crdt_fund(cash_group=None):
    strategy_log.warning('回测不支持get_crdt_fund函数')
@ExecutionContext.enforce_phase(ExecutionPhase.BEFORE_TRADING_START, ExecutionPhase.ON_HANDLE_DATA, ExecutionPhase.ON_ORDER_RSP, ExecutionPhase.ON_TRADE_RSP, ExecutionPhase.ON_HANDLE_TICK, ExecutionPhase.AFTER_TRADING_END, ExecutionPhase.SCHEDULED, ExecutionPhase.GLOBAL)
def fund_transfer(trans_direction, occur_balance, exchange_type='1'):
    strategy_log.warning('回测不支持fund_transfer函数')
    return False
@ExecutionContext.enforce_phase(ExecutionPhase.BEFORE_TRADING_START, ExecutionPhase.ON_HANDLE_DATA, ExecutionPhase.ON_ORDER_RSP, ExecutionPhase.ON_TRADE_RSP, ExecutionPhase.ON_HANDLE_TICK, ExecutionPhase.AFTER_TRADING_END, ExecutionPhase.SCHEDULED, ExecutionPhase.GLOBAL)
def market_fund_transfer(exchange_type, occur_balance):
    strategy_log.warning('回测不支持market_fund_transfer函数')
    return False
@ExecutionContext.enforce_phase(ExecutionPhase.INITIALIZE, ExecutionPhase.ON_HANDLE_DATA, ExecutionPhase.ON_ORDER_RSP, ExecutionPhase.ON_TRADE_RSP, ExecutionPhase.ON_HANDLE_TICK, ExecutionPhase.SCHEDULED, ExecutionPhase.BEFORE_TRADING_START, ExecutionPhase.GLOBAL)
def get_manage_mark():
    strategy_log.warning('回测不支持get_manage_mark函数')
@ExecutionContext.enforce_phase(ExecutionPhase.INITIALIZE)
def set_email_info(email_address, smtp_code, email_subject):
    strategy_log.warning('回测不支持set_email_info函数')
    return False
