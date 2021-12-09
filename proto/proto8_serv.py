from proto8_util_extractor import *
from proto8_util_argparse  import *
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
        
    #TODO: PARSE ARGS  
    parsed = SERVER_ARGPARSER.parse_message(frame)
    if not isinstance(parsed, list):
        raw = str_to_bytes("ERRORENC") + BYTE_REPR(SEP) + BYTE_REPR(parsed) + BYTE_REPR(END)
    else:
        raw = b''.join([ord(c).to_bytes(1,'little') for c in frame])
        
    try:  
        socket.sendall(raw)
    except error:
        print(e)

while True:
    connectionSocket, addr = serverSocket.accept()
    print("Connection on:", addr)
    SBBP_Frame_Extractor(connectionSocket, 32, on_recieve_frame)