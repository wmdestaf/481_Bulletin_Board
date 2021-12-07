from proto9_util_extractor import *
from proto9_util_argparse  import *
from proto9_data           import *
import socket
from socket import AF_INET, SOCK_STREAM, error
from threading import Thread
import signal
serverPort = 12000
serverSocket = socket.socket(AF_INET,SOCK_STREAM)
serverSocket.bind(('',serverPort))
serverSocket.listen(1)
print('The server is ready to receive')

def on_recieve_frame(*args): 
    socket = args[0]
    frame  = args[1]
    if len(args) > 2:
        other = args[2:]
        
    #PARSE ARGS => OPCODE, ARGS
    parsed = SERVER_ARGPARSER.parse_message(frame)
    
    if not isinstance(parsed, tuple):
        raw = str_to_bytes("ERRORENC") + BYTE_REPR(SEP) + BYTE_REPR(parsed) + BYTE_REPR(END)
    else:
        opcode = parsed[0]
        arguments = parsed[1]
        #EXECUTE_ARGS => SUCCESS, RESPONSE_ARGUMENTS
        response = EXECUTE_ARGS(opcode, arguments)
        if not response[0]:
            opcode = "ERRORENC"
        print(response[0], opcode, response[1])
        raw = str_to_bytes(argjoin(opcode, response[1]))
        
    try:  
        socket.sendall(raw)
    except error:
        print(e)

while True:
    connectionSocket, addr = serverSocket.accept()
    print("Connection on:", addr)
    SBBP_Frame_Extractor(connectionSocket, 32, on_recieve_frame)