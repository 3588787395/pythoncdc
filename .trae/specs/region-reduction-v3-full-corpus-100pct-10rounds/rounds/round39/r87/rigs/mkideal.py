"""Diagnostic: hand-substitute the hypothesised source for _sync_worker's compound while and
measure what the judge's unit diff reads. NOT a deliverable product.

usage: python -X utf8 work/mkideal.py <variant> <in.py> <out.py>
"""
import sys

variant, src, dst = sys.argv[1], sys.argv[2], sys.argv[3]
raw = open(src, 'rb').read()
nl = b'\r\n' if b'\r\n' in raw else b'\n'
lines = raw.split(nl)
# product file lines 840..847 (1-based) -> indices 839..846
assert lines[839].strip().startswith(b'while int(datetime'), lines[839][:80]
assert lines[846].strip().startswith(b'continue'), lines[846][:80]

I8 = ' ' * 12
if variant == 'a':
    new = [
        I8 + "while (int(datetime.datetime.now().strftime('%H%M')) < pre_before_trading",
        I8 + "       or int(datetime.datetime.now().strftime('%H%M')) >= int(post_after_trading)",
        I8 + "       or holiday_sync_account == '0'",
        I8 + "       and not self.engine.data_proxy.is_trading_date(datetime.datetime.now().date())):",
        I8 + "    time.sleep(60)",
    ]
elif variant == 'b':
    new = [
        I8 + "while int(datetime.datetime.now().strftime('%H%M')) < pre_before_trading \\",
        I8 + "        or int(datetime.datetime.now().strftime('%H%M')) >= int(post_after_trading) \\",
        I8 + "        or holiday_sync_account == '0' and not self.engine.data_proxy.is_trading_date(datetime.datetime.now().date()):",
        I8 + "    time.sleep(60)",
    ]
else:
    raise SystemExit('unknown variant')
lines[839:847] = [s.encode('utf-8') for s in new]
open(dst, 'wb').write(nl.join(lines))
print('wrote', dst, 'nl=', repr(nl))
