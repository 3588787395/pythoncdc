# Source Generated with Decompyle++ (Python version)
# File: a05_mixed_and_or_chain.pyc (Python 3.11)

class BarData:
    def _history_bars(self, frequency, phase):
        if not (self.config.frequency == '1m' and frequency == '1d'):
            return None
        return self.data
