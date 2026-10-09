#!/bin/bash
# 17-file panel: regenerate products with the CURRENT working-tree code into $TEMP and judge them.
# Cheap pre-gate signal (the 402-file gate is the only certification, but it costs minutes).
# Never writes into site-packages: products go to $TMPDIR/panel17_<stamp>/, judged with --source.
#
# usage: bash panel17.sh [label]     # label only names the log
# Baselines are read from the repo's sealed in-place products (they equal gate-18 numbers),
# and every line prints "file cur=->  base=" so a regression is visible without arithmetic.
set -uo pipefail
cd /d/admin/.qoder/worktrees/app/f557fd/pythoncdc-main || exit 1
SPEC=.trae/specs/region-reduction-v3-full-corpus-100pct-10rounds
LAB=${1:-$(date +%H%M)}
OUT=/d/Temp/panel17_$LAB
mkdir -p "$OUT"
FILES="IQCommon/api/klinedata
IQCommon/logger/handlers
IQCommon/strategy/wizard_quant_api
IQCommon/util/trade_info_utils
IQData/api/api_base
IQData/plugins/plugin_system_realquote/real_quote
IQEngine/plugins/plugin_fly_data/fly_api/order_api
IQEngine/plugins/plugin_fly_data/strategy/strategy
IQEngine/plugins/plugin_system_event_source/realtime_event_source
IQEngine/plugins/plugin_system_risk_calculation/__init__
IQEngine/plugins/plugin_system_trade/trade_live_broker
fly/data/quote
IQEngine/plugins/plugin_system_matcher/matcher
fly/data/quotation
IQEngine/core/bar
IQEngine/core/strategy/strategy_universe
fly/dumpload/load_daily"
for f in $FILES; do
  P="site-packages/$f.pyc"
  [ -f "$P" ] || { echo "MISSING INPUT $P"; continue; }
  base=$(timeout 250 python -X utf8 scripts/pyc_verify.py single "$P" 2>&1 | grep -o "units=[0-9]*/[0-9]*" | head -1)
  timeout 250 python -X utf8 pycdc.py --region "$P" -o "$OUT/$(basename "$f").py" >/dev/null 2>&1
  if [ ! -s "$OUT/$(basename "$f").py" ]; then
    echo "$(basename $f): cur=EMPTY_PRODUCT base=$base"
    continue
  fi
  cur=$(timeout 250 python -X utf8 scripts/pyc_verify.py single "$P" --source "$OUT/$(basename "$f").py" 2>&1 | grep -o "units=[0-9]*/[0-9]*" | head -1)
  echo "$(basename $f): cur=${cur:-NOVERDICT} base=$base"
done 2>&1 | tee "$OUT/panel.log"
echo "panel log: $OUT/panel.log"
