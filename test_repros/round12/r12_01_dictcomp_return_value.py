# -*- coding: utf-8 -*-
"""R12-01: dict comprehension with filter as return value inside try body.
Root family: Round 9 comprehension return-vs-statement (merger_storage.get_merger_date_info).
Expected: return {comp}   Defect: Expr(comp) + return None
"""
import sys
sys.path.insert(0, '.')
from core.cfg import decompile

SRC = '''
def get_merger_date_info(self, symbol_list, datetime):
    try:
        return {symbol: self.get_merger_info(symbol) for symbol in self._time_table[datetime] if symbol in symbol_list}
    except KeyError:
        system_log.error(get_traceback_message())
        return {}
'''

def check():
    out = decompile(SRC, '<r12_01>', use_region=True)
    ok = 'return {' in out and 'return None' not in out.split('except')[0]
    print('OUTPUT:')
    print(out)
    print('PASS' if ok else 'FAIL: comprehension return downgraded')

if __name__ == '__main__':
    check()
