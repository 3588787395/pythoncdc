import sys
src = 'out_base/trade_live_broker.py'
raw = open(src, 'rb').read()
nl = b'\r\n'
lines = raw.split(nl)
def L(i):  # 1-based
    return lines[i - 1]
assert L(840).strip().startswith(b'while int(datetime'), L(840)[:60]
assert L(847).strip() == b'continue', L(847)[:60]
assert L(848).strip().startswith(b'while pre_before_trading'), L(848)[:60]
assert L(866).strip().startswith(b'time_difference'), L(866)[:60]
assert L(867).strip().startswith(b'while int(datetime'), L(867)[:60]
assert L(871).strip() == b'pass', L(871)[:80]
assert L(872).strip().startswith(b'if self.engine.data_proxy.is_trading_date'), L(872)[:60]
assert L(876).strip().startswith(b'self.reconnect_flag'), L(876)[:60]
assert L(877).strip() == b'time.sleep(steps)', L(877)[:60]

I8 = ' ' * 12
loop1 = [
    I8 + "while (int(datetime.datetime.now().strftime('%H%M')) < pre_before_trading",
    I8 + "       or int(datetime.datetime.now().strftime('%H%M')) >= int(post_after_trading)",
    I8 + "       or holiday_sync_account == '0'",
    I8 + "       and not self.engine.data_proxy.is_trading_date(datetime.datetime.now().date())):",
    I8 + "    time.sleep(60)",
]
loop2 = lines[847:866]      # 848..866
ifth = lines[871:876]       # 872..876
tail = lines[876]           # 877
new = [lines[838]] + [s.encode() for s in loop1] + ifth + loop2 + [tail]   # 839 'while True:'
lines[838:877] = new
open(sys.argv[1], 'wb').write(nl.join(lines))
print('wrote', sys.argv[1])
