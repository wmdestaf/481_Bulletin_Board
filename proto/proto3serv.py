from socket import *
from threading import *
serverPort = 12000
serverSocket = socket(AF_INET,SOCK_STREAM)
serverSocket.bind(('',serverPort))
serverSocket.listen(1)
print('The server is ready to receive')

connectionSocket, addr = serverSocket.accept()

bf_size = 32
SEP = 0xFE.to_bytes(1, 'big')
END = 0xFF.to_bytes(1, 'big')

def fire(msg):
    if ord(msg[-1]) != 0xFF:
        print("Message improperly terminated.")
        return
        
    #strip terminator
    msg = msg[:-1].split(chr(254))
    if len(msg) != 2:
        print("Message improperly segmented.")
        return
    
    try:
        msg_len = int(msg[0])
    except ValueError:
        print("Message length improperly given.")
        return
    
    if msg_len != len(msg[1]):
        print("Given length != Message Length.")
        return
        
    print("Message of length {}: {}".format(msg_len,msg[1]))


buf = bytes(0)
while True:
    frame = connectionSocket.recv(bf_size)
    if not len(frame): #socket died
        print("socket died... :(")
        quit(1)
        
    buf  += frame
    if 0xFF in frame: #hit the terminator
        msg = "".join([chr(x) for x in buf])
        Thread(target=fire, args=(msg,)).start()
        buf = bytes(0)
    
    
    
    
    
    
    
    
    
    