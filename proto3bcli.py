from socket import *
import re

serverName = 'localhost'
serverPort = 12000
clientSocket = socket(AF_INET, SOCK_STREAM)
clientSocket.connect((serverName,serverPort))

bf_size = 32
SEP = 0xFE.to_bytes(1, 'big')
END = 0xFF.to_bytes(1, 'big')

while True:
    msg = input("MSG: ")
    msg = re.sub(r'\[(F[C-F])\]', lambda hx: chr(int(hx.group(1),16)), msg)
    clientSocket.send(b''.join([ord(c).to_bytes(1,'little') for c in msg]))
    
clientSocket.close()