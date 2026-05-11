"""
字节码操作模块
包含字节码操作码定义和处理函数
支持Python 3.11+ 字节码
"""

from typing import Optional, Tuple, Dict


class Opcode:
    """字节码操作码类"""
    
    PYC_HAVE_ARG = 90
    
    # Python 3.11+ opcodes (来自python_3_11.cpp)
    CACHE = 0
    POP_TOP = 1
    PUSH_NULL = 2
    NOP = 9
    UNARY_POSITIVE = 10
    UNARY_NEGATIVE = 11
    UNARY_NOT = 12
    UNARY_INVERT = 15
    BINARY_SUBSCR = 25
    GET_LEN = 30
    MATCH_MAPPING = 31
    MATCH_SEQUENCE = 32
    MATCH_KEYS = 33
    PUSH_EXC_INFO = 35
    CHECK_EXC_MATCH = 36
    CHECK_EG_MATCH = 37
    WITH_EXCEPT_START = 49
    GET_AITER = 50
    GET_ANEXT = 51
    BEFORE_ASYNC_WITH = 52
    BEFORE_WITH = 53
    END_ASYNC_FOR = 54
    STORE_SUBSCR = 60
    DELETE_SUBSCR = 61
    GET_ITER = 68
    GET_YIELD_FROM_ITER = 69
    PRINT_EXPR = 70
    LOAD_BUILD_CLASS = 71
    LOAD_ASSERTION_ERROR = 74
    RETURN_GENERATOR = 75
    LIST_TO_TUPLE = 82
    RETURN_VALUE = 83
    IMPORT_STAR = 84
    SETUP_ANNOTATIONS = 85
    YIELD_VALUE = 86
    ASYNC_GEN_WRAP = 87
    PREP_RERAISE_STAR = 88
    POP_EXCEPT = 89
    STORE_NAME_A = 90
    DELETE_NAME_A = 91
    UNPACK_SEQUENCE_A = 92
    FOR_ITER_A = 93
    UNPACK_EX_A = 94
    STORE_ATTR_A = 95
    DELETE_ATTR_A = 96
    STORE_GLOBAL_A = 97
    DELETE_GLOBAL_A = 98
    SWAP_A = 99
    LOAD_CONST_A = 100
    LOAD_NAME_A = 101
    BUILD_TUPLE_A = 102
    BUILD_LIST_A = 103
    BUILD_SET_A = 104
    BUILD_MAP_A = 105
    LOAD_ATTR_A = 106
    COMPARE_OP_A = 107
    IMPORT_NAME_A = 108
    IMPORT_FROM_A = 109
    JUMP_FORWARD_A = 110
    JUMP_IF_FALSE_OR_POP_A = 111
    JUMP_IF_TRUE_OR_POP_A = 112
    POP_JUMP_FORWARD_IF_FALSE_A = 114
    POP_JUMP_FORWARD_IF_TRUE_A = 115
    LOAD_GLOBAL_A = 116
    IS_OP_A = 117
    CONTAINS_OP_A = 118
    RERAISE_A = 119
    COPY_A = 120
    BINARY_OP_A = 122
    SEND_A = 123
    LOAD_FAST_A = 124
    STORE_FAST_A = 125
    DELETE_FAST_A = 126
    POP_JUMP_FORWARD_IF_NOT_NONE_A = 128
    POP_JUMP_FORWARD_IF_NONE_A = 129
    RAISE_VARARGS_A = 130
    GET_AWAITABLE_A = 131
    MAKE_FUNCTION_A = 132
    BUILD_SLICE_A = 133
    JUMP_BACKWARD_NO_INTERRUPT_A = 134
    MAKE_CELL_A = 135
    LOAD_CLOSURE_A = 136
    LOAD_DEREF_A = 137
    STORE_DEREF_A = 138
    DELETE_DEREF_A = 139
    JUMP_BACKWARD_A = 140
    CALL_FUNCTION_EX_A = 142
    EXTENDED_ARG_A = 144
    LIST_APPEND_A = 145
    SET_ADD_A = 146
    MAP_ADD_A = 147
    LOAD_CLASSDEREF_A = 148
    COPY_FREE_VARS_A = 149
    RESUME_A = 151
    MATCH_CLASS_A = 152
    FORMAT_VALUE_A = 155
    BUILD_CONST_KEY_MAP_A = 156
    BUILD_STRING_A = 157
    LOAD_METHOD_A = 160
    PRECALL_A = 166
    CALL_A = 171
    KW_NAMES_A = 172
    POP_JUMP_BACKWARD_IF_NOT_NONE_A = 173
    POP_JUMP_BACKWARD_IF_NONE_A = 174
    POP_JUMP_BACKWARD_IF_FALSE_A = 175
    POP_JUMP_BACKWARD_IF_TRUE_A = 176
    
    # Python 3.0-3.10 操作码 (基于C++版本)
    BINARY_MATRIX_MULTIPLY = 16
    INPLACE_MATRIX_MULTIPLY = 17
    GET_LEN = 30
    MATCH_MAPPING = 31
    MATCH_SEQUENCE = 32
    MATCH_KEYS = 33
    COPY_DICT_WITHOUT_KEYS = 34
    JUMP_ABSOLUTE_A = 113
    JUMP_IF_NOT_EXC_MATCH_A = 121
    SETUP_FINALLY_A = 122
    SETUP_LOOP_A = 120  # Python 3.0-3.10 循环设置指令
    GEN_START_A = 129
    CALL_FUNCTION_A = 131
    CALL_FUNCTION_KW_A = 141
    CALL_FUNCTION_EX_A = 142
    SETUP_WITH_A = 143
    SETUP_ASYNC_WITH_A = 154
    CALL_METHOD_A = 161
    LIST_EXTEND_A = 162
    SET_UPDATE_A = 163
    DICT_MERGE_A = 164
    DICT_UPDATE_A = 165
    GET_AWAITABLE = 73
    YIELD_FROM = 72
    ROT_N_A = 99
    
    # Python 3.13+ 新增操作符（来自pycdc，避免重复）
    CLEANUP_THROW = 8
    END_FOR = 11
    END_SEND = 12
    EXIT_INIT_CHECK = 13
    FORMAT_SIMPLE = 14
    FORMAT_WITH_SPEC = 15
    INTERPRETER_EXIT = 22
    LOAD_LOCALS = 25
    MAKE_FUNCTION = 132  # Python 3.11+ 的 MAKE_FUNCTION opcode
    STORE_SLICE = 38
    TO_BOOL = 40
    
    # Python 1.0-2.7 操作码 (基于C++版本)
    # 注意：这些操作码在Python 3.11+中已经被移除或替换
    # 使用负值表示这些操作码只在旧版本中使用
    STOP_CODE = -1
    ROT_TWO = -2  # 在Python 3.11+中被PUSH_NULL (2)替换
    ROT_THREE = -3
    DUP_TOP = -4
    ROT_FOUR = -5
    NOP = 9
    UNARY_POSITIVE = 10
    UNARY_NEGATIVE = 11
    UNARY_NOT = 12
    UNARY_CONVERT = 13
    UNARY_INVERT = 15
    BINARY_POWER = 19
    BINARY_MULTIPLY = 20
    BINARY_DIVIDE = 21
    BINARY_MODULO = 22
    BINARY_ADD = 23
    BINARY_SUBTRACT = 24
    BINARY_SUBSCR = 25
    BINARY_FLOOR_DIVIDE = 26
    BINARY_TRUE_DIVIDE = 27
    INPLACE_FLOOR_DIVIDE = 28
    INPLACE_TRUE_DIVIDE = 29
    SLICE_0 = 30
    SLICE_1 = 31
    SLICE_2 = 32
    SLICE_3 = 33
    STORE_SLICE_0 = 40
    STORE_SLICE_1 = 41
    STORE_SLICE_2 = 42
    STORE_SLICE_3 = 43
    DELETE_SLICE_0 = 50
    DELETE_SLICE_1 = 51
    DELETE_SLICE_2 = 52
    DELETE_SLICE_3 = 53
    STORE_MAP = 54
    INPLACE_ADD = 55
    INPLACE_SUBTRACT = 56
    INPLACE_MULTIPLY = 57
    INPLACE_DIVIDE = 58
    INPLACE_MODULO = 59
    STORE_SUBSCR = 60
    DELETE_SUBSCR = 61
    BINARY_LSHIFT = 62
    BINARY_RSHIFT = 63
    BINARY_AND = 64
    BINARY_XOR = 65
    BINARY_OR = 66
    INPLACE_POWER = 67
    GET_ITER = 68
    PRINT_EXPR = 70
    PRINT_ITEM = 71
    PRINT_NEWLINE = 72
    PRINT_ITEM_TO = 73
    PRINT_NEWLINE_TO = 74
    INPLACE_LSHIFT = 75
    INPLACE_RSHIFT = 76
    INPLACE_AND = 77
    INPLACE_XOR = 78
    INPLACE_OR = 79
    BREAK_LOOP = 80
    WITH_CLEANUP = 81
    LOAD_LOCALS = 82
    RETURN_VALUE = 83
    IMPORT_STAR = 84
    EXEC_STMT = 85
    YIELD_VALUE = 86
    POP_BLOCK = 87
    END_FINALLY = 88
    # 🔧 关键修复：在Python 3.11+中，89是POP_EXCEPT，不是BUILD_CLASS
    # BUILD_CLASS = 89  # 旧版本定义，已移除
    ROT_FOUR = 92
    SET_ADD = 93
    YIELD_FROM = 94
    BUILD_STRING = 157
    CALL_METHOD = 161
    
    HAVE_ARGUMENT = 90


