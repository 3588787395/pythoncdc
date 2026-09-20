# -*- coding: utf-8 -*-
"""R13b-01  verdict (D)  family: spurious `else:` / wrong else-attach level.

Targets (both adjudicated (D) by compiling the corrected source with 3.11.7):
  IQEngine/plugins/plugin_fly_data/fly_api/history_api.pyc :: <module>.get_price
  fly/simtradding/pboxAccount_jupyterhub.pyc               :: <module>.getVaildAccount

Shape: an `if` whose then-arm is a ladder of `if/elif/... : return` that can
*fall through* (the ladder has no else).  CPython then lets the false path of
the outer test fall straight into the code that follows the `if` - the outer
`if` has NO else.  The decompiler computes merge=None (the then-arm is not a
sink) and turns that continuation into `else:`; the whole tail is indented one
level too deep, an `else:` appears out of nowhere and CPython must additionally
emit the implicit `LOAD_CONST None; RETURN_VALUE` tail (seq_len +2).

Stage implicated:
  core/cfg/region_analyzer.py::_identify_conditional_regions (def at 15367)
      merge determination 17028-17039, the sink guard 17072-17074
      `_if_arm_is_sink` 25369, `_collect_branch_blocks` 25448 (calls 17054/17151)
      region built by `_build_basic_if_region` 17366 (IfRegion at 17800)
"""
VERDICT = 'D'
TARGET = ('IQEngine/plugins/plugin_fly_data/fly_api/history_api.pyc :: <module>.get_price; '
          'fly/simtradding/pboxAccount_jupyterhub.pyc :: <module>.getVaildAccount')
STAGE = 'region_analyzer._identify_conditional_regions:17028-17074 (+ _collect_branch_blocks:25448)'
FAMILY = 'spurious-else'
EXPECT = 'MATCH'

SRC = '''
def get_price(security, start_date, end_date, frequency):
    if start_date is not None:
        start_date = check_datetime_common(start_date)
        if start_date is None:
            return None
        elif start_date > allowd_date:
            strategy_log.error('bad start_date')
            return None
    frequency = FREQUENCY_DICT.get(frequency, frequency)
    if frequency not in ALL_FREQUENCY:
        strategy_log.error('bad frequency')
        return None
    else:
        nd_array = get_price_common(security, start_date, end_date, frequency)
        return nd_array
'''
