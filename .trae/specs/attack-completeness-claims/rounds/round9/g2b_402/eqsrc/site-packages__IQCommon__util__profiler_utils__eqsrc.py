# Source Generated with Decompyle++ (Python version)
# File: profiler_utils.pyc (Python 3.11)

import atexit
import line_profiler
line_profiler_decorator = line_profiler.LineProfiler()
atexit.register(line_profiler_decorator.print_stats)