def opcode_to_name(opcode: int, version: Tuple[int, int] = None) -> str:
    """将操作码转换为名称
    
    Args:
        opcode: 操作码值
        version: Python版本元组，默认为(3, 11) - 最新版本
    """
    # 默认使用最新版本
    if version is None:
        version = (3, 11)
    
    major, minor = version
    
    # 根据版本选择正确的操作码映射
    if major == 3 and minor >= 11:
        # Python 3.11+ 映射
        python311_opcodes = {
            0: 'CACHE',
            1: 'POP_TOP',
            2: 'PUSH_NULL',
            4: 'MAKE_FUNCTION',
            9: 'NOP',
            10: 'UNARY_POSITIVE',
            11: 'UNARY_NEGATIVE',
            12: 'UNARY_NOT',
            15: 'UNARY_INVERT',
            25: 'BINARY_SUBSCR',
            30: 'GET_LEN',
            31: 'MATCH_MAPPING',
            32: 'MATCH_SEQUENCE',
            33: 'MATCH_KEYS',
            35: 'PUSH_EXC_INFO',
            36: 'CHECK_EXC_MATCH',
            37: 'CHECK_EG_MATCH',
            49: 'WITH_EXCEPT_START',
            50: 'GET_AITER',
            51: 'GET_ANEXT',
            52: 'BEFORE_ASYNC_WITH',
            53: 'BEFORE_WITH',
            54: 'END_ASYNC_FOR',
            60: 'STORE_SUBSCR',
            61: 'DELETE_SUBSCR',
            68: 'GET_ITER',
            69: 'GET_YIELD_FROM_ITER',
            70: 'PRINT_EXPR',
            71: 'LOAD_BUILD_CLASS',
            74: 'LOAD_ASSERTION_ERROR',
            75: 'RETURN_GENERATOR',
            82: 'LIST_TO_TUPLE',
            83: 'RETURN_VALUE',
            84: 'IMPORT_STAR',
            85: 'SETUP_ANNOTATIONS',
            86: 'YIELD_VALUE',
            87: 'ASYNC_GEN_WRAP',
            88: 'PREP_RERAISE_STAR',
            89: 'POP_EXCEPT',
            90: 'STORE_NAME_A',
            91: 'DELETE_NAME_A',
            92: 'UNPACK_SEQUENCE_A',
            93: 'FOR_ITER_A',
            94: 'UNPACK_EX_A',
            95: 'STORE_ATTR_A',
            96: 'DELETE_ATTR_A',
            97: 'STORE_GLOBAL_A',
            98: 'DELETE_GLOBAL_A',
            99: 'SWAP_A',
            100: 'LOAD_CONST_A',
            101: 'LOAD_NAME_A',
            102: 'BUILD_TUPLE_A',
            103: 'BUILD_LIST_A',
            104: 'BUILD_SET_A',
            105: 'BUILD_MAP_A',
            106: 'LOAD_ATTR_A',
            107: 'COMPARE_OP_A',
            108: 'IMPORT_NAME_A',
            109: 'IMPORT_FROM_A',
            110: 'JUMP_FORWARD_A',
            111: 'JUMP_IF_FALSE_OR_POP_A',
            112: 'JUMP_IF_TRUE_OR_POP_A',
            114: 'POP_JUMP_FORWARD_IF_FALSE_A',
            115: 'POP_JUMP_FORWARD_IF_TRUE_A',
            116: 'LOAD_GLOBAL_A',
            117: 'IS_OP_A',
            118: 'CONTAINS_OP_A',
            119: 'RERAISE_A',
            120: 'COPY_A',
            122: 'BINARY_OP_A',
            123: 'SEND_A',
            124: 'LOAD_FAST_A',
            125: 'STORE_FAST_A',
            126: 'DELETE_FAST_A',
            128: 'POP_JUMP_FORWARD_IF_NOT_NONE_A',
            129: 'POP_JUMP_FORWARD_IF_NONE_A',
            130: 'RAISE_VARARGS_A',
            131: 'GET_AWAITABLE_A',
            132: 'MAKE_FUNCTION_A',
            133: 'BUILD_SLICE_A',
            134: 'JUMP_BACKWARD_NO_INTERRUPT_A',
            135: 'MAKE_CELL_A',
            136: 'LOAD_CLOSURE_A',
            137: 'LOAD_DEREF_A',
            138: 'STORE_DEREF_A',
            139: 'DELETE_DEREF_A',
            140: 'JUMP_BACKWARD_A',
            142: 'CALL_FUNCTION_EX_A',
            144: 'EXTENDED_ARG_A',
            145: 'LIST_APPEND_A',
            146: 'SET_ADD_A',
            147: 'MAP_ADD_A',
            148: 'LOAD_CLASSDEREF_A',
            149: 'COPY_FREE_VARS_A',
            151: 'RESUME_A',
            152: 'MATCH_CLASS_A',
            155: 'FORMAT_VALUE_A',
            156: 'BUILD_CONST_KEY_MAP_A',
            157: 'BUILD_STRING_A',
            160: 'LOAD_METHOD_A',
            166: 'PRECALL_A',
            171: 'CALL_A',
            172: 'KW_NAMES_A',
            173: 'POP_JUMP_BACKWARD_IF_NOT_NONE_A',
            174: 'POP_JUMP_BACKWARD_IF_NONE_A',
            175: 'POP_JUMP_BACKWARD_IF_FALSE_A',
            176: 'POP_JUMP_BACKWARD_IF_TRUE_A',
        }
        
        if opcode in python311_opcodes:
            return python311_opcodes[opcode]
        
    elif major == 3 and minor >= 0:
        # Python 3.0-3.10 映射
        python310_opcodes = {
            1: 'POP_TOP',
            2: 'ROT_TWO',
            3: 'ROT_THREE',
            4: 'DUP_TOP',
            5: 'DUP_TOP_TWO',
            6: 'ROT_FOUR',
            9: 'NOP',
            10: 'UNARY_POSITIVE',
            11: 'UNARY_NEGATIVE',
            12: 'UNARY_NOT',
            15: 'UNARY_INVERT',
            16: 'BINARY_MATRIX_MULTIPLY',
            17: 'INPLACE_MATRIX_MULTIPLY',
            19: 'BINARY_POWER',
            20: 'BINARY_MULTIPLY',
            22: 'BINARY_MODULO',
            23: 'BINARY_ADD',
            24: 'BINARY_SUBTRACT',
            25: 'BINARY_SUBSCR',
            26: 'BINARY_FLOOR_DIVIDE',
            27: 'BINARY_TRUE_DIVIDE',
            28: 'INPLACE_FLOOR_DIVIDE',
            29: 'INPLACE_TRUE_DIVIDE',
            30: 'GET_LEN',
            31: 'MATCH_MAPPING',
            32: 'MATCH_SEQUENCE',
            33: 'MATCH_KEYS',
            34: 'COPY_DICT_WITHOUT_KEYS',
            49: 'WITH_EXCEPT_START',
            50: 'GET_AITER',
            51: 'GET_ANEXT',
            52: 'BEFORE_ASYNC_WITH',
            54: 'END_ASYNC_FOR',
            55: 'INPLACE_ADD',
            56: 'INPLACE_SUBTRACT',
            57: 'INPLACE_MULTIPLY',
            59: 'INPLACE_MODULO',
            60: 'STORE_SUBSCR',
            61: 'DELETE_SUBSCR',
            62: 'BINARY_LSHIFT',
            63: 'BINARY_RSHIFT',
            64: 'BINARY_AND',
            65: 'BINARY_XOR',
            66: 'BINARY_OR',
            67: 'INPLACE_POWER',
            68: 'GET_ITER',
            69: 'GET_YIELD_FROM_ITER',
            70: 'PRINT_EXPR',
            71: 'LOAD_BUILD_CLASS',
            72: 'YIELD_FROM',
            73: 'GET_AWAITABLE',
            74: 'LOAD_ASSERTION_ERROR',
            75: 'INPLACE_LSHIFT',
            76: 'INPLACE_RSHIFT',
            77: 'INPLACE_AND',
            78: 'INPLACE_XOR',
            79: 'INPLACE_OR',
            82: 'LIST_TO_TUPLE',
            83: 'RETURN_VALUE',
            84: 'IMPORT_STAR',
            85: 'SETUP_ANNOTATIONS',
            86: 'YIELD_VALUE',
            87: 'POP_BLOCK',
            89: 'POP_EXCEPT',
            90: 'STORE_NAME_A',
            91: 'DELETE_NAME_A',
            92: 'UNPACK_SEQUENCE_A',
            93: 'FOR_ITER_A',
            94: 'UNPACK_EX_A',
            95: 'STORE_ATTR_A',
            96: 'DELETE_ATTR_A',
            97: 'STORE_GLOBAL_A',
            98: 'DELETE_GLOBAL_A',
            99: 'ROT_N_A',
            100: 'LOAD_CONST_A',
            101: 'LOAD_NAME_A',
            102: 'BUILD_TUPLE_A',
            103: 'BUILD_LIST_A',
            104: 'BUILD_SET_A',
            105: 'BUILD_MAP_A',
            106: 'LOAD_ATTR_A',
            107: 'COMPARE_OP_A',
            108: 'IMPORT_NAME_A',
            109: 'IMPORT_FROM_A',
            110: 'JUMP_FORWARD_A',
            111: 'JUMP_IF_FALSE_OR_POP_A',
            112: 'JUMP_IF_TRUE_OR_POP_A',
            113: 'JUMP_ABSOLUTE_A',
            114: 'POP_JUMP_IF_FALSE_A',
            115: 'POP_JUMP_IF_TRUE_A',
            116: 'LOAD_GLOBAL_A',
            117: 'IS_OP_A',
            118: 'CONTAINS_OP_A',
            119: 'RERAISE_A',
            121: 'JUMP_IF_NOT_EXC_MATCH_A',
            122: 'SETUP_FINALLY_A',
            124: 'LOAD_FAST_A',
            125: 'STORE_FAST_A',
            126: 'DELETE_FAST_A',
            129: 'GEN_START_A',
            130: 'RAISE_VARARGS_A',
            131: 'CALL_FUNCTION_A',
            132: 'MAKE_FUNCTION_A',
            133: 'BUILD_SLICE_A',
            135: 'LOAD_CLOSURE_A',
            136: 'LOAD_DEREF_A',
            137: 'STORE_DEREF_A',
            138: 'DELETE_DEREF_A',
            141: 'CALL_FUNCTION_KW_A',
            142: 'CALL_FUNCTION_EX_A',
            143: 'SETUP_WITH_A',
            144: 'EXTENDED_ARG_A',
            145: 'LIST_APPEND_A',
            146: 'SET_ADD_A',
            147: 'MAP_ADD_A',
            148: 'LOAD_CLASSDEREF_A',
            152: 'MATCH_CLASS_A',
            154: 'SETUP_ASYNC_WITH_A',
            155: 'FORMAT_VALUE_A',
            156: 'BUILD_CONST_KEY_MAP_A',
            157: 'BUILD_STRING_A',
            160: 'LOAD_METHOD_A',
            161: 'CALL_METHOD_A',
            162: 'LIST_EXTEND_A',
            163: 'SET_UPDATE_A',
            164: 'DICT_MERGE_A',
            165: 'DICT_UPDATE_A',
        }
        
        if opcode in python310_opcodes:
            return python310_opcodes[opcode]
    
    # Python 1.0-2.7 映射
    python27_opcodes = {
        0: 'STOP_CODE',
        2: 'ROT_TWO',
        3: 'ROT_THREE',
        4: 'DUP_TOP',
        5: 'ROT_FOUR',
        9: 'NOP',
        10: 'UNARY_POSITIVE',
        11: 'UNARY_NEGATIVE',
        12: 'UNARY_NOT',
        13: 'UNARY_CONVERT',
        15: 'UNARY_INVERT',
        19: 'BINARY_POWER',
        20: 'BINARY_MULTIPLY',
        21: 'BINARY_DIVIDE',
        22: 'BINARY_MODULO',
        23: 'BINARY_ADD',
        24: 'BINARY_SUBTRACT',
        25: 'BINARY_SUBSCR',
        26: 'BINARY_FLOOR_DIVIDE',
        27: 'BINARY_TRUE_DIVIDE',
        28: 'INPLACE_FLOOR_DIVIDE',
        29: 'INPLACE_TRUE_DIVIDE',
        30: 'SLICE_0',
        31: 'SLICE_1',
        32: 'SLICE_2',
        33: 'SLICE_3',
        40: 'STORE_SLICE_0',
        41: 'STORE_SLICE_1',
        42: 'STORE_SLICE_2',
        43: 'STORE_SLICE_3',
        50: 'DELETE_SLICE_0',
        51: 'DELETE_SLICE_1',
        52: 'DELETE_SLICE_2',
        53: 'DELETE_SLICE_3',
        54: 'STORE_MAP',
        55: 'INPLACE_ADD',
        56: 'INPLACE_SUBTRACT',
        57: 'INPLACE_MULTIPLY',
        58: 'INPLACE_DIVIDE',
        59: 'INPLACE_MODULO',
        60: 'STORE_SUBSCR',
        61: 'DELETE_SUBSCR',
        62: 'BINARY_LSHIFT',
        63: 'BINARY_RSHIFT',
        64: 'BINARY_AND',
        65: 'BINARY_XOR',
        66: 'BINARY_OR',
        67: 'INPLACE_POWER',
        68: 'GET_ITER',
        70: 'PRINT_EXPR',
        71: 'PRINT_ITEM',
        72: 'PRINT_NEWLINE',
        73: 'PRINT_ITEM_TO',
        74: 'PRINT_NEWLINE_TO',
        75: 'INPLACE_LSHIFT',
        76: 'INPLACE_RSHIFT',
        77: 'INPLACE_AND',
        78: 'INPLACE_XOR',
        79: 'INPLACE_OR',
        80: 'BREAK_LOOP',
        81: 'WITH_CLEANUP',
        82: 'LOAD_LOCALS',
        83: 'RETURN_VALUE',
        84: 'IMPORT_STAR',
        85: 'EXEC_STMT',
        86: 'YIELD_VALUE',
        87: 'POP_BLOCK',
        88: 'END_FINALLY',
        89: 'BUILD_CLASS',
        92: 'ROT_FOUR',
        93: 'SET_ADD',
        94: 'YIELD_FROM',
        157: 'BUILD_STRING',
        161: 'CALL_METHOD',
    }
    
    if opcode in python27_opcodes:
        return python27_opcodes[opcode]
    
    # Fallback to class attributes
    for name, value in Opcode.__dict__.items():
        if isinstance(value, int) and value == opcode and not name.startswith('_'):
            return name
    
    return f"UNKNOWN_{opcode}"


