from proto7_util import *
import socket
from socket import AF_INET, SOCK_STREAM, error
from threading import Thread
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
        
    try:
        raw = b''.join([ord(c).to_bytes(1,'little') for c in frame])
        socket.sendall(raw)
    except error:
        print(e)

while True:
    connectionSocket, addr = serverSocket.accept()
    print("Connection on:", addr)
    SBBP_Frame_Extractor(connectionSocket, 32, on_recieve_frame)