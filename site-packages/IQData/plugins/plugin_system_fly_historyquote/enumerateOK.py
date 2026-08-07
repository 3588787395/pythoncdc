# Source Generated with Decompyle++ (Python version)
# File: enumerate.pyc (Python 3.11)

from IQData.enumerate import AssetType, DATA_INDEX as DATA_INDEX_, DATA_INDEX_DICT as DATA_INDEX_DICT_, Frequency as Frequency_, IQEnum
ASSET_TYPE_DICT = {'1m': 1, '5m': 2, '15m': 3, '30m': 4, '60m': 5, '1d': 6, 'w': 7, 'mo': 8, '120m': 13}
FREQUENCY_TUPLE = (('MINUTE5', '5m'), ('MINUTE15', '15m'), ('MINUTE30', '30m'), ('MINUTE60', '60m'), ('MINUTE120', '120m'), ('WEEK', 'w'), ('MONTH', 'mo'), ('QUARTER', 'q'), ('YEAR', 'y'))
FREQUENCY_DICT = {k: v.value for k, v in Frequency_.__members__.items()}
FREQUENCY_DICT.update(dict(FREQUENCY_TUPLE))
Frequency = IQEnum('Frequency', FREQUENCY_DICT)
EXTRA_FREQUENCY = tuple((Frequency[k] for k, v in FREQUENCY_TUPLE))
DATA_INDEX = DATA_INDEX_ + [(AssetType.STOCK.value, f.value) for f in EXTRA_FREQUENCY]
DATA_INDEX_DICT = {(AssetType.STOCK.value, f.value): i for f, i in zip(EXTRA_FREQUENCY, range(len(DATA_INDEX_), len(DATA_INDEX_) + len(EXTRA_FREQUENCY)))}
DATA_INDEX_DICT.update(DATA_INDEX_DICT_)
