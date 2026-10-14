#!/bin/bash
# Install a mirror-built patched file into the repo and measure it, in the campaign's fixed sequence:
#   backup original bytes -> whole-file copy -> py_compile -> marker count -> per-unit readings.
# Why a script and not ad-hoc commands: four tickets this session were adjudicated by hand-typed
# sequences, and twice a step was skipped (the stale-product and anchor-drift incidents).
#
# Usage: install_and_measure.sh <patched_file> <repo_relative_target> [marker]
#   e.g. install_and_measure.sh /d/Temp/r133/wt/core/cfg/region_analyzer.py core/cfg/region_analyzer.py r11-b133
# The patched file must be byte-complete (mirror diffs do NOT `git apply` in this repo).
set -uo pipefail
SRC=${1:?patched file required}
DST=${2:?repo-relative target required}
MARK=${3:-}
cd /d/admin/.qoder/worktrees/app/f557fd/pythoncdc-main || exit 1
STAMP=$(date +%H%M)
LOG=/d/Temp/r10gate/install_${STAMP}.log
ORIG=/d/Temp/r10gate/backup_${STAMP}_$(basename "$DST")
[ -f "$SRC" ] || { echo "no such patched file: $SRC"; exit 1; }
cp "$DST" "$ORIG"
OLDSHA=$(python -X utf8 -c "import hashlib,sys;print(hashlib.sha256(open(sys.argv[1],'rb').read()).hexdigest()[:16])" "$ORIG")
echo "[install] backup $ORIG sha $(python -X utf8 -c "import hashlib,sys;print(hashlib.sha256(open(sys.argv[1],'rb').read()).hexdigest()[:16])" "$ORIG")"
cp "$SRC" "$DST"
NEW=$(python -X utf8 -c "import hashlib,sys;print(hashlib.sha256(open(sys.argv[1],'rb').read()).hexdigest()[:16])" "$DST")
echo "[install] landed $DST sha $NEW"
python -X utf8 -m py_compile "$DST" || { echo "[install] PY_COMPILE FAILED -> revert"; cp "$ORIG" "$DST"; exit 1; }
# Two refusals, both learned the hard way this session:
#  (1) a no-op install: a mirror left mid-A/B holds the PRISTINE file, so its "patched" copy is
#      byte-identical to the seal and every reading afterward is silently HEAD;
#  (2) installing a file whose guard marker never landed (patch lost, wrong branch kept).
if [ "$NEW" = "$OLDSHA" ]; then
  echo "[install] REFUSED: patched file hash equals the original ($NEW) - nothing changed.";
  echo "           镜像可能正处于 A/B 之间的还原态；等施工者交付 patch 文件或最终声明后再装。";
  cp "$ORIG" "$DST"; exit 3;
fi
if [ -n "$MARK" ]; then
  CNT=$(grep -c "$MARK" "$DST")
  echo "[install] marker '$MARK' count: $CNT"
  if [ "$CNT" -eq 0 ]; then echo "[install] REFUSED: 目标字节里没有守卫标记 -> 回滚"; cp "$ORIG" "$DST"; exit 4; fi
fi
{
  for P in site-packages/fly/dumpload/load_daily.pyc \
           site-packages/IQCommon/util/trade_info_utils.pyc \
           site-packages/IQEngine/plugins/plugin_system_matcher/matcher.pyc \
           site-packages/IQCommon/logger/handlers.pyc \
           site-packages/fly/data/quotation.pyc; do
    echo "### $P"
    timeout 250 python -X utf8 pycdc.py "$P" -o "${P%.pyc}OK.py" >/dev/null 2>&1
    timeout 250 python -X utf8 scripts/pyc_verify.py single "$P" 2>&1 | tail -1
  done
  echo "### anchor roster"
  timeout 290 python -X utf8 scripts/pyc_verify.py batch --index D:/Temp/r9w16/anchor_index.json --json D:/Temp/r10gate/anchor_new.json 2>&1 | grep -E '"units_success"|"units_total"|files_total' | head -3
  echo "### small34"
  timeout 290 python -X utf8 scripts/pyc_verify.py batch --index .trae/specs/region-reduction-v3-full-corpus-100pct-10rounds/baseline/small34_index.json --json D:/Temp/r10gate/small34_new.json 2>&1 | grep -E '"units_success"|"files_total"' | head -2
} 2>&1 | tee "$LOG"
echo "[install] measurements logged to $LOG"
echo "[install] to revert: cp \"$ORIG\" \"$DST\""
