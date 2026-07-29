"""repro_06: 长 or 链 + try/except 包裹 + `if len(data) > 0:` 包裹层（load_bars_from_hundsun）。

load_bars_from_hundsun 的 -174 指令差异源于长 or 链分支体丢失。R3 修复未触达原始 CFG 路径，
原因是原始函数含 `if os.path.exists(DumploadDailyFile):` 前导嵌套 if + `if len(data) > 0:` 包裹层 + try/except 上下文。
本 repro 镜像原始 CFG 的三层嵌套结构。

镜像 load_bars_from_hundsun 的实际 CFG：
  - retpanel = pandas.Panel()
  - if os.path.exists(DumploadDailyFile):（前导 if）
    - if typet == 6: ...
    - if isinstance(stocks, str): stocks = [stocks]
    - try: ... except: ...
  - if len(data) > 0:（包裹层）
    - panel = pandas.Panel(data, ...)
    - if len(panel.major_axis) != 0:
      - if is_utc == '0' and (typet == 1 or ... or typet == 13): panel.major_axis = tz_convert
      - elif typet == 6: panel.major_axis = tz_localize
  - if retpanel.empty: retpanel = pandas.concat([retpanel, panel])
  - return retpanel
"""


def load_bars_from_hundsun_repro(stocks, typet, start, end, is_utc, data, retpanel):
    if os.path.exists(DumploadDailyFile):
        if typet == 6:
            source_start = qdt.datetime.strptime(start, '%Y%m%d%H%M')
        if isinstance(stocks, str):
            stocks = [stocks]
        try:
            panel = pandas.Panel(data, major_axis=dts)
        except BaseException:
            system_log.error(get_traceback_message())
    if len(data) > 0:
        panel = pandas.Panel(data, items=['open', 'close', 'high', 'low', 'volume', 'price', 'money'])
        if len(panel.major_axis) != 0:
            if is_utc == '0' and (typet == 1 or typet == 2 or typet == 3 or typet == 4 or typet == 5 or typet == 13):
                panel.major_axis = panel.major_axis.tz_localize('Asia/Shanghai').tz_convert('UTC')
            elif typet == 6:
                panel.major_axis = panel.major_axis.tz_localize(pytz.utc)
    if retpanel.empty:
        panel = pandas.concat([retpanel, panel])
    return panel
