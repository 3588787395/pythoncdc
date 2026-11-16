def _host():
    pass

import os
import os.path as p
from sys import path

def outer():
    global _G
    x = 1
    del x
    assert x is None
    return p.join('a', 'b')