# 别名，用于兼容
opcode_name = opcode_to_name


def byte_to_opcode(byte: int, version: Tuple[int, int]) -> int:
    """根据版本将字节转换为操作码"""
    return byte


def bc_next(source, mod, pos: int) -> Tuple[int, int, int]:
    """
    读取下一条字节码指令
    类似于C++版本的bc_next函数
    """
    from ..core.pyc_stream import PycBuffer
    
    if isinstance(source, PycBuffer) and source.at_eof():
        return 0, 0, pos
    
    # 读取操作码
    opcode = source.read_byte()
    operand = 0
    pos += 1
    
    # 检查是否有操作数
    if isinstance(source, PycBuffer) and source.at_eof():
        return opcode, operand, pos
    
    # 检查操作码是否需要参数
    if opcode >= Opcode.PYC_HAVE_ARG:
        operand = source.read_uint16()
        pos += 2
    
    return opcode, operand, pos


def bc_read_byte(source) -> int:
    """从字节码缓冲区读取一个字节"""
    from ..core.pyc_stream import PycBuffer
    
    if isinstance(source, PycBuffer):
        return source.read_byte()
    else:
        # 处理其他类型的数据源
        return 0


def bc_read_signed_byte(source) -> int:
    """从字节码缓冲区读取一个有符号字节"""
    byte = bc_read_byte(source)
    return byte if byte < 128 else byte - 256


