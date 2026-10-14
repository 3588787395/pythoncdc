# FIX_R21-76 — clock_worker shared body entry + positive tail claim

Engineer: **r103a** · round 40 (continuing after gate 40) · unit: `<module>.RealtimeEventSource.clock_worker`
File under test: `site-packages/IQEngine/plugins/plugin_system_event_source/realtime_event_source.pyc`
Owned file(s): prefer `core/cfg/region_analyzer.py`. Mirror: `D:/Temp/r103`.

## 0. Platform (installed + re-hashed BEFORE anything)

`hashlib.sha256(open(p,'rb').read()).hexdigest()[:16]`:

| file | sha16 | source |
|---|---|---|
| `core/cfg/region_analyzer.py` | `1471c92eca157e46` | `$SP/rounds/round40/r93/region_analyzer_R21-64a_FINAL.py` |
| `core/cfg/region_ast_generator.py` | `566ff5c502276e48` | `$SP/rounds/round40/r102/CANDIDATE_r2174_566ff5c502276e48.py` |

Both match the brief. Repo HEAD core pair is identical to this pair (verified). Mirror root repointed to `D:/Temp/r103`.

## 1. Base reproduction on the landed platform

- `realtime_event_source.pyc` → `status=failure units=12/13`, sole failure `clock_worker`, `Different control flow`. REPRODUCED.
- `trade_live_broker.pyc` → `status=success units=128/128`. REPRODUCED (confirms the platform is the true landed pair).

### Discrepancy vs the brief's window numbers (recorded honestly)

The brief states the current product reads `unit_diff/allwin` delta `+2` and `win_r91` `orig=1442 prod=1448 delta=+6`,
4 tiny insert windows. On the LANDED platform I measure (fresh regen, `--source`):

- allwin_r63: `len orig=1424 prod=1311 delta=-113`
- win_r91: `orig instrs=1442 prod instrs=1330 delta=-112`, **15 windows**

The orig side (1442 / 1424) matches exactly, so the pyc + code-object extraction is correct; only the PROD side differs.
I verified this is NOT my mirror or R21-74: under the pre-R21-74 generator `0f4c3898298e6f2e` realtime clock_worker
reads the SAME `delta=-113` (broker drops back to 127/128, so `566ff5c5` is required for the gate). The near-parity
`+2` numbers in the brief were measured on an OLDER analyzer base (r101's `21548`-byte product). On the mandated
`1471c92e + 566ff5c5` pair the real defect is far larger: a contiguous 112-instruction statement block
(original offsets `@7972..@8586`, source lines 498–524) is DROPPED entirely by the decompiler. The Decompyle++
output `realtime_event_source.py` drops the SAME block (it also reads 12/13), so this region is a genuine
control-flow-hard block, not a mirror artifact.

### What is dropped (from `dis`, stdlib only)

Inside the `while self.active:` loop, within the first branch
`if before_trading <= now_time < pm_close or self.before_trading_date == self.initial_trading_date:`
(immediately after the `for i in range(60): try/except BaseException/else break` persist loop):

```
L498 if persist_flag is False:
L499     set_trade_stop_status(self._engine.config.strategy.trade_id)
L500     system_log.error('获取交易持久化对象超时，系统退出')
L501     self.event_queue.put((dt, EventEnum.SYSTEM_EXIT))
L502     return
L504 self.before_trading_date = now_date
L507 try: server_restart_do_before_type = str(self._engine.config.user.server_restart_not_do_before)
L508 except AttributeError:
L509     server_restart_do_before_type = '0'
L511 if server_restart_do_before_type == '0':
L512     self.put_before_trading_start()
L515 elif broker_persist is not None:
L516     on_before_trading_start_time_info = broker_persist.get('on_before_trading_start_time')
L517     if on_before_trading_start_time_info is not None:
L518         today_date = now_date.strftime('%Y-%m-%d')
L519         if today_date in on_before_trading_start_time_info:
L520             today_info = on_before_trading_start_time_info[today_date]
L521             if len(today_info) == 0:
L522                 self.put_before_trading_start()
L524         else:
                   self.put_before_trading_start()
```

Every `put_before_trading_start()` arm exits to the loop back-edge/merge `@9194` (the `while self.active:` header
re-check); no per-statement label survives, which is exactly the "shared body entry / positive tail claim" failure
the brief's ownership analysis (§ known facts) describes — but here it manifests as a full DROP, not a manufactured
`JUMP_FORWARD`.

## 2. GOLD oracle (planned / in progress)
See `GOLD_realtime_event_source_PROOF.py` and the judge line recorded below once built.
