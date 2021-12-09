import re
import signal
import enum 

FIELDSEP = 0xFC.to_bytes(1, 'big')
ELEM_SEP = 0xFD.to_bytes(1, 'big')
SEP      = 0xFE.to_bytes(1, 'big')
END      = 0xFF.to_bytes(1, 'big')

UNKNWNOP = 0x00.to_bytes(1, 'big')
BOARDDNE = 0x01.to_bytes(1, 'big')
MSGS_DNE = 0x02.to_bytes(1, 'big')
UNOPERMS = 0x03.to_bytes(1, 'big')
RESEMPTY = 0x10.to_bytes(1, 'big')
INVALFMT = 0xC4.to_bytes(1, 'big')
NO  = 'ERRORENC'.encode(encoding='ASCII')

OPCODE_LEN = 8

class ARG_TYPE(enum.Enum):
    integer    = enum.auto()
    string     = enum.auto()
    boolean    = enum.auto()
    descend    = enum.auto()
    repeat     = enum.auto()
    
commands = ("GET_M_CT","GETNEWCT","POST_MSG","DELT_MSG","GET_MSGS","CREATE_B","DELETE_B")
expected_args = {
    #BOARD ID
    "GET_M_CT": (ARG_TYPE.integer,),
    
    #BOARD ID, USER ID
    "GETNEWCT": (ARG_TYPE.integer, ARG_TYPE.integer),
    
    #BOARD ID, USER ID, SUBJECT, MESSAGE
    "POST_MSG": (ARG_TYPE.integer, ARG_TYPE.integer, ARG_TYPE.string, ARG_TYPE.string),
    
    #BOARD ID, USER ID, MESSAGE ID
    "DELT_MSG": (ARG_TYPE.integer, ARG_TYPE.integer, ARG_TYPE.integer),
    
    #BOARD ID, USER ID, MSG_IDS, 
    "GET_MSGS": (ARG_TYPE.integer, ARG_TYPE.integer, (ARG_TYPE.descend, (ARG_TYPE.repeat, ARG_TYPE.integer)), ARG_TYPE.boolean, ARG_TYPE.boolean),
    
    #BOARD ID, USER ID
    "CREATE_B": (ARG_TYPE.integer, ARG_TYPE.integer),
    
    #BOARD ID, USER ID
    "DELETE_B": (ARG_TYPE.integer, ARG_TYPE.integer)
}

def c(byte):
    return chr(int.from_bytes(byte,'big'))

class ParseError(Exception):
    pass

def parse_asc_encoded_boolean(raw):
    if len(raw) != 1 or (raw != '0' and raw != '1'):
        raise ParseError
    return True if raw == '1' else False

def parse_asc_encoded_int(raw):
    if any(ord(x) < ord('0') or ord(x) > ord('9') for x in raw):
        raise ParseError
    return int(raw)

def parse_string(raw):
    if not raw:
        raise ParseError
    return raw

def parse_byte(raw):
    if len(raw) != 1:
        raise ParseError
    return raw

''' START HERE '''
def recursive_descent(expected_args, given_args, parsed_args, depth):
    if len(given_args) == 1 and not given_args[0]:
        return
    
    for idx, arg_type in enumerate(expected_args):
        if isinstance(arg_type, tuple) and arg_type[0] == ARG_TYPE.descend: 
            next_expect = expected_args[idx][1] 
            next_given  = given_args[idx].split(chr(0xFE - depth - 1))
            
            #parameterize next_expect as needed
            if next_expect[0] == ARG_TYPE.repeat:
                next_expect = (next_expect[1],) * len(next_given)
                
            print(next_expect, next_given)
                
            sublist = []
            recursive_descent(next_expect,next_given,sublist, depth + 1)
            parsed_args.append(sublist)
        elif arg_type == ARG_TYPE.integer:
            parsed_args.append(parse_asc_encoded_int(given_args[idx]))
        elif arg_type == ARG_TYPE.boolean:
            parsed_args.append(parse_asc_encoded_boolean(given_args[idx]))
        elif arg_type == ARG_TYPE.string:
            parsed_args.append(parse_string(given_args[idx]))
        elif arg_type == ARG_TYPE.byte:
            parsed_args.append(parse_byte(given_args[idx - offset]))

def parse(msg):
    if len(msg) < 10:
        return NO + INVALFMT + END
    elif msg[-1] != c(END) or msg[OPCODE_LEN] != c(SEP):         
        return NO + INVALFMT + END
    elif msg[:OPCODE_LEN] not in commands:
        return NO + UNKNWNOP + END
        
    op    = msg[:OPCODE_LEN]
    given = msg[OPCODE_LEN + 1:-1].split(c(SEP)) #split out into args

    expected = expected_args[op]
    if len(expected) != len(given):
        return -1
        
    parsed_args = []
    try:
        recursive_descent(expected_args[op], given, parsed_args, 0)
    except ParseError:
        return NO + INVALFMT + END 
        
    print(op, parsed_args)    
    return op.encode(encoding='ascii') + SEP + END
    

signal.signal(signal.SIGINT, lambda *a: quit())
while True:
    msg = input("MSG: ")
    msg = re.sub(r'\[(F[C-F])\]', lambda hx: chr(int(hx.group(1),16)), msg)
    ret = ''.join([chr(c) for c in parse(msg)])
    for i in range(0xFC, 0x100):
        ret = ret.replace(chr(i), '[' + hex(i)[2:] + ']')
    for i in range(0x0, 0x11):
        ret = ret.replace(chr(i), '[' + hex(i)[2:] + ']')
    ret = ret.replace(chr(0xC4), '[' + hex(0xC4)[2:] + ']')
    print(ret)