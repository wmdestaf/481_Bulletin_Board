from socket import *
serverPort = 12000
serverSocket = socket(AF_INET,SOCK_STREAM)
serverSocket.bind(('',serverPort))
serverSocket.listen(1)
print('The server is ready to receive')

connectionSocket, addr = serverSocket.accept()

bf_size = 32
SEP = 0xFE.to_bytes(1, 'big')
END = 0xFF.to_bytes(1, 'big')

while True:
    buf = bytes(0)
    while True:
        frame = connectionSocket.recv(bf_size)
        if not len(frame): #socket died
            print("socket died... :(")
            quit(1)
        
        buf  += frame
        if len(frame) < bf_size or frame[-1] == 0xFF:
            break
        
    msg = "".join([chr(x) for x in buf])
    if ord(msg[-1]) != 0xFF:
        print("Message improperly terminated.")
        continue
        
    #strip terminator
    msg = msg[:-1].split(chr(254))
    if len(msg) != 2:
        print("Message improperly segmented.")
        continue
    
    try:
        msg_len = int(msg[0])
    except ValueError:
        print("Message length improperly given.")
        continue
    
    if msg_len != len(msg[1]):
        print("Given length != Message Length.")
        continue
        
    print("Message of length {}: {}".format(msg_len,msg[1]))
    
    
    
    
    
    
    
    
    