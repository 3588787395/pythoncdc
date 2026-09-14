def create_user_code_iqe_pattern(content, reloads, business_mode):
    MODE_1 = 'mode1'
    MODE_2 = 'mode2'
    if business_mode or business_mode == MODE_2 or reloads and reloads:
        print('compile mode')
    elif business_mode == MODE_1:
        if not reloads:
            print('dll mode')
