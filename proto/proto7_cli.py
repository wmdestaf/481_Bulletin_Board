from proto7_util import *
import socket
from socket import AF_INET, SOCK_STREAM, error
from threading import Thread, Semaphore
import re
import time

serverName = 'localhost'
serverPort = 12000
clientSocket = socket.socket(AF_INET, SOCK_STREAM)
clientSocket.connect((serverName,serverPort))

mutex = Semaphore(1)
#begin a recieving thread
def on_recieve_frame(*args):
    socket = args[0]
    frame  = args[1]
    if len(args) > 2:
        other = args[2:]
    
    mutex.acquire()
    print(unzip_seperators(frame))
    mutex.release()

SBBP_Frame_Extractor(clientSocket, 32, on_recieve_frame)

while True:
    mutex.acquire()
    msg = input("MSG: ")
    mutex.release()
    clientSocket.sendall(str_to_bytes(zip_seperators(msg)))
    time.sleep(2)