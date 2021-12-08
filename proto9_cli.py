from proto9_util_extractor import *
from proto9_util_argparse  import *
from proto9_data           import *
import socket
from socket import AF_INET, SOCK_STREAM
from socket import error as GENERIC_SOCKET_ERROR
from threading import Thread, Semaphore
import re
import time
import signal

serverName = 'localhost'
serverPort = 12000

try:
    clientSocket = socket.socket(AF_INET, SOCK_STREAM)
except GENERIC_SOCKET_ERROR as e:
    print("Could not establish socket -",e)
    quit(1)
    
try:
    clientSocket.connect((serverName,serverPort))
except GENERIC_SOCKET_ERROR as e:
    print("Could not connect to servr -",e)
    quit(1)

mutex = Semaphore(1)
#begin a recieving thread
def on_recieve_frame(*args):
    socket = args[0]
    frame  = args[1]
    if len(args) > 2:
        other = args[2:]

    parsed = CLIENT_ARGPARSER.parse_message(frame)
    
    if not isinstance(parsed, tuple): #Server returned something strange...very bad!
        print( ("#"*20) + "ERROR" + ("#"*20))
        print("Could not parse response from server! (parse returned {:d})".format(parsed))
        print("Dumping information...")
        print(frame)
    else:
        res = EXECUTE_ARGS_CLIENT(parsed[0], parsed[1])

    print(res)
    client_io_lock.release()

client_io_lock = Semaphore(1)
extractor = SBBP_Frame_Extractor(clientSocket, (serverName, serverPort), RECV_SSIZE, on_recieve_frame)

def on_exit(*args):
    extractor.close()
    quit()
signal.signal(signal.SIGINT, on_exit)

while True:
    msg = input("MSG: ")

    if not msg:
        on_exit()
        
    try:
        clientSocket.sendall(str_to_bytes(zip_seperators(msg))) #TODO: PROTECT
    except GENERIC_SOCKET_ERROR as e:
        print("Error sending message:",e)
        on_exit()
    
    client_io_lock.acquire()
    
'''
    TODO: 
    client send like a human being
    lock access to board with RWSEM
'''