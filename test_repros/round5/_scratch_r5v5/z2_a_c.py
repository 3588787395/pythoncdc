"""docstring."""
import os as _os
import os.path

MOD_A = 3
MOD_B: int = 5
MOD_C, MOD_D = 1, 2
MOD_E = MOD_F = 9
MOD_G = MOD_A if MOD_A > 0 else MOD_B
for _i in range(2):
    MOD_I = _i
else:
    MOD_I = -1
