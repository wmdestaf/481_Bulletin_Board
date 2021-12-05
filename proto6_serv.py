from socket import *
from threading import Thread
serverPort = 12000
serverSocket = socket(AF_INET,SOCK_STREAM)
serverSocket.bind(('',serverPort))
serverSocket.listen(1)
print('The server is ready to receive')

bf_size = 32
SEP = 0xFE.to_bytes(1, 'big')
END = 0xFF.to_bytes(1, 'big')

def respond(socket, addr, msg):
    for i in range(0xFC, 0x100):
        msg = msg.replace(chr(i), '[' + hex(i)[2:] + ']')
    print("From {}: {}".format(addr,msg))
    
    socket.send(b''.join([ord(c).to_bytes(1,'little') for c in msg]))

def recieve(socket, addr):
    buf = bytes(0)
    while True:
        frame = connectionSocket.recv(bf_size)
        if not len(frame): #socket died
            print("socket died... :(")
            quit(1)

        if 0xFF in frame: #hit the terminator
            points = [0] + [idx + 1 for idx, val in enumerate(frame) if val == 0xFF] + [len(frame)]
            splits = [frame[points[idx]:points[idx+1]] for idx in range(len(points) - 1)]
            
            #finish the current message
            buf += splits[0]
            msg = "".join([chr(x) for x in buf])
            Thread(target=respond, args=(socket,addr,msg)).start()
            
            #and if there are any other messages...
            for other_msg in splits[1:]:
                if other_msg and 0xFF in other_msg:
                    other_msg = "".join([chr(x) for x in other_msg])
                    Thread(target=respond, args=(socket,addr,other_msg)).start()
                else: #last message in list, potentially not terminated
                    buf = other_msg
        else:
            buf += frame

while True:
    connectionSocket, addr = serverSocket.accept()
    Thread(target=recieve, args=(connectionSocket,addr)).start()