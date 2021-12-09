from socket import *
from threading import Thread
import re

serverName = 'localhost'
serverPort = 12000
clientSocket = socket(AF_INET, SOCK_STREAM)
clientSocket.connect((serverName,serverPort))

bf_size = 32
SEP = 0xFE.to_bytes(1, 'big')
END = 0xFF.to_bytes(1, 'big')

def handleInput(socket): #TODO: fragmentation
    while True:
        back = socket.recv(bf_size)
        back = "".join([chr(x) for x in back])
        for i in range(0xFC, 0x100):
            back = back.replace(chr(i), '[' + hex(i)[2:] + ']')
        print("GOTBACK:",back)

Thread(target=handleInput, args=(clientSocket,)).start()
while True:
    msg = input("MSG: ")
    msg = re.sub(r'\[(F[C-F])\]', lambda hx: chr(int(hx.group(1),16)), msg)
    clientSocket.send(b''.join([ord(c).to_bytes(1,'little') for c in msg]))
    
clientSocket.close()