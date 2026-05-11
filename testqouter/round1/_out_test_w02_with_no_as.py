=== test_w02_with_no_as.py ===
  0: def test():
  1:     import tempfile
  2:     import os
  3:     fd, path = tempfile.mkstemp()
  4:     os.close(fd)
  5:     with open(path, 'w'):
  6:         pass
  7:     result = os.path.exists(path)
  8:     os.unlink(path)
  9:     return result
 10: 

