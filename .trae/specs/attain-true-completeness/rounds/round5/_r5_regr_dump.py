import io
import re
import sys

files = {
    r'F:\Downloads\pythoncdc-main\site-packages\IQCommon\util\trade_info_utilsOK.py': ['trade_operation'],
    r'F:\Downloads\pythoncdc-main\site-packages\IQEngine\utils\schedulerOK.py':
        ['_trade_job', 'on_handle_data', 'on_before_trading', 'on_after_trading', 'on_post_after_trading'],
    r'F:\Downloads\pythoncdc-main\site-packages\fly\data\quote_handlerOK.py': ['get_holiday_local'],
}
for path, names in files.items():
    print('=' * 30, path)
    lines = io.open(path, encoding='utf-8-sig', errors='replace').read().splitlines()
    for i, l in enumerate(lines):
        m = re.match(r'^(\s*)def (\w+)\(', l)
        if m and m.group(2) in names:
            ind = len(m.group(1))
            j = i + 1
            while j < len(lines):
                l2 = lines[j]
                if l2.strip() and (len(l2) - len(l2.lstrip())) <= ind and re.match(r'^\s*(def |class |@)', l2):
                    break
                j += 1
            print('--- %s (lines %d-%d)' % (m.group(2), i + 1, j))
            print('\n'.join(lines[i:j]))
