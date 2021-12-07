import enum
from proto9_constants import *

class ARG_TYPE(enum.Enum):
    byte       = enum.auto()
    integer    = enum.auto()
    string     = enum.auto()
    boolean    = enum.auto()
    descend    = enum.auto()
    repeat     = enum.auto()

#Where *_client, *_(client|server) means the parser is called from the (client|server)
commands_client = ("GET_M_CT","GETNEWCT","POST_MSG","DELT_MSG","GET_MSGS","CREATE_B","DELETE_B","ERRORENC")
commands_server = ("GET_M_CT","GETNEWCT","POST_MSG","DELT_MSG","GET_MSGS","CREATE_B","DELETE_B")

expected_args_client = {
    #BOARD ID
    "GET_M_CT": (ARG_TYPE.integer,),
    
    #BOARD ID, USER ID
    "GETNEWCT": (ARG_TYPE.integer,),

    "POST_MSG": (),
    "DELT_MSG": (),
    
    #TODO: DESCRIBE
    "GET_MSGS": ((ARG_TYPE.descend, (ARG_TYPE.repeat, (ARG_TYPE.descend, (ARG_TYPE.integer, ARG_TYPE.integer, ARG_TYPE.integer, ARG_TYPE.string, ARG_TYPE.string)),)),),
    "CREATE_B": (),
    "DELETE_B": (),
    
    #ERROR CODE
    "ERRORENC": (ARG_TYPE.byte,)
}

expected_args_server = {
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

class ParseError(Exception):
    pass

def parse_asc_encoded_int(raw):
    if any(ord(x) < ord('0') or ord(x) > ord('9') for x in raw):
        raise ParseError
    return int(raw)

def parse_asc_encoded_boolean(raw):
    if len(raw) != 1 or (raw != '0' and raw != '1'):
        raise ParseError
    return True if raw == '1' else False

def parse_string(raw):
    if not raw:
        raise ParseError
    return raw
    
def parse_byte(raw):
    if len(raw) != 1:
        raise ParseError
    return raw
    
def recursive_descent(expected_args, given_args, parsed_args, depth):
    if len(given_args) == 1 and not given_args[0]:
        return
    
    elif depth > 2:
        raise ParseError 
    
    for idx, arg_type in enumerate(expected_args):
        if isinstance(arg_type, tuple) and arg_type[0] == ARG_TYPE.descend: 
            next_expect = expected_args[idx][1] 
            next_given  = given_args[idx].split(chr(0xFE - depth - 1))
            
            #parameterize next_expect as needed
            if next_expect[0] == ARG_TYPE.repeat:
                next_expect = (next_expect[1],) * len(next_given)

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
            parsed_args.append(parse_byte(given_args[idx]))


def parse(msg, commands, expected_args):
    #Determine if a message can be parsed
    if len(msg) < 10 or msg[-1] != ASCII_REPR(END) or msg[OPCODE_LEN] != ASCII_REPR(SEP):
        return INVALFMT
    
    op = msg[:OPCODE_LEN]
    if msg[:OPCODE_LEN] not in commands:
        return UNKNWNOP

    given = msg[OPCODE_LEN + 1:-1].split(ASCII_REPR(SEP)) #split out into args
    if not given[0]:
        given = []

    if len(expected_args[op]) != len(given):
        return ARGCOUNT
        
    parsed_args = []
    try:
        recursive_descent(expected_args[op], given, parsed_args, 0)
    except ParseError:
        return ARGVALUE
        
    return (op, parsed_args)    

class ArgParser:
    def __init__(self, commands, expected_args):
        self.commands = commands
        self.expected_args = expected_args
        
    def parse_message(self, msg):
        return parse(msg, self.commands, self.expected_args)

CLIENT_ARGPARSER = ArgParser(commands_client, expected_args_client)
SERVER_ARGPARSER = ArgParser(commands_server, expected_args_server)

def force_str_repr(x):
    if isinstance(x, str):
        return x
    elif isinstance(x, bool):
        return '1' if x else '0'
    elif isinstance(x, int):
        return str(x)
    elif isinstance(x, float):
        return str(int(x))
    raise ValueError
        
def argjoin(opcode, arg_list):
    string = ''
    
    def argjoin0(arg_list, sep):
        nonlocal string
        for idx, arg in enumerate(arg_list):
            if not isinstance(arg, list):
                string += force_str_repr(arg) + ('' if idx == len(arg_list) - 1 else ASCII_REPR(sep))
            else:
                argjoin0(arg, sep - 1)
                string += ('' if idx == len(arg_list) - 1 else ASCII_REPR(sep))
                
    argjoin0(arg_list,SEP)
    return opcode + ASCII_REPR(SEP) + string + ASCII_REPR(END)