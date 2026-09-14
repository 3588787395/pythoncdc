# Source Generated with Decompyle++ (Python version)
# File: minrepro_18.pyc (Python 3.11)

def create_user_code_iqe_pattern(content, reloads, business_mode):
    MODE_1 = 'mode1'
    MODE_2 = 'mode2'
    if not (business_mode or business_mode == MODE_2):
        if reloads and reloads:
            print('compile mode')
            return None
        elif not (business_mode == MODE_1 and reloads):
            print('dll mode')
            return None
