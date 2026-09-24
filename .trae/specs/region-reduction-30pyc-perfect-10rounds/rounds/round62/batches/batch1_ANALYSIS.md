# Round 62 batch 1 ANALYSIS (live log, appended as I go)

Targets (targets.txt):
1. site-packages/IQEngine/plugins/plugin_system_log/__init__.pyc  -- only `<module>.DefaultLogger.setup`, orig=320 decomp=313 (-7)
2. site-packages/IQEngine/plugins/plugin_system_trade/trade_live_broker.pyc -- 15 mismatched fns

## Status
- [ ] landed baseline re-measured on current bytes

## Landed baseline re-measured (current bytes, 2026-09-24)
- __init__.pyc 9/10, setup [320,313,-7,jd1,td199]  == FACTS
- trade_live_broker.pyc 104/119, all 15 rows == FACTS (deficit 15)

## fund_transfer (-35) ROOT CAUSE (probe: logs/ft.probe.txt)
CFG: 21 blocks. Regions: IfRegion@0 IF_ELIF_CHAIN -> IfRegion@60 IF_ELIF_CHAIN ->
IfRegion@184 IF_THEN_ELSE whose then-arm is TernaryRegion@300(blocks 300,334,338,340,356,360,362)
and else-arm TernaryRegion@430(430,464,468,470,486,490,492). All blocks ARE marked generated.
AST emitted stops inside the then-arm:
   If(test=error_dict.get('error_no')!=0, body=[Return(JoinedStr[...,'失败，错误原因：',Constant 'error_info'])])
   -> orelse ENTIRELY ABSENT (strategy_log.info(f...); return True lost = 27 instrs)
   -> and the then-arm body is `Return(JoinedStr)` where source is
      `strategy_log.error(f"...{error_dict.get('error_info')}...")` ; `return False`.
   The f-string's 5th piece `{error_dict.get('error_info')}` (LOAD_FAST/LOAD_METHOD/LOAD_CONST/
   PRECALL/CALL/FORMAT_VALUE) was flattened into a bare Constant 'error_info' -> the enclosing
   Call(strategy_log.error, JoinedStr) + POP_TOP + LOAD_CONST False vanished and the JoinedStr
   leaked as the block's value expression -> became a Return.
So BOTH symptoms (mangled then-arm, dropped else-arm) trace to one mis-scan of an f-string whose
FormattedValue operand is a CALL, located in the *last* block of a ternary arm.