def bc_read_int(source) -> int:
    """从字节码缓冲区读取一个整数"""
    from ..core.pyc_stream import PycBuffer
    
    if isinstance(source, PycBuffer):
        return source.read_int()
    else:
        return 0


def bc_read_int_signed(source) -> int:
    """从字节码缓冲区读取一个有符号整数"""
    return bc_read_int(source)


def bc_read_long(source) -> int:
    """从字节码缓冲区读取一个长整数"""
    return bc_read_int(source)


def _parse_varint(data, pos: int) -> Tuple[int, int]:
    """
    解析变长整数
    类似于C++版本的_parse_varint函数
    """
    result = 0
    shift = 0
    
    while True:
        if pos >= len(data):
            break
        
        byte = data[pos] & 0xFF
        pos += 1
        
        result |= (byte & 0x7F) << shift
        shift += 7
        
        if (byte & 0x80) == 0:
            break
    
    return result, pos


def bc_load_name(code, mod, idx: int) -> str:
    """加载名称"""
    if hasattr(code, 'names') and idx < len(code.names()):
        name_obj = code.names()[idx]
        if hasattr(name_obj, 'value'):
            return name_obj.value()
        else:
            return str(name_obj)
    return f"<unknown_{idx}>"


def bc_load_global(code, mod, idx: int) -> str:
    """加载全局变量"""
    if hasattr(code, 'globals') and idx < len(code.globals()):
        global_obj = code.globals()[idx]
        if hasattr(global_obj, 'value'):
            return global_obj.value()
        else:
            return str(global_obj)
    return f"<global_{idx}>"


