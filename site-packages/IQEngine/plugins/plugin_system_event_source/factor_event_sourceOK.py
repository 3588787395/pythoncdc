# Source Generated with Decompyle++ (Python version)
# File: factor_event_source.pyc (Python 3.11)

from IQEngine.interface import AbstractEventSource
from IQEngine.core.events import EventEnum
from IQEngine.const import AccountType
from IQEngine.utils.exception import user_exc
from IQEngine.utils.i18n import get_local_text as _
from IQEngine.core.events import Event
from IQEngine.const import FactorCalcMode
from IQCommon.exception import get_traceback_message
from IQCommon.logger import system_log
class FactorEventSource(AbstractEventSource):
    _trading_dates = []
    """"""
    def __init__(self, engine):
        self._engine = engine
        self._universe_changed = False
        self._engine.event_bus.append_listener(EventEnum.SYSTEM_EXIT, self._on_system_exit)
    def _on_system_exit(self, event):
        self._trading_dates.clear()
    def events(self, start_date, end_date, frequency):
        self._trading_dates = self._engine.data_proxy.get_trading_dates(start_date, end_date)
        if frequency == '1d':
            for day in self._trading_dates:
                try:
                    date = day.to_pydatetime()
                except AttributeError:
                    system_log.error(get_traceback_message())
                    date = day
                dt_before_calc = date.replace(hour=8, minute=30)
                dt_bar = date.replace(hour=15, minute=0)
                dt_after_calc = date.replace(hour=15, minute=0)
                yield Event(EventEnum.BEFORE_TRADING_START, calendar_dt=dt_before_calc, trading_dt=dt_before_calc)
                yield Event(EventEnum.HANDLE_DATA, calendar_dt=dt_bar, trading_dt=dt_bar)
                yield Event(EventEnum.AFTER_TRADING_END, calendar_dt=dt_after_calc, trading_dt=dt_after_calc)
        else:
            raise NotImplementedError(_('执行频率{}不支持').format(frequency))
