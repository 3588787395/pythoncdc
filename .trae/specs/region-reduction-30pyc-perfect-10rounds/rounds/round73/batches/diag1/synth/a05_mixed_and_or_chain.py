# F-BOOLOP (bar.BarData._history_bars): mixed chain `A and B or C` in a return
# guard. Decompiler re-associates it as `if A: if B or C:` so the first jump lands
# on the wrong target (126 -> 140 vs 126 -> 304).
class BarData:
    def _history_bars(self, frequency, phase):
        if self.config.frequency == '1m' and frequency == '1d' or phase == 'BEFORE_TRADING_START':
            return None
        return self.data
