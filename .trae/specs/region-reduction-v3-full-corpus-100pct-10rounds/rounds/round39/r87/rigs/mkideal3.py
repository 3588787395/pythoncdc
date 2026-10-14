"""Variant C: correct compound-while text for loop1 AND drop the duplicated leg blocks that the
landed bytes emit a second time at lines 867-871. Diagnostic only.
"""
import sys
src = 'out_base/trade_live_broker.py'
raw = open(src, 'rb').read()
nl = b'\r\n'
lines = raw.split(nl)
def L(i):
    return lines[i - 1]
assert L(840).strip().startswith(b'while int(datetime'), L(840)[:60]
assert L(847).strip() == b'continue', L(847)[:60]
assert L(867).strip().startswith(b'while int(datetime'), L(867)[:60]
assert L(871).strip() == b'pass', L(871)[:80]
I8 = ' ' * 12
loop1 = [
    I8 + "while (int(datetime.datetime.now().strftime('%H%M')) < pre_before_trading",
    I8 + "       or int(datetime.datetime.now().strftime('%H%M')) >= int(post_after_trading)",
    I8 + "       or holiday_sync_account == '0'",
    I8 + "       and not self.engine.data_proxy.is_trading_date(datetime.datetime.now().date())):",
    I8 + "    time.sleep(60)",
]
out = lines[:839] + [s.encode() for s in loop1] + lines[847:866] + lines[877:]
open(sys.argv[1], 'wb').write(nl.join(out))
print('wrote', sys.argv[1], 'lines', len(out))
