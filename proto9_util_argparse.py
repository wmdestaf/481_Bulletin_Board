import enum
from proto9_constants import *

#Define our BNF in the form of an enum
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
    
    #SUBJS ONLY, (ONE OR MORE OF) mID, OWNER, TIMESTAMP, SUBJECT, MESSAGE
    "GET_MSGS": (ARG_TYPE.boolean, (ARG_TYPE.descend, (ARG_TYPE.repeat, (ARG_TYPE.descend, (ARG_TYPE.integer, ARG_TYPE.integer, ARG_TYPE.integer, ARG_TYPE.string, ARG_TYPE.string)),)),),
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
    
    #BOARD ID, USER ID, MSG_IDS, SUBJS_ONLY, NEW_ONLY
    "GET_MSGS": (ARG_TYPE.integer, ARG_TYPE.integer, (ARG_TYPE.descend, (ARG_TYPE.repeat, ARG_TYPE.integer)), ARG_TYPE.boolean, ARG_TYPE.boolean),
    
    #BOARD ID, USER ID
    "CREATE_B": (ARG_TYPE.integer, ARG_TYPE.integer),
    
    #BOARD ID, USER ID
    "DELETE_B": (ARG_TYPE.integer, ARG_TYPE.integer)
}

#Simple wrapper for exception class
class ParseError(Exception):
    pass

'''
    Parses an 'Ascii-encoded integer' (e.g. "12345") as an integer
    @throws ParseError If any digit of said integer is not an ascii 'digit' ('0'-'9', inclusive)
    @return The integer
'''
def parse_asc_encoded_int(raw):
    if any(ord(x) < ord('0') or ord(x) > ord('9') for x in raw):
        raise ParseError
    return int(raw)

'''
    Parses an 'Ascii-encoded boolean' ("0" or "1") as a boolean
    @throws ParseError If any digit of said integer is not a "0" or "1"
    @return True if raw == "1", or False of raw == "0"
'''
def parse_asc_encoded_boolean(raw):
    if len(raw) != 1 or (raw != '0' and raw != '1'):
        raise ParseError
    return True if raw == '1' else False

'''
    Parses a 'string' as a string.
    @throws ParseError if the string is empty
    @return The string
'''
def parse_string(raw):
    if not raw:
        raise ParseError
    return raw
    
'''
    Parses a 'string' as a byte.
    @throws ParseError if the string is not exactly 1 byte
    @return The string
'''
def parse_byte(raw):
    if len(raw) != 1:
        raise ParseError
    return raw
    
'''
    Main function for the recursive descent parser.
    @param expected_args The expected arguments
    @param given_args The given arguments (by the user)
    @param parsed_args Pointer to the arguments parsed by the function
    @param depth The current depth, which determines which seperator to split on
'''
def recursive_descent(expected_args, given_args, parsed_args, depth):
    if len(given_args) == 1 and not given_args[0]:
        return
    
    elif depth > 2: #Arbitrary limit for this specific BNF grammar
        raise ParseError 
    
    #Iterate through, and split and descend where necessary
    for idx, arg_type in enumerate(expected_args):
        if isinstance(arg_type, tuple) and arg_type[0] == ARG_TYPE.descend: 
            next_expect = expected_args[idx][1] 
            next_given  = given_args[idx].split(chr(0xFE - depth - 1))
            
            #A 'repeat' implies any number of the following arguments, including zero.
            #Therefore, we 'expect' as many arguments as the caller 'provides'
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

'''
    Parses a message, into arguments according to a 
    known list of commands and expected arguments
    @param msg The string 'message' to parse
    @param commands The list of acceptable commands (opcodes)
    @param expected_args The map of arguments to expect
    @return The list of parsed arguments, or an informative error code
'''
def parse(msg, commands, expected_args):
    #Determine if a message can be parsed
    if len(msg) < 10 or msg[-1] != ASCII_REPR(END) or msg[OPCODE_LEN] != ASCII_REPR(SEP):
        return INVALFMT
    
    #split out an opcode, determine if legal
    op = msg[:OPCODE_LEN]
    if msg[:OPCODE_LEN] not in commands:
        return UNKNWNOP

    #with the opcode known, interpret the rest of 'msg' as the arguments
    #additionally, strip out the trailing 0xFF seperator
    given = msg[OPCODE_LEN + 1:-1].split(ASCII_REPR(SEP))
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

'''
    Simple wrapper class for additional abstraction
'''
class ArgParser:
    def __init__(self, commands, expected_args):
        self.commands = commands
        self.expected_args = expected_args
        
    def parse_message(self, msg):
        return parse(msg, self.commands, self.expected_args)

CLIENT_ARGPARSER = ArgParser(commands_client, expected_args_client)
SERVER_ARGPARSER = ArgParser(commands_server, expected_args_server)

'''
    Forces an 'argument' into the form of a string
    @param x The 'argument' to convert
    @return The appropriate 'string' representation of said argument.
'''
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
        
'''
    Joins an 'argument list' back into a string
    @param opcode The opcode 
    @param arg_list The argument list to join
    @return The 'string' representation = OPCODE + SEP + STRING_ARGUMENTS + END
'''
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
                
    if not isinstance(arg_list, list): #Possible that a top-level argument could not be a list,
                                       #which generates an 'off-by-one' error for the seperator
        string = force_str_repr(arg_list)
    else:
        argjoin0(arg_list,SEP)
    return opcode + ASCII_REPR(SEP) + string + ASCII_REPR(END)