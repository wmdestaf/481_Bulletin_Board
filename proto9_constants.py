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

#The client "should've" caught this code - hence, a 'fault'.
FAULT_CODES = {INVALFMT, UNKNWNOP, ARGCOUNT, ARGVALUE}

OPCODE_LEN = 8  #On something that can be limited, limit (to ease with parsing)
RECV_SSIZE = 32 #Size of each recv call

'''
    Converts an ordinal to its character representation
    @param number The ordinal
    @return The character specified by the ordinal
'''
def ASCII_REPR(number):
    return chr(number)
    
'''
    Converts an ordinal to its byte representation
    @param number The ordinal
    @return The byte specified by the ordinal
''' 
def BYTE_REPR(number):
    return number.to_bytes(1, 'little') #1 byte doesn't matter little or big endian.