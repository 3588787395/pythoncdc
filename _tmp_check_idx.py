#!/usr/bin/env python3
import json, sys
sys.stdout.reconfigure(encoding='utf-8')
idx = json.load(open('pyc_index.json', 'r', encoding='utf-8'))
for e in idx:
    p = e.get('path', '')
    if any(k in p.lower() for k in ['quotation', 'backtest', 'trade_schedule', 'const.', 'api_data', 'base_db', 'user_error', 'bar.']):
        print(f"{p.split('/')[-1]}: status={e.get('decompile_status','?')} rate={e.get('bytecode_match_rate','?')} round={e.get('last_tested_round','?')}")
