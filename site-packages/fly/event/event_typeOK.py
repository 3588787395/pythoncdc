# Source Generated with Decompyle++ (Python version)
# File: event_type.pyc (Python 3.11)

from enum import Enum
class SystemEvent(Enum):
    __doc__ = """
    *   系统事件，由系统级的事件触发
    """
    EVENT_SYSTEM_INIT = 'event_system_init'
    EVENT_SYSTEM_PAUSE = 'event_system_pause'
    EVENT_SYSTEM_RESUME = 'event_system_resume'
    EVENT_SYSTEM_EXIT = 'event_system_exit'
class QuotationEvent(Enum):
    __doc__ = """
    *   行情事件，行情相关模块使用
    """
    EVENT_PRE_SETTLEMENT = 'event_pre_settlement'
    EVENT_SETTLEMENT = 'settlement'
    EVENT_AFTER_SETTLEMENT = 'after_settlement'
class StrategyEvent(Enum):
    __doc__ = """
    *   策略事件，策略模块使用
    """
    EVENT_USER_INIT = 'event_user_init'
    EVENT_UNIVERSE_CHANGED = 'event_universe_changed'
    EVENT_BEFORE_TRADING = 'before_trading'
    EVENT_HANDLE_DATA = 'handle_data'
    EVENT_HANDLE_TICK = 'handle_tick'
    EVENT_AFTER_TRADING = 'after_trading'
class TradeEvent(Enum):
    __doc__ = """
    *   交易事件，交易模块使用
    """
    EVENT_ORDER_PENDING_NEW = 'order_pending_new'
    EVENT_ORDER_CREATION_PASS = 'order_creation_pass'
    EVENT_ORDER_CREATION_REJECT = 'order_creation_reject'
    EVENT_ORDER_PENDING_CANCEL = 'order_pending_cancel'
    EVENT_ORDER_CANCELLATION_PASS = 'order_cancellation_pass'
    EVENT_ORDER_CANCELLATION_REJECT = 'order_cancellation_reject'
    EVENT_SECURITY_ENTRUST = 'security_entrust'
    EVENT_ENTRUST_WITHDRAW = 'entrust_withdraw'
    EVENT_ENTRUST_QUERY = 'entrust_query'
    EVENT_WITHDRAW_QUERY = 'withdraw_query'
    EVENT_FUND_QUERY = 'fund_query'
    EVENT_BUSINESS_QUERY = 'business_query'
    EVENT_POSITION_QUERY = 'position_query'
    EVENT_FUTURE_QUERY = 'future_query'
    EVENT_FUTURE_FARES_QUERY = 'future_fare_query'
    EVENT_FUTURE_MARGIN_QUERY = 'future_margin_query'
    EVENT_ORDER_UNSOLICITED_UPDATE = 'order_unsolicited_update'
    EVENT_ORDER_TRADE = 'trade'