def bc_load_const(code, mod, idx: int):
    """加载常量"""
    if hasattr(code, 'consts') and idx < len(code.consts()):
        return code.consts()[idx]
    return None


def bc_load_fast(code, mod, idx: int) -> str:
    """加载局部变量"""
    if hasattr(code, 'varnames') and idx < len(code.varnames()):
        var_obj = code.varnames()[idx]
        if hasattr(var_obj, 'value'):
            return var_obj.value()
        else:
            return str(var_obj)
    return f"<fast_{idx}>"


def bc_load_deref(code, mod, idx: int) -> str:
    """加载自由变量"""
    # 优先检查cellvars
    if hasattr(code, 'cellvars') and idx < len(code.cellvars()):
        cell_obj = code.cellvars()[idx]
        if hasattr(cell_obj, 'value'):
            return cell_obj.value()
        else:
            return str(cell_obj)
    
    # 检查freevars
    if hasattr(code, 'freevars') and idx < len(code.freevars()):
        free_obj = code.freevars()[idx]
        if hasattr(free_obj, 'value'):
            return free_obj.value()
        else:
            return str(free_obj)
    
    return f"<deref_{idx}>"


def bc_load_closure(code, mod, idx: int) -> str:
    """加载闭包变量"""
    return bc_load_deref(code, mod, idx)


