#message components
FIELDSEP = 0xFC
ELEM_SEP = 0xFD
SEP      = 0xFE
END      = 0xFF

#error codes
INVALFMT = 0x00 #The input cannot be interpreted as a message
UNKNWNOP = 0x01 #Unknown Command Opcode
ARGCOUNT = 0x02 #Incorrect number of arguments
ARGVALUE = 0x03 #Unacceptable value of one or more arguments
BOARDDNE = 0x10 #Specified board does not exist
MSGS_DNE = 0x11 #One or more of the specified messages do not exist
UNOPERMS = 0x20 #The user does not have the appropriate permissions to perform the operation
RESEMPTY = 0x30 #The specified operation was acceptable, but returned an empty result

FAULT_CODES    = {INVALFMT, UNKNWNOP, ARGCOUNT, ARGVALUE}

OPCODE_LEN = 8  #On something that can be limited, limit (to ease with parsing)

def ASCII_REPR(number):
    return chr(number)
    
def BYTE_REPR(number):
    return number.to_bytes(1, 'little')