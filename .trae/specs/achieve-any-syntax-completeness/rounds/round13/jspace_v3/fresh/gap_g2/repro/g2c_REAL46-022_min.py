# g2c REAL46-022 min: TypeVar.__module__ records the judge's synthetic _sd_<sha12> name.
from typing import TypeVar
T = TypeVar('T')
print(T.__name__)