def bc_load_classderef(code, mod, idx: int) -> str:
    """加载类作用域的变量"""
    return bc_load_deref(code, mod, idx)


def bc_store_name(code, mod, idx: int) -> str:
    """存储名称"""
    return bc_load_name(code, mod, idx)


def bc_store_global(code, mod, idx: int) -> str:
    """存储全局变量"""
    return bc_load_global(code, mod, idx)


def bc_store_fast(code, mod, idx: int) -> str:
    """存储局部变量"""
    return bc_load_fast(code, mod, idx)


def bc_store_deref(code, mod, idx: int) -> str:
    """存储自由变量"""
    return bc_load_deref(code, mod, idx)


def bc_delete_name(code, mod, idx: int) -> str:
    """删除名称"""
    return bc_load_name(code, mod, idx)


def bc_delete_global(code, mod, idx: int) -> str:
    """删除全局变量"""
    return bc_load_global(code, mod, idx)


def bc_delete_fast(code, mod, idx: int) -> str:
    """删除局部变量"""
    return bc_load_fast(code, mod, idx)


def bc_delete_deref(code, mod, idx: int) -> str:
    """删除自由变量"""
    return bc_load_deref(code, mod, idx)


# 辅助函数：获取操作的字符串表示
def opcode_description(opcode: int) -> str:
    """获取操作码的描述"""
    name = opcode_to_name(opcode)
    
    descriptions = {
        'POP_TOP': 'Pop top of stack',
        'PUSH_NULL': 'Push NULL on stack',
        'UNARY_POSITIVE': 'Unary + (positive)',
        'UNARY_NEGATIVE': 'Unary - (negative)',
        'UNARY_NOT': 'Unary not',
        'UNARY_INVERT': 'Unary ~ (invert)',
        'BINARY_SUBSCR': 'Binary subscript',
        'BINARY_POWER': 'Binary **',
        'BINARY_MULTIPLY': 'Binary *',
        'BINARY_DIVIDE': 'Binary /',
        'BINARY_FLOOR_DIVIDE': 'Binary //',
        'BINARY_MODULO': 'Binary %',
        'BINARY_ADD': 'Binary +',
        'BINARY_SUBTRACT': 'Binary -',
        'BINARY_LSHIFT': 'Binary <<',
        'BINARY_RSHIFT': 'Binary >>',
        'BINARY_AND': 'Binary &',
        'BINARY_XOR': 'Binary ^',
        'BINARY_OR': 'Binary |',
        'INPLACE_POWER': 'In-place **',
        'INPLACE_MULTIPLY': 'In-place *',
        'INPLACE_DIVIDE': 'In-place /',
        'INPLACE_FLOOR_DIVIDE': 'In-place //',
        'INPLACE_MODULO': 'In-place %',
        'INPLACE_ADD': 'In-place +',
        'INPLACE_SUBTRACT': 'In-place -',
        'INPLACE_LSHIFT': 'In-place <<',
        'INPLACE_RSHIFT': 'In-place >>',
        'INPLACE_AND': 'In-place &',
        'INPLACE_XOR': 'In-place ^',
        'INPLACE_OR': 'In-place |',
        'LOAD_CONST': 'Load constant',
        'LOAD_NAME': 'Load name',
        'LOAD_GLOBAL': 'Load global',
        'LOAD_FAST': 'Load local (fast)',
        'LOAD_DEREF': 'Load free variable',
        'LOAD_CLOSURE': 'Load closure',
        'STORE_NAME': 'Store name',
        'STORE_GLOBAL': 'Store global',
        'STORE_FAST': 'Store local (fast)',
        'STORE_DEREF': 'Store free variable',
        'DELETE_NAME': 'Delete name',
        'DELETE_GLOBAL': 'Delete global',
        'DELETE_FAST': 'Delete local (fast)',
        'DELETE_DEREF': 'Delete free variable',
        'RETURN_VALUE': 'Return value',
        'YIELD_VALUE': 'Yield value',
        'YIELD_FROM': 'Yield from',
        'POP_TOP': 'Pop top of stack',
        'DUP_TOP': 'Duplicate top of stack',
        'DUP_TOP_TWO': 'Duplicate top two items',
        'ROT_TWO': 'Rotate top two items',
        'ROT_THREE': 'Rotate top three items',
        'ROT_FOUR': 'Rotate top four items',
        'PRINT_EXPR': 'Print expression',
        'IMPORT_NAME': 'Import name',
        'IMPORT_FROM': 'Import from',
        'IMPORT_STAR': 'Import all',
        'BUILD_LIST': 'Build list',
        'BUILD_TUPLE': 'Build tuple',
        'BUILD_SET': 'Build set',
        'BUILD_MAP': 'Build map',
        'BUILD_SLICE': 'Build slice',
        'BUILD_STRING': 'Build string',
        'CALL_FUNCTION': 'Call function',
        'CALL_FUNCTION_VAR': 'Call function with *args',
        'CALL_FUNCTION_KW': 'Call function with **kwargs',
        'CALL_FUNCTION_VAR_KW': 'Call function with *args and **kwargs',
        'MAKE_FUNCTION': 'Make function',
        'MAKE_CLOSURE': 'Make closure',
        'LOAD_BUILD_CLASS': 'Load __build_class__',
        'POP_BLOCK': 'Pop block',
        'POP_EXCEPT': 'Pop exception',
        'SETUP_EXCEPT': 'Setup except handler',
        'SETUP_FINALLY': 'Setup finally handler',
        'WITH_CLEANUP': 'With cleanup',
        'BEGIN_FINALLY': 'Begin finally',
        'END_FINALLY': 'End finally',
        'RAISE_VARARGS': 'Raise with varargs',
        'RAISE_VARARGS_A': 'Raise with varargs (extended arg)',
        'RAISE': 'Raise exception',
        'BREAK_LOOP': 'Break loop',
        'CONTINUE_LOOP': 'Continue loop',
        'JUMP_FORWARD': 'Jump forward',
        'JUMP_ABSOLUTE': 'Jump absolute',
        'POP_JUMP_IF_TRUE': 'Pop and jump if true',
        'POP_JUMP_IF_FALSE': 'Pop and jump if false',
        'JUMP_IF_TRUE_OR_POP': 'Jump if true or pop',
        'JUMP_IF_FALSE_OR_POP': 'Jump if false or pop',
        'COMPARE_OP': 'Compare operation',
        'COMPARE_OP_A': 'Compare operation (extended arg)',
        'EXEC': 'Execute',
        'BUILD_CLASS': 'Build class',
        'HAVE_ARGUMENT': 'Marker for instructions with arguments',
    }
    
    return descriptions.get(name, f'Unknown operation: {name}')


