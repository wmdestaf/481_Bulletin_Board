from socket import *
serverName = 'localhost'
serverPort = 12000
clientSocket = socket(AF_INET, SOCK_STREAM)
clientSocket.connect((serverName,serverPort))

bf_size = 32
SEP = 0xFE.to_bytes(1, 'big')
END = 0xFF.to_bytes(1, 'big')

while True:
    sentence = input('Input lowercase sentence:').encode(encoding='ascii')
    length = str(len(sentence)).encode(encoding='ascii') #ASCII CODED DECIMAL
    message = length + SEP + sentence + END
    print(list(message))
    clientSocket.send(message)
    
clientSocket.close()