# 版本兼容性检查函数
def version_supports_opcode(version: Tuple[int, int], opcode: int) -> bool:
    """检查指定版本是否支持指定操作码"""
    major, minor = version
    
    # Python 3.11+ 操作码
    if opcode in [
        Opcode.CACHE, Opcode.PUSH_NULL, Opcode.NOP,
        Opcode.UNARY_POSITIVE, Opcode.UNARY_NEGATIVE, Opcode.UNARY_NOT,
        Opcode.UNARY_INVERT, Opcode.GET_LEN, Opcode.MATCH_MAPPING,
        Opcode.MATCH_SEQUENCE, Opcode.MATCH_KEYS, Opcode.PUSH_EXC_INFO,
        Opcode.CHECK_EXC_MATCH, Opcode.CHECK_EG_MATCH, Opcode.WITH_EXCEPT_START,
        Opcode.GET_AITER, Opcode.GET_ANEXT, Opcode.BEFORE_ASYNC_WITH,
        Opcode.BEFORE_WITH, Opcode.END_ASYNC_FOR, Opcode.GET_AWAITABLE_A,
        Opcode.GET_YIELD_FROM_ITER, Opcode.RETURN_GENERATOR,
        Opcode.LIST_TO_TUPLE, Opcode.SETUP_ANNOTATIONS, Opcode.ASYNC_GEN_WRAP,
        Opcode.PREP_RERAISE_STAR, Opcode.POP_EXCEPT, Opcode.CALL_A,
        Opcode.KW_NAMES_A, Opcode.MATCH_CLASS_A, Opcode.FORMAT_VALUE_A,
        Opcode.BUILD_CONST_KEY_MAP_A, Opcode.BUILD_STRING_A,
        Opcode.PRECALL_A, Opcode.LOAD_METHOD_A
    ]:
        return major >= 3 and minor >= 11
    
    # Python 3.10+ 操作码
    if opcode in [
        Opcode.RAISE_VARARGS_A, Opcode.MATCH_CLASS_A,
        Opcode.COPY_A, Opcode.BINARY_OP_A
    ]:
        return major >= 3 and minor >= 10
    
    # Python 3.8+ 操作码
    if opcode in [
        Opcode.BUILD_TUPLE_A, Opcode.BUILD_LIST_A, Opcode.BUILD_SET_A,
        Opcode.BUILD_MAP_A, Opcode.LOAD_ATTR_A, Opcode.COMPARE_OP_A,
        Opcode.IMPORT_NAME_A, Opcode.IMPORT_FROM_A, Opcode.JUMP_FORWARD_A,
        Opcode.LOAD_GLOBAL_A, Opcode.IS_OP_A, Opcode.CONTAINS_OP_A,
        Opcode.RERAISE_A, Opcode.LOAD_FAST_A, Opcode.STORE_FAST_A,
        Opcode.DELETE_FAST_A, Opcode.CALL_FUNCTION_EX_A,
        Opcode.MAKE_FUNCTION_A, Opcode.BUILD_SLICE_A, Opcode.MAKE_CELL_A,
        Opcode.LOAD_CLOSURE_A, Opcode.LOAD_DEREF_A, Opcode.STORE_DEREF_A,
        Opcode.DELETE_DEREF_A, Opcode.JUMP_BACKWARD_A, Opcode.LIST_APPEND_A,
        Opcode.SET_ADD_A, Opcode.MAP_ADD_A, Opcode.RESUME_A, Opcode.COPY_FREE_VARS_A
    ]:
        return major >= 3 and minor >= 8
    
    # 基础操作码在所有Python 3版本中都支持
    return major >= 3


# 调试和诊断函数
def disassemble_instruction(opcode: int, operand: int = 0, pos: int = 0, version: Tuple[int, int] = (3, 8)) -> str:
    """反汇编单个指令"""
    name = opcode_to_name(opcode)
    
    # 基本格式
    result = f"{pos:4d} {name:20s}"
    
    # 添加参数
    if opcode >= Opcode.PYC_HAVE_ARG:
        result += f" {operand}"
    
    # 添加版本信息
    if not version_supports_opcode(version, opcode):
        result += f"  # Not supported in Python {version[0]}.{version[1]}"
    
    return result


def disassemble_bytecode(bytecode_data: bytes, version: Tuple[int, int] = (3, 8)) -> str:
    """反汇编字节码序列"""
    from ..core.pyc_stream import PycBuffer
    
    buffer = PycBuffer(bytecode_data, len(bytecode_data))
    result = []
    pos = 0
    
    while not buffer.at_eof():
        try:
            opcode, operand, pos = bc_next(buffer, None, pos)
            result.append(disassemble_instruction(opcode, operand, pos - (3 if opcode >= Opcode.PYC_HAVE_ARG else 1), version))
        except Exception as e:
            result.append(f"{pos:4d} ERROR: {e}")
            break
    
    return '\n'.join(result)
